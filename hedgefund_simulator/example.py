#!/usr/bin/env python3
"""
Hedge Fund Simulator - Example Script
------------------------------------
This script demonstrates how to use the hedge fund simulator to backtest
a simple moving average crossover strategy on AAPL stock.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Import the simulator components
from backtest_engine import BacktestEngine
from config import CONFIG

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backtest.log')
    ]
)
logger = logging.getLogger(__name__)

def run_backtest():
    """Run a backtest with the hedge fund simulator."""
    logger.info("Starting backtest...")
    
    try:
        # Initialize the backtest engine with configuration
        engine = BacktestEngine(CONFIG)
        
        # Run the backtest for AAPL
        ticker = "AAPL"
        initial_cash = 100000.0  # $100,000 initial capital
        
        logger.info(f"Running backtest for {ticker} from {CONFIG['market_data']['start_date']} to {CONFIG['market_data']['end_date']}")
        
        # Run the backtest
        results = engine.run_backtest(ticker, initial_cash)
        
        # Print summary
        engine.print_summary()
        
        # Plot results
        plot_file = f"{ticker.lower()}_backtest_results.png"
        engine.plot_results(plot_file)
        logger.info(f"Results plot saved to {plot_file}")
        
        # Show the plot (uncomment if running in a notebook)
        # plt.show()
        
        return results
        
    except Exception as e:
        logger.error(f"Error during backtest: {str(e)}", exc_info=True)
        raise

def analyze_results(results):
    """Analyze and print detailed results from the backtest."""
    if not results:
        print("No results to analyze.")
        return
    
    print("\n" + "="*80)
    print("DETAILED BACKTEST ANALYSIS")
    print("="*80)
    
    # Extract trade history
    trades = pd.DataFrame(results['trades'])
    
    if not trades.empty:
        # Calculate trade statistics
        winning_trades = trades[trades['realized_pnl'] > 0]
        losing_trades = trades[trades['realized_pnl'] < 0]
        
        print(f"\nTrade Statistics:")
        print(f"  - Total Trades: {len(trades)}")
        print(f"  - Winning Trades: {len(winning_trades)} ({len(winning_trades)/len(trades)*100:.1f}%)")
        print(f"  - Losing Trades: {len(losing_trades)} ({len(losing_trades)/len(trades)*100:.1f}%)")
        
        if not winning_trades.empty:
            print(f"\nWinning Trades:")
            print(f"  - Avg. Return: ${winning_trades['realized_pnl'].mean():.2f} per trade")
            print(f"  - Max Return: ${winning_trades['realized_pnl'].max():.2f}")
            print(f"  - Min Return: ${winning_trades['realized_pnl'].min():.2f}")
        
        if not losing_trades.empty:
            print(f"\nLosing Trades:")
            print(f"  - Avg. Loss: ${losing_trades['realized_pnl'].mean():.2f} per trade")
            print(f"  - Max Loss: ${losing_trades['realized_pnl'].min():.2f}")
            print(f"  - Min Loss: ${losing_trades['realized_pnl'].max():.2f}")
    
    # Extract equity curve
    equity_curve = pd.DataFrame(results['equity_curve'])
    
    if not equity_curve.empty:
        # Calculate drawdown
        equity_curve['peak'] = equity_curve['strategy'].cummax()
        equity_curve['drawdown'] = (equity_curve['strategy'] - equity_curve['peak']) / equity_curve['peak'] * 100
        
        print("\nEquity Curve Analysis:")
        print(f"  - Initial Capital: ${results['initial_capital']:,.2f}")
        print(f"  - Final Portfolio Value: ${results['final_portfolio_value']:,.2f}")
        print(f"  - Total Return: {results['total_return_pct']:,.2f}%")
        print(f"  - Annualized Return: {results['annualized_return_pct']:,.2f}%")
        print(f"  - Max Drawdown: {equity_curve['drawdown'].min():.2f}%")
        print(f"  - Volatility: {results['annualized_volatility_pct']:.2f}%")
        print(f"  - Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    
    print("\n" + "="*80 + "\n")

def main():
    """Main function to run the example."""
    print("="*80)
    print("HEDGE FUND SIMULATOR - EXAMPLE BACKTEST")
    print("="*80)
    print(f"Strategy: Moving Average Crossover (5/20)")
    print(f"Asset: AAPL")
    print(f"Date Range: {CONFIG['market_data']['start_date']} to {CONFIG['market_data']['end_date']}")
    print("="*80 + "\n")
    
    # Run the backtest
    results = run_backtest()
    
    # Analyze results
    if results:
        analyze_results(results)
    
    print("Backtest completed successfully!")

if __name__ == "__main__":
    main()
