"""
Agents package for the Hedge Fund Simulator.

This package contains the following agents:
- MarketDataAgent: Fetches and processes market data
- QuantAgent: Generates trading signals
- RiskManagerAgent: Manages risk and position sizing
- PortfolioManagerAgent: Manages portfolio and executes trades
"""

from .market_data_agent import MarketDataAgent
from .quant_agent import QuantAgent
from .risk_manager_agent import RiskManagerAgent
from .portfolio_manager_agent import PortfolioManagerAgent

__all__ = [
    'MarketDataAgent',
    'QuantAgent',
    'RiskManagerAgent',
    'PortfolioManagerAgent',
]
