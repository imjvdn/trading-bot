import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from .base_agent import BaseAgent

class QuantAgent(BaseAgent):
    """Agent responsible for generating trading signals based on quantitative strategies."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the QuantAgent.
        
        Args:
            config: Configuration dictionary with optional keys:
                   - fast_ma: Period for fast moving average (default: 5)
                   - slow_ma: Period for slow moving average (default: 20)
                   - rsi_overbought: RSI threshold for overbought (default: 70)
                   - rsi_oversold: RSI threshold for oversold (default: 30)
        """
        super().__init__(config)
        self.fast_ma = self.config.get('fast_ma', 5)
        self.slow_ma = self.config.get('slow_ma', 20)
        self.rsi_overbought = self.config.get('rsi_overbought', 70)
        self.rsi_oversold = self.config.get('rsi_oversold', 30)
    
    def moving_average_crossover(self, data: pd.DataFrame) -> pd.Series:
        """Generate signals based on moving average crossover strategy.
        
        Args:
            data: DataFrame containing price data with SMA columns
            
        Returns:
            Series with signals (1 for buy, -1 for sell, 0 for hold)
        """
        signals = pd.Series(0, index=data.index)
        
        # Generate signals based on crossover
        signals[data[f'SMA_{self.fast_ma}'] > data[f'SMA_{self.slow_ma}']] = 1
        signals[data[f'SMA_{self.fast_ma}'] < data[f'SMA_{self.slow_ma}']] = -1
        
        # Only take the first signal in each direction
        signals = signals.diff()
        signals[signals == 0] = 0
        
        return signals
    
    def rsi_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate signals based on RSI indicator.
        
        Args:
            data: DataFrame containing RSI data
            
        Returns:
            Series with signals (1 for buy, -1 for sell, 0 for hold)
        """
        signals = pd.Series(0, index=data.index)
        
        # Buy when RSI crosses above oversold
        signals[(data['RSI'] > self.rsi_oversold) & 
               (data['RSI'].shift(1) <= self.rsi_oversold)] = 1
        
        # Sell when RSI crosses below overbought
        signals[(data['RSI'] < self.rsi_overbought) & 
               (data['RSI'].shift(1) >= self.rsi_overbought)] = -1
        
        return signals
    
    def combine_signals(self, *signal_series: pd.Series) -> pd.Series:
        """Combine multiple signal series into a single signal series.
        
        Args:
            *signal_series: One or more signal series to combine
            
        Returns:
            Combined signal series
        """
        if not signal_series:
            return pd.Series(0, index=pd.DatetimeIndex([]))
        
        # Start with the first series
        combined = signal_series[0].copy()
        
        # Combine with other series
        for series in signal_series[1:]:
            combined = combined.add(series, fill_value=0)
        
        # Normalize to -1, 0, 1
        combined[combined > 0] = 1
        combined[combined < 0] = -1
        
        return combined.astype(int)
    
    def process(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Generate trading signals based on the input data.
        
        Args:
            data: DataFrame containing market data with indicators
            
        Returns:
            Dictionary containing signal series for each strategy
        """
        signals = {}
        
        # Generate signals from different strategies
        signals['ma_crossover'] = self.moving_average_crossover(data)
        signals['rsi'] = self.rsi_signals(data)
        
        # Combine all signals
        signals['combined'] = self.combine_signals(
            signals['ma_crossover'],
            signals['rsi']
        )
        
        return signals
