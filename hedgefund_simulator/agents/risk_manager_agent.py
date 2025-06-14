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
        import logging
        logger = logging.getLogger(__name__)
        
        # Safely extract scalar values from potential pandas Series/DataFrames
        price_val = float(price.iloc[-1] if hasattr(price, 'iloc') else price)
        portfolio_val = float(portfolio_value.iloc[-1] if hasattr(portfolio_value, 'iloc') else portfolio_value)
        atr_val = float(atr.iloc[-1]) if atr is not None and hasattr(atr, 'iloc') and not atr.empty else atr
        
        # Format ATR value safely
        atr_str = f"{atr_val:.4f}" if atr_val is not None else "N/A"
        
        logger.debug(
            f"Calculating position size - "
            f"Price: ${price_val:.2f}, "
            f"Portfolio: ${portfolio_val:.2f}, "
            f"ATR: {atr_str}"
        )
        
        # Calculate maximum position value based on portfolio percentage
        max_position_value = portfolio_val * self.max_position_size
        logger.debug(f"Max position value ({self.max_position_size*100}% of portfolio): ${max_position_value:.2f}")
        
        # If ATR is provided, adjust position size based on volatility
        if atr is not None and atr > 0:
            # Use ATR to scale position size (higher ATR = smaller position)
            volatility_factor = 1.0 / (1.0 + atr / price)
            original_max = max_position_value
            max_position_value *= volatility_factor
            logger.debug(f"ATR-based adjustment - Volatility factor: {volatility_factor:.4f}, "
                       f"Adjusted max position: ${max_position_value:.2f} (from ${original_max:.2f})")
        
        # Calculate quantity based on position value and current price
        if price_val <= 0:
            logger.warning(f"Invalid price (${price_val:.2f}) - cannot calculate position size")
            return 0, 0.0
            
        # Ensure we're not dividing by a very small number
        if abs(price_val) < 1e-8:
            logger.warning(f"Price too close to zero: ${price_val:.8f}")
            return 0, 0.0
            
        # Calculate quantity and ensure it's at least 1 if we have enough cash for at least 1 share
        quantity = int(max_position_value / price_val)
        
        # Log detailed calculation information
        logger.debug(
            f"Position size calculation details:\n"
            f"  - Price: ${price_val:.2f}\n"
            f"  - Portfolio value: ${portfolio_val:.2f}\n"
            f"  - Max position size: {self.max_position_size*100}% of portfolio = ${max_position_value:.2f}\n"
            f"  - Raw quantity: {max_position_value:.2f} / {price_val:.2f} = {quantity} shares\n"
            f"  - Position value: ${quantity * price_val:.2f}"
        )
        
        # If we have enough for at least 1 share but got 0, log a warning
        if quantity == 0 and max_position_value >= price_val:
            logger.warning(
                f"Position size rounded to 0 despite having sufficient funds. "
                f"Price: ${price_val:.2f}, Max position: ${max_position_value:.2f}, "
                f"Min position: ${price_val:.2f}"
            )
            # Return at least 1 share if we can afford it
            if max_position_value >= price_val:
                quantity = 1
                logger.info(f"Adjusted quantity to 1 share (${price_val:.2f} <= ${max_position_value:.2f})")
        
        # Ensure we have at least 1 share if we can afford it
        if quantity == 0 and max_position_value >= price_val:
            quantity = 1
            logger.debug("Adjusted quantity to minimum of 1 share")
        elif quantity == 0:
            logger.warning(f"Insufficient funds for 1 share - Need ${price_val:.2f} but only ${max_position_value:.2f} available")
        
        position_value = quantity * price_val
        
        logger.info(f"Position size: {quantity} shares (${position_value:.2f}) at ${price_val:.2f} each")
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
    
    def _get_scalar_value(self, value):
        """Helper method to safely extract scalar value from pandas objects."""
        if hasattr(value, 'iloc'):
            return value.iloc[-1] if len(value) > 0 else value.iloc[0] if hasattr(value, 'iloc') else value
        return value
    
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
        
        # Ensure we're working with scalar values
        current_price = self._get_scalar_value(price_data['Close'] if hasattr(price_data, 'Close') else price_data)
        entry_price = self._get_scalar_value(current_position.get('avg_price', current_price))
        stop_loss = self._get_scalar_value(current_position.get('stop_loss', 0))
        take_profit = self._get_scalar_value(current_position.get('take_profit', float('inf')))
        
        # Determine position direction (default to long if not specified)
        position_direction = current_position.get('direction', 'long')
        
        # Check stop loss and take profit
        if position_direction == 'long':
            if current_price <= stop_loss:
                return {'action': 'sell', 'reason': 'stop_loss', 'price': float(stop_loss)}
            elif current_price >= take_profit:
                return {'action': 'sell', 'reason': 'take_profit', 'price': float(take_profit)}
        else:  # short position
            if current_price >= stop_loss:
                return {'action': 'buy', 'reason': 'stop_loss', 'price': float(stop_loss)}
            elif current_price <= take_profit:
                return {'action': 'buy', 'reason': 'take_profit', 'price': float(take_profit)}
        
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
                    'reduce_by': reduce_by,
                    'price': float(current_price),
                    'quantity': min(reduce_by, current_position['quantity'])
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
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(
            f"Processing signal - Signal: {signal}, "
            f"Current position: {current_position}, "
            f"Portfolio value: ${portfolio_value:.2f}, "
            f"ATR: {atr}"
        )
        
        if signal == 0:
            logger.debug("No signal (0) - returning hold")
            return {'action': 'hold', 'reason': 'no_signal'}
            
        # Get current price and ensure it's a scalar
        current_price = self._get_scalar_value(price_data['Close'] if hasattr(price_data, 'Close') else price_data)
        logger.debug(f"Current price: ${current_price:.2f}")
        
        # Check risk limits for existing position
        logger.debug("Checking risk limits...")
        risk_check = self.check_risk_limits(current_position, price_data, portfolio_value)
        if risk_check['action'] != 'hold':
            logger.debug(f"Risk check triggered action: {risk_check}")
            return risk_check
        
        logger.debug("No risk limits triggered")
            
        # If we get here, we have a valid signal and no risk limits were hit
        action = 'buy' if signal > 0 else 'sell'
        logger.debug(f"Processing {action} signal")
        
        # Log position sizing inputs
        logger.debug(
            f"Position sizing inputs - "
            f"Price: ${current_price:.2f}, "
            f"Portfolio: ${portfolio_value:.2f}, "
            f"Max position size: {self.max_position_size*100}% = ${portfolio_value * self.max_position_size:.2f}, "
            f"ATR: {atr}"
        )
        
        # Calculate position size
        quantity, position_value = self.calculate_position_size(
            price=current_price,
            portfolio_value=portfolio_value,
            atr=atr
        )
        
        # Log position sizing results
        logger.debug(
            f"Position sizing results - "
            f"Quantity: {quantity}, "
            f"Position value: ${position_value:.2f}, "
            f"As % of portfolio: {position_value/portfolio_value*100:.2f}%"
        )
        
        # Calculate stop loss and take profit levels
        stop_loss, take_profit = self.calculate_stop_loss_and_take_profit(
            entry_price=current_price,
            signal=signal
        )
        
        logger.debug(
            f"Stop loss: ${stop_loss:.2f} ({abs((stop_loss-current_price)/current_price*100):.2f}%), "
            f"Take profit: ${take_profit:.2f} ({abs((take_profit-current_price)/current_price*100):.2f}%)"
        )
        
        result = {
            'action': 'buy' if signal > 0 else 'sell',
            'reason': 'signal',
            'quantity': quantity,
            'price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
        
        return result
