import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional
from .base_agent import BaseAgent

class MarketDataAgent(BaseAgent):
    """Agent responsible for fetching and preparing market data."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the MarketDataAgent.
        
        Args:
            config: Configuration dictionary with optional keys:
                   - start_date: Start date for data in 'YYYY-MM-DD' format
                   - end_date: End date for data in 'YYYY-MM-DD' format
                   - interval: Data interval ('1d', '1h', etc.)
        """
        super().__init__(config)
        self.start_date = self.config.get('start_date', '2024-01-01')
        self.end_date = self.config.get('end_date', '2024-01-31')
        self.interval = self.config.get('interval', '1d')
    
    def fetch_data(self, ticker: str) -> pd.DataFrame:
        """Fetch historical market data for a given ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            DataFrame containing OHLCV data with date index
        """
        try:
            data = yf.download(
                ticker,
                start=self.start_date,
                end=self.end_date,
                interval=self.interval,
                progress=False
            )
            
            if data.empty:
                raise ValueError(f"No data found for {ticker}")
                
            return data
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            raise
    
    def add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the market data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with additional technical indicators
        """
        df = data.copy()
        
        # Simple Moving Averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['BB_upper'] = df['SMA_20'] + 2 * df['Close'].rolling(window=20).std()
        df['BB_lower'] = df['SMA_20'] - 2 * df['Close'].rolling(window=20).std()
        
        return df
    
    def process(self, ticker: str) -> pd.DataFrame:
        """Fetch and process market data for a given ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            Processed DataFrame with market data and technical indicators
        """
        print(f"Fetching data for {ticker} from {self.start_date} to {self.end_date}")
        data = self.fetch_data(ticker)
        data = self.add_technical_indicators(data)
        return data
