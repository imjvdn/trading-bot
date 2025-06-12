"""Utility functions for plotting financial data and backtest results."""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import seaborn as sns
from matplotlib.gridspec import GridSpec

# Set style
plt.style.use('seaborn')
sns.set_palette("husl")

def plot_equity_curve(
    equity_curve: pd.Series,
    benchmark: Optional[pd.Series] = None,
    title: str = "Equity Curve",
    figsize: Tuple[int, int] = (12, 6)
) -> plt.Figure:
    """Plot equity curve with optional benchmark comparison.
    
    Args:
        equity_curve: Series with equity curve data
        benchmark: Optional benchmark series for comparison
        title: Plot title
        figsize: Figure size (width, height)
        
    Returns:
        Matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot equity curve
    ax.plot(equity_curve.index, equity_curve, label='Strategy', linewidth=2)
    
    # Plot benchmark if provided
    if benchmark is not None:
        ax.plot(benchmark.index, benchmark, label='Benchmark', linestyle='--', alpha=0.7)
    
    # Formatting
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Portfolio Value')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_drawdown(
    equity_curve: pd.Series,
    title: str = "Drawdown",
    figsize: Tuple[int, int] = (12, 4)
) -> plt.Figure:
    """Plot drawdown from equity curve.
    
    Args:
        equity_curve: Series with equity curve data
        title: Plot title
        figsize: Figure size (width, height)
        
    Returns:
        Matplotlib Figure object
    """
    # Calculate drawdown
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max * 100
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot drawdown
    ax.fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3)
    
    # Formatting
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Drawdown (%)')
    ax.grid(True, alpha=0.3)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_monthly_returns_heatmap(
    returns: pd.Series,
    title: str = "Monthly Returns (%)",
    figsize: Tuple[int, int] = (12, 6)
) -> plt.Figure:
    """Plot monthly returns as a heatmap.
    
    Args:
        returns: Series with return data (must have DateTimeIndex)
        title: Plot title
        figsize: Figure size (width, height)
        
    Returns:
        Matplotlib Figure object
    """
    # Convert to DataFrame and extract month/year
    returns_df = returns.to_frame('Returns')
    returns_df['Year'] = returns_df.index.year
    returns_df['Month'] = returns_df.index.month_name().str[:3]
    
    # Pivot for heatmap
    monthly_returns = returns_df.pivot_table(
        index='Year', 
        columns='Month', 
        values='Returns', 
        aggfunc=lambda x: (1 + x).prod() - 1
    ) * 100  # Convert to percentage
    
    # Reorder columns to be Jan-Dec
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_returns = monthly_returns[month_order]
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create heatmap
    sns.heatmap(
        monthly_returns, 
        annot=True, 
        fmt=".1f", 
        cmap='RdYlGn', 
        center=0,
        linewidths=0.5,
        ax=ax
    )
    
    # Formatting
    ax.set_title(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    return fig

def plot_returns_distribution(
    returns: pd.Series,
    title: str = "Returns Distribution",
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """Plot distribution of returns.
    
    Args:
        returns: Series with return data
        title: Plot title
        figsize: Figure size (width, height)
        
    Returns:
        Matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot histogram
    sns.histplot(returns * 100, kde=True, bins=30, ax=ax)
    
    # Add mean and median lines
    mean = returns.mean() * 100
    median = returns.median() * 100
    
    ax.axvline(mean, color='r', linestyle='--', label=f'Mean: {mean:.2f}%')
    ax.axvline(median, color='g', linestyle='-', label=f'Median: {median:.2f}%')
    
    # Formatting
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Daily Return (%)')
    ax.set_ylabel('Frequency')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def plot_rolling_sharpe(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    window: int = 63,  # 3 months of daily data
    title: str = "Rolling Sharpe Ratio (6-Month)",
    figsize: Tuple[int, int] = (12, 4)
) -> plt.Figure:
    """Plot rolling Sharpe ratio.
    
    Args:
        returns: Series with return data
        risk_free_rate: Annual risk-free rate
        window: Rolling window in periods
        title: Plot title
        figsize: Figure size (width, height)
        
    Returns:
        Matplotlib Figure object
    """
    # Calculate excess returns
    excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
    
    # Calculate rolling Sharpe ratio (annualized)
    rolling_sharpe = excess_returns.rolling(window=window).mean() / \
                    excess_returns.rolling(window=window).std() * np.sqrt(252)
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot rolling Sharpe
    ax.plot(rolling_sharpe.index, rolling_sharpe, label='Rolling Sharpe')
    
    # Add horizontal line at 0
    ax.axhline(0, color='black', linestyle='-', alpha=0.3)
    
    # Formatting
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Sharpe Ratio')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_trades(
    prices: pd.Series,
    trades: pd.DataFrame,
    title: str = "Trades",
    figsize: Tuple[int, int] = (14, 8)
) -> plt.Figure:
    """Plot price chart with buy/sell markers.
    
    Args:
        prices: Series of prices
        trades: DataFrame with trade information (must have 'date', 'action', 'price' columns)
        title: Plot title
        figsize: Figure size (width, height)
        
    Returns:
        Matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot price
    ax.plot(prices.index, prices, label='Price', linewidth=2, alpha=0.7)
    
    # Plot trades
    if not trades.empty:
        buy_trades = trades[trades['action'] == 'buy']
        sell_trades = trades[trades['action'] == 'sell']
        
        if not buy_trades.empty:
            ax.scatter(
                buy_trades['date'], 
                buy_trades['price'], 
                color='green', 
                marker='^', 
                s=100,
                label='Buy',
                alpha=0.8
            )
        
        if not sell_trades.empty:
            ax.scatter(
                sell_trades['date'], 
                sell_trades['price'], 
                color='red', 
                marker='v', 
                s=100,
                label='Sell',
                alpha=0.8
            )
    
    # Formatting
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_correlation_heatmap(
    returns_df: pd.DataFrame,
    title: str = "Returns Correlation",
    figsize: Tuple[int, int] = (10, 8)
) -> plt.Figure:
    """Plot correlation heatmap of returns.
    
    Args:
        returns_df: DataFrame with returns (columns = assets, index = dates)
        title: Plot title
        figsize: Figure size (width, height)
        
    Returns:
        Matplotlib Figure object
    """
    # Calculate correlation matrix
    corr = returns_df.corr()
    
    # Create mask for upper triangle
    mask = np.triu(np.ones_like(corr, dtype=bool))
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create heatmap
    sns.heatmap(
        corr, 
        mask=mask,
        annot=True, 
        fmt=".2f", 
        cmap='coolwarm', 
        center=0,
        square=True,
        linewidths=0.5,
        ax=ax
    )
    
    # Formatting
    ax.set_title(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    return fig

def plot_summary(
    equity_curve: pd.Series,
    returns: pd.Series,
    trades: pd.DataFrame,
    benchmark: Optional[pd.Series] = None,
    title: str = "Strategy Performance Summary",
    figsize: Tuple[int, int] = (12, 16)
) -> plt.Figure:
    """Create a summary dashboard with multiple subplots.
    
    Args:
        equity_curve: Series with equity curve data
        returns: Series with return data
        trades: DataFrame with trade information
        benchmark: Optional benchmark series for comparison
        title: Plot title
        figsize: Figure size (width, height)
        
    Returns:
        Matplotlib Figure object
    """
    # Create figure with subplots
    fig = plt.figure(figsize=figsize)
    gs = GridSpec(4, 2, height_ratios=[2, 1, 1, 1])
    
    # Plot 1: Equity Curve
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(equity_curve.index, equity_curve, label='Strategy', linewidth=2)
    if benchmark is not None:
        ax1.plot(benchmark.index, benchmark, label='Benchmark', linestyle='--', alpha=0.7)
    ax1.set_title('Equity Curve', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Drawdown
    ax2 = fig.add_subplot(gs[1, :])
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max * 100
    ax2.fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3)
    ax2.set_title('Drawdown (%)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Monthly Returns Heatmap
    ax3 = fig.add_subplot(gs[2, 0])
    returns_df = returns.to_frame('Returns')
    returns_df['Year'] = returns_df.index.year
    returns_df['Month'] = returns_df.index.month_name().str[:3]
    monthly_returns = returns_df.pivot_table(
        index='Year', 
        columns='Month', 
        values='Returns', 
        aggfunc=lambda x: (1 + x).prod() - 1
    ) * 100
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_returns = monthly_returns[month_order]
    sns.heatmap(monthly_returns, annot=True, fmt=".1f", cmap='RdYlGn', center=0, ax=ax3)
    ax3.set_title('Monthly Returns (%)', fontsize=12, fontweight='bold')
    
    # Plot 4: Returns Distribution
    ax4 = fig.add_subplot(gs[2, 1])
    sns.histplot(returns * 100, kde=True, bins=30, ax=ax4)
    mean = returns.mean() * 100
    median = returns.median() * 100
    ax4.axvline(mean, color='r', linestyle='--', label=f'Mean: {mean:.2f}%')
    ax4.axvline(median, color='g', linestyle='-', label=f'Median: {median:.2f}%')
    ax4.set_title('Daily Returns Distribution', fontsize=12, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Rolling Sharpe (6-month)
    ax5 = fig.add_subplot(gs[3, :])
    rolling_sharpe = returns.rolling(window=126).mean() / returns.rolling(window=126).std() * np.sqrt(252)
    ax5.plot(rolling_sharpe.index, rolling_sharpe)
    ax5.axhline(0, color='black', linestyle='-', alpha=0.3)
    ax5.set_title('6-Month Rolling Sharpe Ratio', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    # Adjust layout
    plt.suptitle(title, fontsize=16, fontweight='bold', y=0.99)
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    
    return fig
