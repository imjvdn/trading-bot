import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from .base_agent import BaseAgent

# Set up logging
logger = logging.getLogger(__name__)

class PortfolioManagerAgent(BaseAgent):
    """Agent responsible for managing the portfolio and making final trade decisions."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the PortfolioManagerAgent.
        
        Args:
            config: Configuration dictionary with optional keys:
                   - max_open_positions: Maximum number of simultaneous positions (default: 5)
                   - max_sector_exposure: Maximum exposure to any single sector (default: 0.3)
                   - max_asset_exposure: Maximum exposure to any single asset (default: 0.2)
        """
        super().__init__(config)
        self.max_open_positions = self.config.get('max_open_positions', 5)
        self.max_sector_exposure = self.config.get('max_sector_exposure', 0.3)
        self.max_asset_exposure = self.config.get('max_asset_exposure', 0.2)
        
        # Track portfolio state
        self.positions = {}
        self.cash = 0
        self.trade_history = []
        self.portfolio_value_history = []
    
    def initialize_portfolio(self, initial_cash: float = 100000.0):
        """Initialize the portfolio with starting cash.
        
        Args:
            initial_cash: Initial cash amount (default: 100,000)
        """
        self.cash = initial_cash
        self.positions = {}
        self.trade_history = []
        self.portfolio_value_history = [{
            'date': None,
            'cash': self.cash,
            'positions_value': 0,
            'total_value': self.cash,
            'return_pct': 0.0
        }]
    
    def calculate_portfolio_value(self) -> Dict[str, float]:
        """Calculate current portfolio value and metrics.
        
        Returns:
            Dictionary with portfolio metrics
        """
        positions_value = sum(
            pos['quantity'] * pos['current_price'] 
            for pos in self.positions.values()
        )
        
        total_value = self.cash + positions_value
        
        # Calculate returns if we have history
        initial_value = self.portfolio_value_history[0]['total_value']
        return_pct = ((total_value / initial_value) - 1) * 100 if initial_value > 0 else 0.0
        
        return {
            'cash': self.cash,
            'positions_value': positions_value,
            'total_value': total_value,
            'return_pct': return_pct
        }
    
    def update_positions(self, price_data: Dict[str, pd.Series]):
        """Update position values with latest prices.
        
        Args:
            price_data: Dictionary mapping tickers to their latest price data
        """
        for ticker, position in list(self.positions.items()):
            if ticker in price_data:
                current_price = price_data[ticker]['Close']
                position['current_price'] = current_price
                position['current_value'] = position['quantity'] * current_price
                position['unrealized_pnl'] = position['current_value'] - position['cost_basis']
                position['unrealized_pnl_pct'] = (
                    (position['current_value'] / position['cost_basis'] - 1) * 100 
                    if position['cost_basis'] > 0 else 0.0
                )
    
    def _format_currency(self, value: float) -> str:
        """Format a numeric value as a currency string.
        
        Args:
            value: Numeric value to format
            
        Returns:
            Formatted currency string (e.g., "$1,234.56")
        """
        return f"${value:,.2f}"
    
    def _format_percent(self, value: float) -> str:
        """Format a numeric value as a percentage string.
        
        Args:
            value: Numeric value to format (e.g., 0.05 for 5%)
            
        Returns:
            Formatted percentage string (e.g., "5.00%")
        """
        return f"{value*100:.2f}%"
    
    def _log_trade_execution(self, trade: Dict[str, Any], position: Dict[str, Any], portfolio_value: Dict[str, float]) -> None:
        """Log trade execution details to the console in a clean, tabular format.
        
        Args:
            trade: Trade details
            position: Current position details (after trade)
            portfolio_value: Current portfolio value metrics
        """
        # Initialize header flag if not exists
        if not hasattr(self, '_header_printed'):
            self._header_printed = False
            
        # Format values
        action = trade['action'].upper()
        ticker = trade['ticker']
        quantity = int(trade['quantity'])
        price = float(trade['price'])
        status = trade.get('status', 'pending').upper()
        
        # Format timestamp
        timestamp = pd.to_datetime(trade['timestamp']).strftime('%Y-%m-%d')
        
        # Calculate position value
        position_size = position.get('quantity', 0) if position else 0
        position_value = position_size * position.get('current_price', 0) if position else 0
        total_value = portfolio_value['total_value']
        cash = portfolio_value['cash']
        
        # Print header on first trade only
        if not self._header_printed:
            print("\n" + "=" * 100)
            print(f"{'Date':<10} | {'Ticker':<6} | {'Status':<8} | {'Action':<6} | {'Qty':>8} | {'Price':>10} | {'Cash':>12} | {'Stock':>12} | {'Total':>12}")
            print("-" * 120)
            self._header_printed = True
        
        # Format the output line with fixed width columns
        print(f"{timestamp} | {ticker:6} | {status:8} | {action:6} | {quantity:8d} | ${price:8.2f} | ${cash:10,.2f} | ${position_value:10,.2f} | ${total_value:10,.2f}")
        
        # Print reason if available
        reason = trade.get('reason', '')
        if reason:
            print(f"{'Reason:':<10} {reason}")
            print("-" * 120)
    
    def execute_trade(
        self, 
        ticker: str, 
        action: str, 
        quantity: int, 
        price: float, 
        timestamp: pd.Timestamp,
        reason: str = ""
    ) -> Dict[str, Any]:
        """Execute a trade and update portfolio state.
        
        Args:
            ticker: Stock ticker
            action: 'buy' or 'sell'
            quantity: Number of shares
            price: Execution price
            timestamp: Trade timestamp
            reason: Reason for the trade
            
        Returns:
            Dictionary with trade execution details and status
            
        Example:
            >>> portfolio.execute_trade('AAPL', 'buy', 100, 150.25, pd.Timestamp('2024-01-15'), 'bullish trend')
            {
                'status': 'success',
                'action': 'buy',
                'ticker': 'AAPL',
                'quantity': 100,
                'price': 150.25,
                'value': 15025.0,
                'commission': 15.03,
                'reason': 'bullish trend',
                'timestamp': '2024-01-15T00:00:00',
                'position_after': {...},
                'portfolio_value_after': {...}
            }
        """
        if quantity <= 0:
            error_msg = f"Trade execution failed: Invalid quantity {quantity} for {ticker}"
            logger.error(error_msg)
            return {'status': 'error', 'message': error_msg}
            
        trade_value = quantity * price
        commission = self._calculate_commission(trade_value)
        total_cost = trade_value + commission
        
        trade = {
            'timestamp': timestamp,
            'ticker': ticker,
            'action': action,
            'quantity': quantity,
            'price': price,
            'value': trade_value,
            'commission': commission,
            'reason': reason,
            'status': 'pending'
        }
        
        if action == 'buy':
            if self.cash < total_cost:
                return {'status': 'error', 'message': 'Insufficient cash'}
                
            # Update cash
            self.cash -= total_cost
            
            # Update or create position
            if ticker in self.positions:
                position = self.positions[ticker]
                total_quantity = position['quantity'] + quantity
                total_cost_basis = position['cost_basis'] + trade_value
                position.update({
                    'quantity': total_quantity,
                    'cost_basis': total_cost_basis,
                    'avg_price': total_cost_basis / total_quantity,
                    'current_price': price,
                    'current_value': total_quantity * price,
                    'last_updated': timestamp
                })
            else:
                self.positions[ticker] = {
                    'ticker': ticker,
                    'quantity': quantity,
                    'cost_basis': trade_value,
                    'avg_price': price,
                    'current_price': price,
                    'current_value': trade_value,
                    'entry_date': timestamp,
                    'last_updated': timestamp,
                    'unrealized_pnl': 0.0,
                    'unrealized_pnl_pct': 0.0
                }
                
        elif action == 'sell':
            if ticker not in self.positions or self.positions[ticker]['quantity'] < quantity:
                return {'status': 'error', 'message': 'Insufficient position'}
                
            position = self.positions[ticker]
            
            # Update cash
            self.cash += (trade_value - commission)
            
            # Calculate realized P&L
            cost_basis = position['avg_price'] * quantity
            realized_pnl = trade_value - cost_basis - commission
            realized_pnl_pct = (realized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0
            
            # Update trade with P&L
            trade.update({
                'realized_pnl': realized_pnl,
                'realized_pnl_pct': realized_pnl_pct
            })
            
            # Update or remove position
            if position['quantity'] == quantity:
                # Close entire position
                del self.positions[ticker]
            else:
                # Reduce position
                position['quantity'] -= quantity
                position['cost_basis'] -= cost_basis
                position['current_value'] = position['quantity'] * price
                position['last_updated'] = timestamp
        
        try:
            # Record trade
            self.trade_history.append(trade)
            
            # Update portfolio value history
            portfolio_value = self.calculate_portfolio_value()
            portfolio_snapshot = {
                'date': timestamp,
                **portfolio_value
            }
            self.portfolio_value_history.append(portfolio_snapshot)
            
            # Add position and portfolio info to trade result
            trade_result = {
                'status': 'success',
                **trade,
                'position_after': self.positions.get(ticker, {}).copy(),
                'portfolio_value_after': portfolio_snapshot
            }
            
            # Log the trade execution
            logger.debug(f"About to log trade: {trade}")
            self._log_trade_execution(trade, self.positions.get(ticker, {}), portfolio_value)
            logger.debug("Trade logged successfully")
            
            return trade_result
            
        except Exception as e:
            error_msg = f"Error executing trade: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'status': 'error',
                'message': error_msg,
                'trade': trade
            }
    
    def _calculate_commission(self, trade_value: float) -> float:
        """Calculate commission for a trade (override for custom commission structure).
        
        Args:
            trade_value: Value of the trade
            
        Returns:
            Commission amount
        """
        # Default: $5 per trade or 0.1% of trade value, whichever is greater
        return max(5.0, trade_value * 0.001)
    
    def process(
        self, 
        ticker: str, 
        signal: Dict[str, Any], 
        price_data: pd.Series,
        timestamp: pd.Timestamp
    ) -> Dict[str, Any]:
        """Process a trading signal and execute trades if needed.
        
        Args:
            ticker: Stock ticker
            signal: Signal from risk manager
            price_data: Current price data (pandas Series with price data)
            timestamp: Current timestamp
            
        Returns:
            Trade execution result
        """
        # Extract action and ensure it's valid
        action = signal.get('action', 'hold')
        
        # If action is hold, return early
        if action == 'hold':
            return {'status': 'no_action', 'reason': signal.get('reason', 'no_reason_provided')}
        
        # Validate required fields
        required_fields = ['price', 'quantity']
        for field in required_fields:
            if field not in signal:
                logger.error(f"Missing required field in signal: {field}")
                return {'status': 'error', 'reason': f'missing_{field}'}
        
        # Ensure we're working with scalar values
        try:
            price = float(signal['price'].iloc[-1] if hasattr(signal['price'], 'iloc') else signal['price'])
            quantity = int(signal['quantity'].iloc[-1] if hasattr(signal['quantity'], 'iloc') else signal['quantity'])
        except (ValueError, IndexError) as e:
            logger.error(f"Error processing signal values: {e}")
            return {'status': 'error', 'reason': 'invalid_signal_values'}
            
        # Check if we have enough cash for buy orders
        if action == 'buy':
            portfolio_value = self.calculate_portfolio_value()['total_value']
            max_position_value = portfolio_value * self.max_asset_exposure
            
            # Don't open new positions if we're at max open positions
            if len(self.positions) >= self.max_open_positions and ticker not in self.positions:
                return {'status': 'no_action', 'reason': 'max_positions_reached'}
                
            # Check asset exposure - ensure we're comparing scalar values
            position_value = float(quantity) * float(price)
            if position_value > max_position_value:
                # Adjust quantity to respect max exposure
                max_quantity = int(max_position_value / float(signal['price']))
                if max_quantity < 1:
                    return {'status': 'no_action', 'reason': 'insufficient_funds'}
                signal['quantity'] = max_quantity
        
        # Execute the trade
        return self.execute_trade(
            ticker=ticker,
            action=signal['action'],
            quantity=signal['quantity'],
            price=signal['price'],
            timestamp=timestamp,
            reason=signal.get('reason', '')
        )
