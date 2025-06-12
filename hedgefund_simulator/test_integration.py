"""
Integration test for the AI Hedge Fund Simulator.

This script tests the end-to-end functionality of the simulator,
including data loading, signal generation, risk management,
portfolio management, and backtesting.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hedgefund_simulator.agents.market_data_agent import MarketDataAgent
from hedgefund_simulator.agents.quant_agent import QuantAgent
from hedgefund_simulator.agents.risk_manager_agent import RiskManagerAgent
from hedgefund_simulator.agents.portfolio_manager_agent import PortfolioManagerAgent
from hedgefund_simulator.backtest_engine import BacktestEngine
from hedgefund_simulator.config import (
    MARKET_DATA_CONFIG, 
    QUANT_CONFIG, 
    RISK_CONFIG, 
    PORTFOLIO_CONFIG, 
    BACKTEST_CONFIG
)
from hedgefund_simulator.utils import config_utils

# Set up logging
config_utils.setup_logging(logging.INFO)
logger = logging.getLogger(__name__)

def run_integration_test():
    """Run an integration test of the hedge fund simulator."""
    logger.info("Starting integration test...")
    
    # Override config for testing
    test_config = {
        'market_data': {
            **MARKET_DATA_CONFIG,
            'tickers': ['AAPL', 'MSFT'],  # Test with two tickers
            'start_date': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'interval': '1d',
            'indicators': ['sma', 'rsi', 'bbands', 'macd', 'atr']
        },
        'quant': {
            **QUANT_CONFIG,
            'strategy': 'moving_average_crossover',
            'fast_ma': 10,
            'slow_ma': 30,
            'rsi_overbought': 70,
            'rsi_oversold': 30
        },
        'risk': {
            **RISK_CONFIG,
            'max_position_size': 0.2,  # 20% of portfolio per position
            'max_portfolio_risk': 0.02,  # 2% risk per trade
            'stop_loss_pct': 0.05,  # 5% stop loss
            'take_profit_pct': 0.10  # 10% take profit
        },
        'portfolio': {
            **PORTFOLIO_CONFIG,
            'initial_cash': 100000,  # $100,000 starting capital
            'max_positions': 5,  # Max 5 open positions
            'commission_pct': 0.001,  # 0.1% commission
            'slippage_pct': 0.0005  # 0.05% slippage
        },
        'backtest': {
            **BACKTEST_CONFIG,
            'output_dir': 'backtest_results',
            'save_plots': True,
            'show_plots': False,
            'save_trades': True
        }
    }
    
    # Initialize agents
    logger.info("Initializing agents...")
    market_data_agent = MarketDataAgent(test_config['market_data'])
    quant_agent = QuantAgent(test_config['quant'])
    risk_manager = RiskManagerAgent(test_config['risk'])
    portfolio_manager = PortfolioManagerAgent(test_config['portfolio'])
    
    # Initialize backtest engine
    backtest_engine = BacktestEngine(
        market_data_agent=market_data_agent,
        quant_agent=quant_agent,
        risk_manager=risk_manager,
        portfolio_manager=portfolio_manager,
        config=test_config['backtest']
    )
    
    # Run backtest
    logger.info("Running backtest...")
    results = backtest_engine.run()
    
    # Print summary
    print("\n" + "="*80)
    print("BACKTEST SUMMARY")
    print("="*80)
    print(f"Period: {test_config['market_data']['start_date']} to {test_config['market_data']['end_date']}")
    print(f"Initial Capital: ${test_config['portfolio']['initial_cash']:,.2f}")
    print(f"Final Portfolio Value: ${results['portfolio_value'][-1]:,.2f}")
    print(f"Total Return: {results['total_return']*100:.2f}%")
    print(f"Annualized Return: {results['annualized_return']*100:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']*100:.2f}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']*100:.1f}%")
    print("="*80 + "\n")
    
    # Save results
    os.makedirs('backtest_results', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"backtest_results/integration_test_{timestamp}.png"
    
    # Plot results
    plt.figure(figsize=(12, 8))
    
    # Plot equity curve
    plt.subplot(2, 1, 1)
    plt.plot(results['dates'], results['portfolio_value'], label='Portfolio Value')
    plt.title('Portfolio Value Over Time')
    plt.xlabel('Date')
    plt.ylabel('Value ($)')
    plt.grid(True)
    plt.legend()
    
    # Plot drawdown
    plt.subplot(2, 1, 2)
    plt.fill_between(results['dates'], results['drawdowns'] * 100, 0, 
                    color='red', alpha=0.3, label='Drawdown')
    plt.title('Drawdown')
    plt.xlabel('Date')
    plt.ylabel('Drawdown (%)')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(results_file)
    logger.info(f"Results saved to {results_file}")
    
    return results

if __name__ == "__main__":
    results = run_integration_test()
