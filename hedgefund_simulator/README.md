# AI Hedge Fund Simulator

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

A modular, Python-based AI hedge fund simulator for backtesting trading strategies on historical stock data. This project provides a comprehensive framework for developing, testing, and evaluating quantitative trading strategies with a focus on risk management and performance analysis.

## Features

- **Modular Architecture**: Clean separation of concerns with specialized agents for data handling, signal generation, risk management, and portfolio management.
- **Multiple Data Sources**: Built-in support for Yahoo Finance with extensible architecture for additional data providers.
- **Technical Indicators**: Comprehensive library of technical indicators for strategy development.
- **Risk Management**: Advanced position sizing, stop-loss, and portfolio risk controls.
- **Performance Metrics**: Detailed performance analytics including Sharpe ratio, drawdown analysis, and trade statistics.
- **AI Integration**: Optional OpenAI integration for sentiment analysis, trade explanations, and strategy generation.
- **Backtesting Engine**: Robust backtesting framework with realistic trade execution modeling.
- **Visualization**: Built-in plotting capabilities for strategy performance visualization.
- **Command Line Interface**: Easy-to-use CLI for running backtests and analyzing results.
- **Extensible**: Well-documented API for custom strategy development and extension.
- **Performance Metrics**: Comprehensive risk and performance analytics
- **Visualization**: Built-in plotting utilities for equity curves, drawdowns, and more
- **Extensible**: Easy to add new strategies, indicators, or data sources
- **Beginner-Friendly**: Well-documented code with example scripts

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/hedgefund-simulator.git
   cd hedgefund-simulator
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

1. Run the example script to see a simple moving average crossover strategy in action:
   ```bash
   python example.py
   ```

2. The script will:
   - Download historical data for AAPL (Jan 2024)
   - Run a backtest with the default strategy
   - Display performance metrics
   - Generate a plot of the equity curve and save it as `aapl_backtest_results.png`

## Project Structure

```
hedgefund_simulator/
├── agents/                     # Agent implementations
│   ├── __init__.py
│   ├── base_agent.py           # Base class for all agents
│   ├── market_data_agent.py    # Fetches and processes market data
│   ├── quant_agent.py          # Generates trading signals
│   ├── risk_manager_agent.py   # Manages risk and position sizing
│   └── portfolio_manager_agent.py  # Manages the portfolio and executes trades
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── data_utils.py           # Data processing and indicator calculations
│   ├── performance_metrics.py  # Risk and performance metrics
│   └── plotting.py             # Visualization utilities
├── backtest_engine.py          # Core backtesting functionality
├── config.py                   # Configuration settings
├── example.py                  # Example script
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Configuration

Modify `config.py` to adjust the simulation parameters:

- `MARKET_DATA_CONFIG`: Data source and date ranges
- `QUANT_CONFIG`: Strategy parameters (e.g., moving average periods)
- `RISK_CONFIG`: Risk management settings (position sizing, stop-loss, etc.)
- `PORTFOLIO_CONFIG`: Portfolio constraints and limits
- `BACKTEST_CONFIG`: Backtest parameters (initial capital, commissions, etc.)

## Creating a Custom Strategy

1. Create a new strategy class that inherits from `BaseAgent`:
   ```python
   from agents.base_agent import BaseAgent
   import pandas as pd

   class MyStrategy(BaseAgent):
       def __init__(self, config=None):
           super().__init__(config)
           # Initialize your strategy parameters
           self.param1 = self.config.get('param1', 10)
           self.param2 = self.config.get('param2', 30)
       
       def process(self, data):
           # Generate trading signals based on data
           # Return a dictionary with signal information
           signals = pd.Series(0, index=data.index)
           # Your strategy logic here
           return {'signals': signals}
   ```

2. Update the configuration in `config.py` to use your new strategy.

3. Run the backtest with your strategy.

## Performance Metrics

The simulator calculates various performance metrics, including:

- **Returns**: Total return, annualized return
- **Risk**: Volatility, maximum drawdown, Value at Risk (VaR)
- **Ratios**: Sharpe ratio, Sortino ratio, Calmar ratio
- **Trade Statistics**: Win rate, profit factor, average win/loss

## Example Output

```
================================================================================
BACKTEST SUMMARY - AAPL
Period: 2024-01-02 to 2024-01-31
--------------------------------------------------------------------------------
Initial Capital: $100,000.00
Final Portfolio Value: $102,345.67
Total Return: 2.35%
Annualized Return: 28.20%
Annualized Volatility: 15.75%
Sharpe Ratio: 1.79
Max Drawdown: -3.45%

--------------------------------------------------------------------------------
Benchmark Return: 1.89%
Alpha (vs. Benchmark): 0.46%

--------------------------------------------------------------------------------
Total Trades: 12
Win Rate: 58.3%
Average Win: $1,234.56
Average Loss: -$567.89
Profit Factor: 1.85
================================================================================
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Python and popular data science libraries (pandas, numpy, matplotlib, yfinance)
- Inspired by professional quantitative finance practices
- Special thanks to the open-source community for valuable tools and libraries
