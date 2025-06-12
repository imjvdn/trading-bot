#!/usr/bin/env python3
"""
Hedge Fund Simulator - Example Script
------------------------------------
This script demonstrates how to use the hedge fund simulator to backtest
a simple moving average crossover strategy on AAPL stock.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Import the simulator components
from hedgefund_simulator.backtest_engine import BacktestEngine
from hedgefund_simulator.config import CONFIG

# Set up logging
import logging

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backtest.log')
    ]
)

# Set debug level for our package
logging.getLogger('hedgefund_simulator').setLevel(logging.DEBUG)

# Configure console handler for debug messages
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('hedgefund_simulator.agents.risk_manager_agent').addHandler(console)

logger = logging.getLogger(__name__)

def run_backtest():
    """Run a backtest with the hedge fund simulator."""
    logger.info("Starting backtest...")
    
    try:
        # Initialize the backtest engine with configuration
        engine = BacktestEngine(CONFIG)
        
        # Run the backtest for AAPL
        ticker = "AAPL"
        initial_cash = 100000.0  # $100,000 initial capital
        
        logger.info(f"Running backtest for {ticker} from {CONFIG['market_data']['start_date']} to {CONFIG['market_data']['end_date']}")
        
        # Run the backtest
        results = engine.run_backtest(ticker, initial_cash)
        
        # Print summary
        engine.print_summary()
        
        # Plot results
        plot_file = f"{ticker.lower()}_backtest_results.png"
        engine.plot_results(plot_file)
        logger.info(f"Results plot saved to {plot_file}")
        
        # Show the plot (uncomment if running in a notebook)
        # plt.show()
        
        return results
        
    except Exception as e:
        logger.error(f"Error during backtest: {str(e)}", exc_info=True)
        raise

def analyze_results(results):
    """Analyze and print detailed results from the backtest."""
    if not results:
        print("No results to analyze.")
        return
    
    print("\n" + "="*80)
    print("DETAILED BACKTEST ANALYSIS")
    print("="*80)
    
    try:
        # Extract trade history if available
        if 'trades' not in results or not results['trades']:
            print("\nNo trade history available for analysis.")
            return
            
        trades = pd.DataFrame(results['trades'])
        
        if not trades.empty:
            # Check if we have PnL information
            pnl_column = None
            for col in ['realized_pnl', 'pnl', 'profit_loss']:
                if col in trades.columns:
                    pnl_column = col
                    break
            
            if pnl_column is None:
                print("\nNo PnL information available in trade history.")
                print("Available columns:", ", ".join(trades.columns))
                return
                
            # Calculate trade statistics
            winning_trades = trades[trades[pnl_column] > 0]
            losing_trades = trades[trades[pnl_column] < 0]
            
            print(f"\nTrade Statistics (using '{pnl_column}' column):")
            print(f"  - Total Trades: {len(trades)}")
            
            if len(trades) > 0:
                print(f"  - Winning Trades: {len(winning_trades)} ({len(winning_trades)/len(trades)*100:.1f}%)")
                print(f"  - Losing Trades: {len(losing_trades)} ({len(losing_trades)/len(trades)*100:.1f}%)")
                
                if not winning_trades.empty:
                    print(f"\nWinning Trades:")
                    print(f"  - Avg. Return: ${winning_trades[pnl_column].mean():.2f} per trade")
                    print(f"  - Max Return: ${winning_trades[pnl_column].max():.2f}")
                    print(f"  - Min Return: ${winning_trades[pnl_column].min():.2f}")
                
                if not losing_trades.empty:
                    print(f"\nLosing Trades:")
                    print(f"  - Avg. Loss: ${losing_trades[pnl_column].mean():.2f} per trade")
                    print(f"  - Max Loss: ${losing_trades[pnl_column].min():.2f}")
                    print(f"  - Min Loss: ${losing_trades[pnl_column].max():.2f}")
            
            # Print first few trades for reference
            print("\nFirst few trades:")
            print(trades.head().to_string())
    except Exception as e:
        print(f"\nError analyzing results: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Extract equity curve
    equity_curve = pd.DataFrame(results['equity_curve'])
    
    if not equity_curve.empty:
        # Calculate drawdown
        equity_curve['peak'] = equity_curve['strategy'].cummax()
        equity_curve['drawdown'] = (equity_curve['strategy'] - equity_curve['peak']) / equity_curve['peak'] * 100
        
        print("\nEquity Curve Analysis:")
        print(f"  - Initial Capital: ${results['initial_capital']:,.2f}")
        print(f"  - Final Portfolio Value: ${results['final_portfolio_value']:,.2f}")
        print(f"  - Total Return: {results['total_return_pct']:,.2f}%")
        print(f"  - Annualized Return: {results['annualized_return_pct']:,.2f}%")
        print(f"  - Max Drawdown: {equity_curve['drawdown'].min():.2f}%")
        print(f"  - Volatility: {results['annualized_volatility_pct']:.2f}%")
        print(f"  - Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    
    print("\n" + "="*80 + "\n")

def main():
    """Main function to run the example."""
    print("="*80)
    print("HEDGE FUND SIMULATOR - EXAMPLE BACKTEST")
    print("="*80)
    print(f"Strategy: Moving Average Crossover (5/20)")
    print(f"Asset: AAPL")
    print(f"Date Range: {CONFIG['market_data']['start_date']} to {CONFIG['market_data']['end_date']}")
    print("="*80 + "\n")
    
    # Run the backtest
    results = run_backtest()
    
    # Analyze results
    if results:
        analyze_results(results)
    
    print("Backtest completed successfully!")

if __name__ == "__main__":
    main()
