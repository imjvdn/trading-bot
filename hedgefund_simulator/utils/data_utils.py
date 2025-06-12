import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
import yfinance as yf

def calculate_atr(data: pd.DataFrame, window: int = 14) -> pd.Series:
    """Calculate the Average True Range (ATR) indicator.
    
    Args:
        data: DataFrame with 'High', 'Low', 'Close' columns
        window: Lookback period for ATR calculation
        
    Returns:
        Series containing ATR values
    """
    high = data['High']
    low = data['Low']
    close = data['Close']
    
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=window).mean()
    
    return atr

def calculate_bollinger_bands(data: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Calculate Bollinger Bands.
    
    Args:
        data: DataFrame with 'Close' column
        window: Lookback period for moving average
        num_std: Number of standard deviations for the bands
        
    Returns:
        DataFrame with 'upper', 'middle', 'lower' band columns
    """
    df = data.copy()
    df['middle'] = df['Close'].rolling(window=window).mean()
    df['std'] = df['Close'].rolling(window=window).std()
    
    df['upper'] = df['middle'] + (df['std'] * num_std)
    df['lower'] = df['middle'] - (df['std'] * num_std)
    
    return df[['upper', 'middle', 'lower']]

def calculate_rsi(data: pd.DataFrame, window: int = 14) -> pd.Series:
    """Calculate the Relative Strength Index (RSI).
    
    Args:
        data: DataFrame with 'Close' column
        window: Lookback period for RSI calculation
        
    Returns:
        Series containing RSI values
    """
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_macd(
    data: pd.DataFrame, 
    fast_window: int = 12, 
    slow_window: int = 26, 
    signal_window: int = 9
) -> pd.DataFrame:
    """Calculate MACD indicator.
    
    Args:
        data: DataFrame with 'Close' column
        fast_window: Period for fast EMA
        slow_window: Period for slow EMA
        signal_window: Period for signal line
        
    Returns:
        DataFrame with 'macd', 'signal', 'histogram' columns
    """
    df = data.copy()
    
    # Calculate EMAs
    fast_ema = df['Close'].ewm(span=fast_window, adjust=False).mean()
    slow_ema = df['Close'].ewm(span=slow_window, adjust=False).mean()
    
    # Calculate MACD and signal line
    df['macd'] = fast_ema - slow_ema
    df['signal'] = df['macd'].ewm(span=signal_window, adjust=False).mean()
    df['histogram'] = df['macd'] - df['signal']
    
    return df[['macd', 'signal', 'histogram']]

def calculate_obv(data: pd.DataFrame) -> pd.Series:
    """Calculate On-Balance Volume (OBV).
    
    Args:
        data: DataFrame with 'Close' and 'Volume' columns
        
    Returns:
        Series containing OBV values
    """
    obv = (np.sign(data['Close'].diff()) * data['Volume']).fillna(0).cumsum()
    return obv

def add_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """Add common technical indicators to the DataFrame.
    
    Args:
        data: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added technical indicators
    """
    df = data.copy()
    
    # Moving Averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    
    # RSI
    df['RSI'] = calculate_rsi(df)
    
    # MACD
    macd = calculate_macd(df)
    df = pd.concat([df, macd], axis=1)
    
    # Bollinger Bands
    bb = calculate_bollinger_bands(df)
    df = pd.concat([df, bb], axis=1)
    
    # ATR
    df['ATR'] = calculate_atr(df)
    
    # OBV
    df['OBV'] = calculate_obv(df)
    
    # Daily Returns
    df['Returns'] = df['Close'].pct_change()
    
    # Volatility (20-day rolling std of returns)
    df['Volatility'] = df['Returns'].rolling(window=20).std() * np.sqrt(252)  # Annualized
    
    return df

def fetch_yahoo_data(
    ticker: str, 
    start_date: str, 
    end_date: str, 
    interval: str = '1d',
    add_indicators: bool = True
) -> pd.DataFrame:
    """Fetch data from Yahoo Finance and add technical indicators.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        interval: Data interval ('1d', '1h', etc.)
        add_indicators: Whether to add technical indicators
        
    Returns:
        DataFrame with market data and indicators
    """
    try:
        data = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            interval=interval,
            progress=False
        )
        
        if data.empty:
            raise ValueError(f"No data found for {ticker}")
        
        if add_indicators:
            data = add_technical_indicators(data)
            
        return data
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        raise

def resample_data(data: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample OHLCV data to a different timeframe.
    
    Args:
        data: DataFrame with OHLCV data
        timeframe: Target timeframe (e.g., '1D' for daily, '1H' for hourly)
        
    Returns:
        Resampled DataFrame
    """
    if not isinstance(data.index, pd.DatetimeIndex):
        data = data.copy()
        data.index = pd.to_datetime(data.index)
    
    # Resample OHLCV data
    ohlc_dict = {
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum',
        'Adj Close': 'last'
    }
    
    resampled = data.resample(timeframe).apply(ohlc_dict)
    
    # Drop any rows with missing data
    resampled = resampled.dropna()
    
    return resampled
