import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import math

def calculate_returns(prices: Union[pd.Series, np.ndarray], method: str = 'simple') -> Union[pd.Series, np.ndarray]:
    """Calculate returns from price data.
    
    Args:
        prices: Series or array of prices
        method: 'simple' for simple returns, 'log' for log returns
        
    Returns:
        Series or array of returns
    """
    if method == 'simple':
        returns = prices.pct_change().dropna() if isinstance(prices, pd.Series) else np.diff(prices) / prices[:-1]
    elif method == 'log':
        returns = np.log(prices / prices.shift(1)).dropna() if isinstance(prices, pd.Series) else np.log(prices[1:] / prices[:-1])
    else:
        raise ValueError("method must be 'simple' or 'log'")
    
    return returns

def calculate_annualized_return(returns: Union[pd.Series, np.ndarray], periods_per_year: int = 252) -> float:
    """Calculate annualized return from return series.
    
    Args:
        returns: Series or array of returns
        periods_per_year: Number of periods per year (252 for daily, 12 for monthly, etc.)
        
    Returns:
        Annualized return as a decimal
    """
    n_periods = len(returns)
    if n_periods == 0:
        return 0.0
    
    if isinstance(returns, pd.Series):
        cumulative_return = (1 + returns).prod() - 1
    else:
        cumulative_return = np.prod(1 + returns) - 1
    
    # Annualize the return
    if n_periods < periods_per_year:
        # If we have less than a year of data, don't annualize
        return cumulative_return
    
    annualized_return = (1 + cumulative_return) ** (periods_per_year / n_periods) - 1
    return annualized_return

def calculate_annualized_volatility(returns: Union[pd.Series, np.ndarray], periods_per_year: int = 252) -> float:
    """Calculate annualized volatility from return series.
    
    Args:
        returns: Series or array of returns
        periods_per_year: Number of periods per year (252 for daily, 12 for monthly, etc.)
        
    Returns:
        Annualized volatility as a decimal
    """
    if len(returns) < 2:
        return 0.0
    
    if isinstance(returns, pd.Series):
        return returns.std() * np.sqrt(periods_per_year)
    else:
        return np.std(returns, ddof=1) * np.sqrt(periods_per_year)

def calculate_sharpe_ratio(
    returns: Union[pd.Series, np.ndarray], 
    risk_free_rate: float = 0.0, 
    periods_per_year: int = 252
) -> float:
    """Calculate the Sharpe ratio.
    
    Args:
        returns: Series or array of returns
        risk_free_rate: Annual risk-free rate (default: 0.0)
        periods_per_year: Number of periods per year
        
    Returns:
        Sharpe ratio (annualized)
    """
    if len(returns) < 2:
        return 0.0
    
    excess_returns = returns - (risk_free_rate / periods_per_year)
    
    if isinstance(returns, pd.Series):
        return_per_period = excess_returns.mean()
        vol_per_period = excess_returns.std()
    else:
        return_per_period = np.mean(excess_returns)
        vol_per_period = np.std(excess_returns, ddof=1)
    
    if vol_per_period == 0:
        return 0.0
    
    # Annualize the ratio
    return (return_per_period / vol_per_period) * np.sqrt(periods_per_year)

def calculate_sortino_ratio(
    returns: Union[pd.Series, np.ndarray], 
    risk_free_rate: float = 0.0, 
    periods_per_year: int = 252
) -> float:
    """Calculate the Sortino ratio.
    
    Args:
        returns: Series or array of returns
        risk_free_rate: Annual risk-free rate (default: 0.0)
        periods_per_year: Number of periods per year
        
    Returns:
        Sortino ratio (annualized)
    """
    if len(returns) < 2:
        return 0.0
    
    excess_returns = returns - (risk_free_rate / periods_per_year)
    
    if isinstance(returns, pd.Series):
        return_per_period = excess_returns.mean()
        # Only consider negative returns for downside deviation
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return float('inf')
        downside_dev = downside_returns.std(ddof=1)
    else:
        return_per_period = np.mean(excess_returns)
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return float('inf')
        downside_dev = np.std(downside_returns, ddof=1)
    
    if downside_dev == 0:
        return float('inf')
    
    # Annualize the ratio
    return (return_per_period / downside_dev) * np.sqrt(periods_per_year)

def calculate_max_drawdown(prices: Union[pd.Series, np.ndarray]) -> float:
    """Calculate maximum drawdown from price series.
    
    Args:
        prices: Series or array of prices
        
    Returns:
        Maximum drawdown as a decimal (e.g., 0.15 for 15%)
    """
    if isinstance(prices, pd.Series):
        prices = prices.values
    
    if len(prices) < 2:
        return 0.0
    
    # Calculate cumulative max
    cum_max = np.maximum.accumulate(prices)
    
    # Calculate drawdown
    drawdown = (prices - cum_max) / cum_max
    
    # Return minimum (most negative) drawdown
    return np.min(drawdown)

def calculate_calmar_ratio(
    returns: Union[pd.Series, np.ndarray], 
    prices: Union[pd.Series, np.ndarray],
    periods_per_year: int = 252
) -> float:
    """Calculate the Calmar ratio (annualized return / max drawdown).
    
    Args:
        returns: Series or array of returns
        prices: Series or array of prices (for drawdown calculation)
        periods_per_year: Number of periods per year
        
    Returns:
        Calmar ratio
    """
    if len(returns) < 2:
        return 0.0
    
    annualized_return = calculate_annualized_return(returns, periods_per_year)
    max_dd = calculate_max_drawdown(prices)
    
    if max_dd == 0:
        return float('inf')
    
    return annualized_return / abs(max_dd)

