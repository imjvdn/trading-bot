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
from hedgefund_simulator.backtest_engine import BacktestEngine
from hedgefund_simulator.config import CONFIG

def main():
    """Main function to run the hedge fund simulator example."""
    try:
        # Print clean header
        print("\n" + "="*60)
        print("AI HEDGE FUND SIMULATOR")
        print("="*60)
        print(f"Strategy: Moving Average Crossover (5/20)")
        print(f"Asset: AAPL")
        print(f"Period: {CONFIG['market_data']['start_date']} to {CONFIG['market_data']['end_date']}")
        print("="*60)
        
        # Initialize the backtest engine
        engine = BacktestEngine(CONFIG)
        
        # Set up the ticker and initial capital
        ticker = "AAPL"
        initial_cash = 100000.0  # $100,000 initial capital
        
        # Run the backtest
        results = engine.run_backtest(ticker, initial_cash)
        
        # Print summary
        engine.print_summary()
        
        # Plot results
        plot_file = f"{ticker.lower()}_backtest_results.png"
        engine.plot_results(plot_file)
        print(f"\nResults plot saved to {plot_file}")
        
        return results
        
    except Exception as e:
        print(f"Error during backtest: {str(e)}")
        raise

def analyze_results(results):
    """Analyze and print detailed results from the backtest."""
    if not results:
        print("No results to analyze.")
        return
    
    print("\n" + "="*60)
    print("BACKTEST ANALYSIS")
    print("="*60)
    
    try:
        # Extract trade history if available
        if 'trades' not in results or not results['trades']:
            print("No trade history available for analysis.")
            return
            
        trades = pd.DataFrame(results['trades'])
        
        if not trades.empty:
            # Check if we have PnL information
            pnl_column = None
            for col in ['realized_pnl', 'pnl', 'profit_loss']:
                if col in trades.columns:
                    pnl_column = col
                    break
            
            if pnl_column is None:
                print("No PnL information available in trade history.")
                return
                
            # Calculate trade statistics
            winning_trades = trades[trades[pnl_column] > 0]
            losing_trades = trades[trades[pnl_column] < 0]
            
            print(f"Trade Statistics:")
            print(f"  Total Trades: {len(trades)}")
            
            if len(trades) > 0:
                win_rate = len(winning_trades)/len(trades)*100
                print(f"  Winning Trades: {len(winning_trades)} ({win_rate:.1f}%)")
                print(f"  Losing Trades: {len(losing_trades)} ({100-win_rate:.1f}%)")
                
                if not winning_trades.empty:
                    print(f"\nWinning Trades:")
                    print(f"  Average Return: ${winning_trades[pnl_column].mean():.2f}")
                    print(f"  Best Trade: ${winning_trades[pnl_column].max():.2f}")
                
                if not losing_trades.empty:
                    print(f"\nLosing Trades:")
                    print(f"  Average Loss: ${losing_trades[pnl_column].mean():.2f}")
                    print(f"  Worst Trade: ${losing_trades[pnl_column].min():.2f}")
            
            # Show first few trades in a clean format
            print(f"\nFirst 5 Trades:")
            print("-" * 60)
            for i, trade in trades.head().iterrows():
                date = pd.to_datetime(trade['timestamp']).strftime('%Y-%m-%d')
                action = trade['action'].upper()
                qty = int(trade['quantity'])
                price = float(trade['price'])
                print(f"  {date} | {action:6} | {qty:3d} shares @ ${price:6.2f}")
        
        # Equity curve analysis
        if 'equity_curve' in results and results['equity_curve']:
            equity_data = results['equity_curve']
            if isinstance(equity_data, list) and len(equity_data) > 0:
                initial_value = equity_data[0] if equity_data else 100000
                final_value = equity_data[-1] if equity_data else 100000
                
                print(f"\nPortfolio Performance:")
                print(f"  Initial Capital: ${initial_value:,.2f}")
                print(f"  Final Value: ${final_value:,.2f}")
                
                if initial_value > 0:
                    total_return = (final_value - initial_value) / initial_value * 100
                    print(f"  Total Return: {total_return:.2f}%")
                
    except Exception as e:
        print(f"Error analyzing results: {str(e)}")
    
    print("="*60)

if __name__ == "__main__":
    results = main()
    if results:
        analyze_results(results)
    print("Backtest completed successfully!")
