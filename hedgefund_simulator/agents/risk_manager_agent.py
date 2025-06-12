import pandas as pd
from typing import Dict, Any, Tuple, Optional
from .base_agent import BaseAgent

class RiskManagerAgent(BaseAgent):
    """Agent responsible for managing risk and position sizing."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the RiskManagerAgent.
        
        Args:
            config: Configuration dictionary with optional keys:
                   - max_position_size: Maximum position size as percentage of portfolio (default: 0.1)
                   - stop_loss_pct: Stop loss percentage (default: 0.05)
                   - take_profit_pct: Take profit percentage (default: 0.1)
                   - max_portfolio_risk: Maximum risk per trade as percentage of portfolio (default: 0.02)
        """
        super().__init__(config)
        self.max_position_size = self.config.get('max_position_size', 0.1)
        self.stop_loss_pct = self.config.get('stop_loss_pct', 0.05)
        self.take_profit_pct = self.config.get('take_profit_pct', 0.1)
        self.max_portfolio_risk = self.config.get('max_portfolio_risk', 0.02)
    
    def calculate_position_size(
        self, 
        price: float, 
        portfolio_value: float,
        atr: Optional[float] = None
    ) -> Tuple[int, float]:
        """Calculate the optimal position size based on risk parameters.
        
        Args:
            price: Current price of the asset
            portfolio_value: Total value of the portfolio
            atr: Average True Range (optional, for volatility-based sizing)
            
        Returns:
            Tuple of (quantity, position_value)
        """
        # Calculate maximum position value based on portfolio percentage
        max_position_value = portfolio_value * self.max_position_size
        
        # If ATR is provided, adjust position size based on volatility
        if atr is not None and atr > 0:
            # Use ATR to scale position size (higher ATR = smaller position)
            volatility_factor = 1.0 / (1.0 + atr / price)
            max_position_value *= volatility_factor
        
        # Calculate quantity based on position value and current price
        quantity = int(max_position_value / price)
        
        # Ensure we have at least 1 share if we can afford it
        if quantity == 0 and max_position_value >= price:
            quantity = 1
        
        position_value = quantity * price
        
        return quantity, position_value
    
    def calculate_stop_loss_and_take_profit(
        self, 
        entry_price: float, 
        signal: int
    ) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels.
        
        Args:
            entry_price: Entry price of the position
            signal: Signal direction (1 for long, -1 for short)
            
        Returns:
            Tuple of (stop_loss, take_profit)
        """
        if signal > 0:  # Long position
            stop_loss = entry_price * (1 - self.stop_loss_pct)
            take_profit = entry_price * (1 + self.take_profit_pct)
        else:  # Short position
            stop_loss = entry_price * (1 + self.stop_loss_pct)
            take_profit = entry_price * (1 - self.take_profit_pct)
            
        return stop_loss, take_profit
    
    def check_risk_limits(
        self,
        current_position: Dict[str, Any],
        price_data: pd.Series,
        portfolio_value: float
    ) -> Dict[str, Any]:
        """Check if any risk limits have been hit for the current position.
        
        Args:
            current_position: Dictionary containing position details
            price_data: Current price data (must contain 'High', 'Low', 'Close')
            portfolio_value: Current total portfolio value
            
        Returns:
            Dictionary with updated position and any actions to take
        """
        if not current_position:
            return {'action': 'hold', 'reason': 'no_position'}
        
        current_price = price_data['Close']
        entry_price = current_position['entry_price']
        stop_loss = current_position['stop_loss']
        take_profit = current_position['take_profit']
        
        # Check stop loss and take profit
        if current_position['direction'] == 'long':
            if current_price <= stop_loss:
                return {'action': 'sell', 'reason': 'stop_loss', 'price': stop_loss}
            elif current_price >= take_profit:
                return {'action': 'sell', 'reason': 'take_profit', 'price': take_profit}
        else:  # short position
            if current_price >= stop_loss:
                return {'action': 'buy', 'reason': 'stop_loss', 'price': stop_loss}
            elif current_price <= take_profit:
                return {'action': 'buy', 'reason': 'take_profit', 'price': take_profit}
        
        # Check if position size exceeds maximum allowed
        position_value = current_position['quantity'] * current_price
        max_allowed = portfolio_value * self.max_position_size
        
        if position_value > max_allowed * 1.1:  # 10% buffer to avoid flip-flopping
            excess = position_value - max_allowed
            reduce_by = int(excess / current_price)
            if reduce_by > 0:
                return {
                    'action': 'reduce', 
                    'reason': 'position_size_limit',
                    'reduce_by': reduce_by
                }
        
        return {'action': 'hold', 'reason': 'no_trigger'}
    
    def process(
        self, 
        signal: int, 
        price_data: pd.Series, 
        current_position: Dict[str, Any],
        portfolio_value: float,
        atr: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process risk management for a potential trade.
        
        Args:
            signal: Trading signal from strategy (1 for buy, -1 for sell, 0 for hold)
            price_data: Current price data
            current_position: Current position details
            portfolio_value: Total portfolio value
            atr: Average True Range (optional)
            
        Returns:
            Dictionary with trade instructions and risk parameters
        """
        result = {
            'action': 'hold',
            'reason': 'no_signal',
            'quantity': 0,
            'price': price_data['Close'],
            'stop_loss': None,
            'take_profit': None
        }
        
        # First check if we need to exit any existing positions due to risk limits
        if current_position:
            risk_check = self.check_risk_limits(current_position, price_data, portfolio_value)
            if risk_check['action'] != 'hold':
                return {**result, **risk_check}
        
        # If no existing position and we have a signal, calculate position size
        if not current_position and signal != 0:
            price = price_data['Close']
            quantity, position_value = self.calculate_position_size(
                price, portfolio_value, atr
            )
            
            if quantity > 0:
                stop_loss, take_profit = self.calculate_stop_loss_and_take_profit(
                    price, signal
                )
                
                result.update({
                    'action': 'buy' if signal > 0 else 'sell',
                    'reason': 'signal',
                    'quantity': quantity,
                    'price': price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                })
        
        return result