def calculate_win_rate(trades: pd.DataFrame, pnl_column: str = 'pnl') -> float:
    """Calculate the win rate from a series of trades.
    
    Args:
        trades: DataFrame containing trade data
        pnl_column: Name of the column containing P&L values
        
    Returns:
        Win rate as a decimal (0.0 to 1.0)
    """
    if len(trades) == 0:
        return 0.0
    
    winning_trades = trades[trades[pnl_column] > 0]
    return len(winning_trades) / len(trades)

def calculate_profit_factor(trades: pd.DataFrame, pnl_column: str = 'pnl') -> float:
    """Calculate the profit factor (gross profits / gross losses).
    
    Args:
        trades: DataFrame containing trade data
        pnl_column: Name of the column containing P&L values
        
    Returns:
        Profit factor (1.0 means break-even, >1.0 means profitable)
    """
    if len(trades) == 0:
        return 0.0
    
    gross_profit = trades[trades[pnl_column] > 0][pnl_column].sum()
    gross_loss = abs(trades[trades[pnl_column] < 0][pnl_column].sum())
    
    if gross_loss == 0:
        return float('inf')
    
    return gross_profit / gross_loss

def calculate_expected_return(returns: Union[pd.Series, np.ndarray]) -> float:
    """Calculate the expected return (mean return).
    
    Args:
        returns: Series or array of returns
        
    Returns:
        Expected return as a decimal
    """
    if len(returns) == 0:
        return 0.0
    return np.mean(returns)

def calculate_value_at_risk(
    returns: Union[pd.Series, np.ndarray], 
    confidence_level: float = 0.95
) -> float:
    """Calculate Value at Risk (VaR) using historical simulation.
    
    Args:
        returns: Series or array of returns
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        
    Returns:
        Value at Risk as a decimal (e.g., -0.05 for -5%)
    """
    if len(returns) == 0:
        return 0.0
    return np.percentile(returns, (1 - confidence_level) * 100)

def calculate_conditional_value_at_risk(
    returns: Union[pd.Series, np.ndarray], 
    confidence_level: float = 0.95
) -> float:
    """Calculate Conditional Value at Risk (CVaR) or Expected Shortfall.
    
    Args:
        returns: Series or array of returns
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        
    Returns:
        Conditional Value at Risk as a decimal
    """
    if len(returns) == 0:
        return 0.0
    
    var = calculate_value_at_risk(returns, confidence_level)
    return np.mean(returns[returns <= var])

def calculate_beta(
    asset_returns: Union[pd.Series, np.ndarray],
    benchmark_returns: Union[pd.Series, np.ndarray]
) -> float:
    """Calculate beta (systematic risk) of an asset relative to a benchmark.
    
    Args:
        asset_returns: Returns of the asset
        benchmark_returns: Returns of the benchmark
        
    Returns:
        Beta coefficient
    """
    if len(asset_returns) != len(benchmark_returns) or len(asset_returns) < 2:
        return 0.0
    
    # Calculate covariance and variance
    cov_matrix = np.cov(asset_returns, benchmark_returns)
    beta = cov_matrix[0, 1] / cov_matrix[1, 1]
    
    return beta

def calculate_alpha(
    asset_returns: Union[pd.Series, np.ndarray],
    benchmark_returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """Calculate alpha (excess return) of an asset relative to a benchmark.
    
    Args:
        asset_returns: Returns of the asset
        benchmark_returns: Returns of the benchmark
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods per year
        
    Returns:
        Alpha (annualized)
    """
    if len(asset_returns) != len(benchmark_returns) or len(asset_returns) < 2:
        return 0.0
    
    # Calculate beta first
    beta = calculate_beta(asset_returns, benchmark_returns)
    
    # Calculate average returns
    asset_avg_return = np.mean(asset_returns) * periods_per_year
    benchmark_avg_return = np.mean(benchmark_returns) * periods_per_year
    
    # Calculate alpha (annualized)
    alpha = (asset_avg_return - risk_free_rate) - beta * (benchmark_avg_return - risk_free_rate)
    
    return alpha

def calculate_tracking_error(
    asset_returns: Union[pd.Series, np.ndarray],
    benchmark_returns: Union[pd.Series, np.ndarray],
    periods_per_year: int = 252
) -> float:
    """Calculate tracking error (standard deviation of active returns).
    
    Args:
        asset_returns: Returns of the asset
        benchmark_returns: Returns of the benchmark
        periods_per_year: Number of periods per year
        
    Returns:
        Tracking error (annualized)
    """
    if len(asset_returns) != len(benchmark_returns) or len(asset_returns) < 2:
        return 0.0
    
    active_returns = asset_returns - benchmark_returns
    tracking_error = np.std(active_returns, ddof=1) * np.sqrt(periods_per_year)
    
    return tracking_error

def calculate_information_ratio(
    asset_returns: Union[pd.Series, np.ndarray],
    benchmark_returns: Union[pd.Series, np.ndarray],
    periods_per_year: int = 252
) -> float:
    """Calculate the information ratio (excess return / tracking error).
    
    Args:
        asset_returns: Returns of the asset
        benchmark_returns: Returns of the benchmark
        periods_per_year: Number of periods per year
        
    Returns:
        Information ratio (annualized)
    """
    if len(asset_returns) != len(benchmark_returns) or len(asset_returns) < 2:
        return 0.0
    
    # Calculate active returns
    active_returns = asset_returns - benchmark_returns
    
    # Calculate average active return (annualized)
    avg_active_return = np.mean(active_returns) * periods_per_year
    
    # Calculate tracking error (annualized)
    tracking_error = calculate_tracking_error(asset_returns, benchmark_returns, periods_per_year)
    
    if tracking_error == 0:
        return 0.0
    
    return avg_active_return / tracking_error
