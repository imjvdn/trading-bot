"""
Command Line Interface for the Hedge Fund Simulator.

This module provides a command-line interface for running backtests,
analyzing results, and managing trading strategies.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import yaml

from hedgefund_simulator import (
    MarketDataAgent,
    QuantAgent,
    RiskManagerAgent,
    PortfolioManagerAgent,
    BacktestEngine,
)
from hedgefund_simulator.utils import config_utils

# Set up logging
config_utils.setup_logging()
logger = logging.getLogger(__name__)

def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or use defaults.
    
    Args:
        config_file: Path to YAML config file
        
    Returns:
        Dictionary with configuration
    """
    # Default config (can be overridden by config file)
    config = {
        'market_data': {
            'tickers': ['SPY'],
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'interval': '1d',
            'indicators': ['sma', 'rsi', 'bbands', 'macd', 'atr']
        },
        'quant': {
            'strategy': 'moving_average_crossover',
            'fast_ma': 10,
            'slow_ma': 30,
            'rsi_overbought': 70,
            'rsi_oversold': 30
        },
        'risk': {
            'max_position_size': 0.2,
            'max_portfolio_risk': 0.02,
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.10
        },
        'portfolio': {
            'initial_cash': 100000,
            'max_positions': 5,
            'commission_pct': 0.001,
            'slippage_pct': 0.0005
        },
        'backtest': {
            'output_dir': 'backtest_results',
            'save_plots': True,
            'show_plots': False,
            'save_trades': True
        }
    }
    
    # Load from file if provided
    if config_file:
        try:
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                # Update default config with file config
                for key in file_config:
                    if key in config:
                        config[key].update(file_config[key])
                    else:
                        config[key] = file_config[key]
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}. Using defaults.")
    
    return config

def run_backtest(args):
    """Run a backtest with the given configuration."""
    logger.info("Starting backtest...")
    
    # Load config
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.tickers:
        config['market_data']['tickers'] = args.tickers
    if args.start_date:
        config['market_data']['start_date'] = args.start_date
    if args.end_date:
        config['market_data']['end_date'] = args.end_date
    if args.initial_cash:
        config['portfolio']['initial_cash'] = args.initial_cash
    if args.output_dir:
        config['backtest']['output_dir'] = args.output_dir
    
    # Initialize agents
    market_data_agent = MarketDataAgent(config['market_data'])
    quant_agent = QuantAgent(config['quant'])
    risk_manager = RiskManagerAgent(config['risk'])
    portfolio_manager = PortfolioManagerAgent(config['portfolio'])
    
    # Initialize and run backtest
    backtest_engine = BacktestEngine(
        market_data_agent=market_data_agent,
        quant_agent=quant_agent,
        risk_manager=risk_manager,
        portfolio_manager=portfolio_manager,
        config=config['backtest']
    )
    
    results = backtest_engine.run()
    
    # Print summary
    print("\n" + "="*80)
    print("BACKTEST SUMMARY")
    print("="*80)
    print(f"Period: {config['market_data']['start_date']} to {config['market_data']['end_date']}")
    print(f"Tickers: {', '.join(config['market_data']['tickers'])}")
    print(f"Initial Capital: ${config['portfolio']['initial_cash']:,.2f}")
    print(f"Final Portfolio Value: ${results['portfolio_value'][-1]:,.2f}")
    print(f"Total Return: {results['total_return']*100:.2f}%")
    print(f"Annualized Return: {results['annualized_return']*100:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']*100:.2f}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']*100:.1f}%")
    print("="*80)
    
    # Save results to CSV
    if args.save_results:
        output_dir = Path(config['backtest']['output_dir'])
        output_dir.mkdir(exist_ok=True)
        
        # Save portfolio values
        df_portfolio = pd.DataFrame({
            'date': results['dates'],
            'portfolio_value': results['portfolio_value'],
            'drawdown': results['drawdowns']
        })
        portfolio_file = output_dir / 'portfolio_values.csv'
        df_portfolio.to_csv(portfolio_file, index=False)
        logger.info(f"Portfolio values saved to {portfolio_file}")
        
        # Save trades if available
        if 'trades' in results and results['trades']:
            df_trades = pd.DataFrame(results['trades'])
            trades_file = output_dir / 'trades.csv'
            df_trades.to_csv(trades_file, index=False)
            logger.info(f"Trades saved to {trades_file}")
    
    return results

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description='AI Hedge Fund Simulator')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Backtest command
    parser_backtest = subparsers.add_parser('backtest', help='Run a backtest')
    parser_backtest.add_argument('-c', '--config', help='Path to config file (YAML)')
    parser_backtest.add_argument('-t', '--tickers', nargs='+', help='List of tickers to trade')
    parser_backtest.add_argument('-s', '--start-date', help='Start date (YYYY-MM-DD)')
    parser_backtest.add_argument('-e', '--end-date', help='End date (YYYY-MM-DD)')
    parser_backtest.add_argument('--initial-cash', type=float, help='Initial cash amount')
    parser_backtest.add_argument('-o', '--output-dir', help='Output directory for results')
    parser_backtest.add_argument('--save-results', action='store_true', 
                               help='Save results to CSV files')
    parser_backtest.set_defaults(func=run_backtest)
    
    # Parse arguments
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    
    # Execute the appropriate function
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
