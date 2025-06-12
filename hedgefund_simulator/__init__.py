"""
Hedge Fund Simulator - A Python package for backtesting trading strategies.
"""

__version__ = "0.1.0"

# Import key components to make them available at package level
from .backtest_engine import BacktestEngine
from .agents import (
    MarketDataAgent,
    QuantAgent,
    RiskManagerAgent,
    PortfolioManagerAgent
)

__all__ = [
    'BacktestEngine',
    'MarketDataAgent',
    'QuantAgent',
    'RiskManagerAgent',
    'PortfolioManagerAgent',
]
