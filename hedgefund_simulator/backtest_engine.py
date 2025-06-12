import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import matplotlib.pyplot as plt
from hedgefund_simulator.agents import (
    MarketDataAgent, 
    QuantAgent, 
    RiskManagerAgent, 
    PortfolioManagerAgent
)

class BacktestEngine:
    """Backtesting engine for simulating and evaluating trading strategies."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the backtesting engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.initialize_agents()
        self.results = {}
    
    def initialize_agents(self):
        """Initialize all the agents with their configurations."""
        # Market Data Agent
        self.market_data_agent = MarketDataAgent(
            self.config.get('market_data', {})
        )
        
        # Quant Agent
        self.quant_agent = QuantAgent(
            self.config.get('quant', {})
        )
        
        # Risk Manager Agent
        self.risk_manager = RiskManagerAgent(
            self.config.get('risk', {})
        )
        
        # Portfolio Manager Agent
        self.portfolio = PortfolioManagerAgent(
            config=self.config.get('portfolio', {})
        )
        
        # Store risk manager reference
        self.portfolio.risk_manager = self.risk_manager
    
    def load_data(self, ticker: str) -> pd.DataFrame:
        """Load and prepare market data.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            DataFrame with market data and indicators
        """
        # Use process instead of fetch_data to ensure technical indicators are added
        return self.market_data_agent.process(ticker)
    
    def run_backtest(
        self, 
        ticker: str, 
        initial_cash: float = 100000.0
    ) -> Dict[str, Any]:
        """Run a backtest for the given ticker.
        
        Args:
            ticker: Stock ticker symbol
            initial_cash: Initial cash amount
            
        Returns:
            Dictionary with backtest results
        """
        print(f"Starting backtest for {ticker}...")
        
        # Load and prepare data
        data = self.load_data(ticker)
        
        # Initialize portfolio
        self.portfolio.initialize_portfolio(initial_cash)
        
        # Run backtest
        for i in range(1, len(data)):
            current_date = data.index[i]
            previous_date = data.index[i-1]
            
            # Get current and previous data
            current_data = data.iloc[i]
            previous_data = data.iloc[i-1]
            
            # Generate trading signals
            signals = self.quant_agent.process(data[:i+1])
            
            # Get current position for this ticker
            current_position = self.portfolio.positions.get(ticker, {})
            
            # Calculate ATR for position sizing (using 14-day ATR)
            atr = None
            if 'ATR' in data.columns:
                atr = data['ATR'].iloc[i]
            
            # Get risk-managed signal
            risk_signal = self.risk_manager.process(
                signal=signals['combined'].iloc[-1] if not signals['combined'].empty else 0,
                price_data=current_data,
                current_position=current_position,
                portfolio_value=self.portfolio.calculate_portfolio_value()['total_value'],
                atr=atr
            )
            
            # Execute trade if needed
            trade_result = self.portfolio.process(
                ticker=ticker,
                signal=risk_signal,
                price_data=current_data,
                timestamp=current_date
            )
            
            # Log trade if executed
            if trade_result.get('status') == 'success':
                self._log_trade(trade_result['trade'])
        
        # Store final results
        self.results = self._generate_results(ticker, data)
        return self.results
    
    def _log_trade(self, trade: Dict[str, Any]):
        """Log trade details to console."""
        action = "BOUGHT" if trade['action'] == 'buy' else "SOLD"
        print(
            f"{trade['timestamp'].strftime('%Y-%m-%d')} | {trade['ticker']} | {action} | "
            f"Qty: {trade['quantity']} | Price: ${trade['price']:.2f} | "
            f"Value: ${trade['value']:,.2f} | "
            f"Cash: ${self.portfolio.cash:,.2f} | "
            f"Portfolio: ${self.portfolio.calculate_portfolio_value()['total_value']:,.2f} | "
            f"Reason: {trade.get('reason', '')}"
        )
        
        if 'realized_pnl' in trade:
            pnl = trade['realized_pnl']
            pnl_pct = trade.get('realized_pnl_pct', 0)
            pnl_sign = '+' if pnl >= 0 else ''
            print(f"  → Realized P&L: {pnl_sign}${abs(pnl):.2f} ({pnl_sign}{abs(pnl_pct):.1f}%)")
    
    def _generate_results(
        self, 
        ticker: str, 
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Generate backtest results and performance metrics."""
        # Calculate returns
        portfolio_values = pd.DataFrame(self.portfolio.portfolio_value_history)
        
        # Ensure we have a datetime index for portfolio values
        portfolio_values['date'] = pd.to_datetime(portfolio_values['date'])
        portfolio_values.set_index('date', inplace=True)
        
        # Calculate benchmark returns (buy and hold)
        close_prices = data['Close']
        if isinstance(close_prices, pd.DataFrame):
            close_prices = close_prices.iloc[:, 0]  # Take first column if multi-column
            
        returns = close_prices.pct_change()
        benchmark_equity = (1 + returns).cumprod() * 100000  # Starting with $100k
        
        # Convert benchmark to DataFrame if it's a Series
        if isinstance(benchmark_equity, pd.Series):
            benchmark_equity = benchmark_equity.to_frame('benchmark')
        else:
            benchmark_equity = benchmark_equity.rename(columns={benchmark_equity.columns[0]: 'benchmark'})
        
        # Ensure both DataFrames have the same index type and name
        benchmark_equity.index = pd.to_datetime(benchmark_equity.index)
        
        # Align the data by index
        results = pd.merge(
            portfolio_values[['total_value']].rename(columns={'total_value': 'strategy'}),
            benchmark_equity[['benchmark']],
            left_index=True,
            right_index=True,
            how='outer'
        )
        
        # Forward fill any missing values
        results.ffill(inplace=True)
        results = results[~results.index.duplicated(keep='first')]
        
        # Calculate performance metrics
        total_return = (results['strategy'].iloc[-1] / results['strategy'].iloc[0] - 1) * 100
        benchmark_return = (results['benchmark'].iloc[-1] / results['benchmark'].iloc[0] - 1) * 100
        
        # Calculate annualized return and volatility
        days = (results.index[-1] - results.index[0]).days
        years = days / 365.25
        
        annualized_return = ((1 + total_return/100) ** (1/years) - 1) * 100 if years > 0 else 0
        annualized_vol = results['strategy'].pct_change().std() * np.sqrt(252) * 100
        
        # Calculate max drawdown
        rolling_max = results['strategy'].cummax()
        drawdown = (results['strategy'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100
        
        # Calculate Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = annualized_return / annualized_vol if annualized_vol > 0 else 0
        
        # Prepare trade history
        trades = pd.DataFrame(self.portfolio.trade_history)
        
        # Ensure we have the required columns for PnL calculation
        if not trades.empty:
            # Ensure we have the required columns
            if 'realized_pnl' not in trades.columns and 'action' in trades.columns:
                # Calculate PnL for each trade if not already present
                trades['realized_pnl'] = 0.0
                trades['realized_pnl_pct'] = 0.0
                
                # Calculate PnL for sell trades
                sell_trades = trades[trades['action'] == 'sell'].copy()
                if not sell_trades.empty:
                    # Get the corresponding buy trades
                    for idx, trade in sell_trades.iterrows():
                        ticker = trade['ticker']
                        # Find the most recent buy for this ticker before this sell
                        buy_trades = trades[
                            (trades['ticker'] == ticker) & 
                            (trades['action'] == 'buy') &
                            (trades.index < idx)
                        ]
                        if not buy_trades.empty:
                            buy_price = buy_trades.iloc[-1]['price']
                            sell_price = trade['price']
                            quantity = trade['quantity']
                            cost_basis = buy_price * quantity
                            trade_value = sell_price * quantity
                            commission = trade.get('commission', 0)
                            pnl = (sell_price - buy_price) * quantity - commission
                            pnl_pct = (pnl / cost_basis) * 100 if cost_basis > 0 else 0
                            
                            trades.at[idx, 'realized_pnl'] = pnl
                            trades.at[idx, 'realized_pnl_pct'] = pnl_pct
        
        # Calculate win rate if we have trades
        win_rate = 0
        avg_win = 0
        avg_loss = 0
        profit_factor = 0
        
        if not trades.empty and 'realized_pnl' in trades.columns:
            # Filter out non-sell trades if needed
            if 'action' in trades.columns:
                sell_trades = trades[trades['action'] == 'sell']
                if not sell_trades.empty:
                    trades = sell_trades
            
            winning_trades = trades[trades['realized_pnl'] > 0]
            losing_trades = trades[trades['realized_pnl'] < 0]
            
            total_trades = len(trades)
            win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
            
            avg_win = winning_trades['realized_pnl'].mean() if not winning_trades.empty else 0
            avg_loss = abs(losing_trades['realized_pnl'].mean()) if not losing_trades.empty else 0
            
            total_win = winning_trades['realized_pnl'].sum()
            total_loss = abs(losing_trades['realized_pnl'].sum()) if not losing_trades.empty else 0
            profit_factor = total_win / total_loss if total_loss > 0 else float('inf')
        
        return {
            'ticker': ticker,
            'start_date': results.index[0],
            'end_date': results.index[-1],
            'initial_capital': self.portfolio.portfolio_value_history[0]['total_value'],
            'final_portfolio_value': self.portfolio.portfolio_value_history[-1]['total_value'],
            'total_return_pct': total_return,
            'benchmark_return_pct': benchmark_return,
            'annualized_return_pct': annualized_return,
            'annualized_volatility_pct': annualized_vol,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown,
            'total_trades': len(trades),
            'win_rate_pct': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'trades': trades.to_dict('records'),
            'equity_curve': results[['strategy', 'benchmark']].reset_index().to_dict('records'),
            'positions': self.portfolio.positions
        }
    
    def plot_results(self, save_path: str = None):
        """Plot backtest results.
        
        Args:
            save_path: Optional path to save the plot
        """
        if not self.results:
            print("No results to plot. Run backtest first.")
            return
        
        try:
            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
            
            # Get equity curve data
            equity = self.results.get('equity_curve')
            if equity is None:
                print("No equity curve data available.")
                return
                
            # Handle case where date is in index
            if isinstance(equity, pd.DataFrame):
                if 'date' in equity.columns:
                    dates = pd.to_datetime(equity['date'])
                else:
                    dates = equity.index.to_series()
                
                strategy_values = equity.get('strategy', pd.Series())
                benchmark_values = equity.get('benchmark', pd.Series())
            else:
                print(f"Unexpected equity curve format: {type(equity)}")
                return
            
            # Plot equity curve if we have valid data
            if not dates.empty and not strategy_values.empty:
                ax1.plot(dates, strategy_values, label='Strategy', linewidth=2)
                
                if not benchmark_values.empty:
                    ax1.plot(dates, benchmark_values, label='Buy & Hold', linestyle='--', alpha=0.7)
                
                ax1.set_title('Equity Curve')
                ax1.set_ylabel('Portfolio Value ($)')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # Plot drawdown
                rolling_max = strategy_values.cummax()
                drawdown = (strategy_values - rolling_max) / rolling_max * 100
                
                ax2.fill_between(dates, drawdown, 0, color='red', alpha=0.3)
                ax2.set_title('Drawdown')
                ax2.set_ylabel('Drawdown (%')
                ax2.set_xlabel('Date')
                ax2.grid(True, alpha=0.3)
                
                plt.tight_layout()
                
                if save_path:
                    plt.savefig(save_path, dpi=300, bbox_inches='tight')
                    print(f"Plot saved to {save_path}")
                else:
                    plt.show()
            else:
                print("Insufficient data to plot equity curve.")
                
        except Exception as e:
            print(f"Error plotting results: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _safe_date_format(self, date_value, default="N/A"):
        """Safely format a date, handling NaT and None values."""
        if pd.isna(date_value) or date_value is None:
            return default
        if hasattr(date_value, 'strftime'):
            return date_value.strftime('%Y-%m-%d')
        return str(date_value)
        
    def print_summary(self):
        """Print a summary of the backtest results."""
        if not self.results:
            print("No results to display. Run backtest first.")
            return
        
        res = self.results
        
        print("\n" + "="*50)
        print(f"BACKTEST SUMMARY - {res.get('ticker', 'N/A')}")
        print(f"Period: {self._safe_date_format(res.get('start_date'))} to {self._safe_date_format(res.get('end_date'))}")
        print("-"*50)
        
        # Portfolio metrics
        print(f"Initial Capital: ${res['initial_capital']:,.2f}")
        print(f"Final Portfolio Value: ${res['final_portfolio_value']:,.2f}")
        print(f"Total Return: {res['total_return_pct']:,.2f}%")
        print(f"Annualized Return: {res['annualized_return_pct']:,.2f}%")
        print(f"Annualized Volatility: {res['annualized_volatility_pct']:,.2f}%")
        print(f"Sharpe Ratio: {res['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {res['max_drawdown_pct']:,.2f}%")
        
        # Benchmark comparison
        print("\n" + "-"*50)
        print(f"Benchmark Return: {res['benchmark_return_pct']:,.2f}%")
        print(f"Alpha (vs. Benchmark): {res['total_return_pct'] - res['benchmark_return_pct']:,.2f}%")
        
        # Trade statistics
        if res['total_trades'] > 0:
            print("\n" + "-"*50)
            print(f"Total Trades: {res['total_trades']}")
            print(f"Win Rate: {res['win_rate_pct']:.1f}%")
            print(f"Average Win: ${res['avg_win']:,.2f}")
            print(f"Average Loss: ${res['avg_loss']:,.2f}")
            print(f"Profit Factor: {res['profit_factor']:.2f}")
        
        print("="*50 + "\n")
