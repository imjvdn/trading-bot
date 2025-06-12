"""
Comprehensive test suite for the Hedge Fund Simulator.

This module contains unit tests and integration tests for the
Hedge Fund Simulator components.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from hedgefund_simulator.agents.market_data_agent import MarketDataAgent
from hedgefund_simulator.agents.quant_agent import QuantAgent
from hedgefund_simulator.agents.risk_manager_agent import RiskManagerAgent
from hedgefund_simulator.agents.portfolio_manager_agent import PortfolioManagerAgent
from hedgefund_simulator.backtest_engine import BacktestEngine
from hedgefund_simulator.utils import data_utils, performance_metrics, plotting

class TestMarketDataAgent(unittest.TestCase):
    """Test cases for the MarketDataAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'tickers': ['AAPL'],
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'interval': '1d',
            'indicators': ['sma', 'rsi', 'bbands']
        }
        self.agent = MarketDataAgent(self.config)
    
    def test_fetch_data(self):
        """Test fetching market data."""
        data = self.agent.fetch_data()
        self.assertIsInstance(data, dict)
        self.assertIn('AAPL', data)
        self.assertGreater(len(data['AAPL']), 0)
        
        # Check if required columns are present
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            self.assertIn(col, data['AAPL'].columns)
    
    def test_add_indicators(self):
        """Test adding technical indicators."""
        # Create sample data
        dates = pd.date_range(start='2023-01-01', periods=100)
        prices = pd.Series(np.random.normal(100, 5, 100).cumsum(), index=dates)
        df = pd.DataFrame({
            'open': prices * 0.99,
            'high': prices * 1.01,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, 100)
        })
        
        # Add indicators
        df_with_indicators = self.agent.add_indicators(df, ['sma', 'rsi', 'bbands'])
        
        # Check if indicators were added
        self.assertIn('sma_20', df_with_indicators.columns)
        self.assertIn('rsi_14', df_with_indicators.columns)
        self.assertIn('bb_upper', df_with_indicators.columns)
        self.assertIn('bb_middle', df_with_indicators.columns)
        self.assertIn('bb_lower', df_with_indicators.columns)


class TestQuantAgent(unittest.TestCase):
    """Test cases for the QuantAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'strategy': 'moving_average_crossover',
            'fast_ma': 10,
            'slow_ma': 30,
            'rsi_overbought': 70,
            'rsi_oversold': 30
        }
        self.agent = QuantAgent(self.config)
        
        # Create sample data
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=100)
        close_prices = np.cumsum(np.random.randn(100)) + 100
        
        self.sample_data = pd.DataFrame({
            'close': close_prices,
            'sma_10': close_prices.rolling(10).mean(),
            'sma_30': close_prices.rolling(30).mean(),
            'rsi_14': np.random.uniform(0, 100, 100),
            'bb_upper': close_prices * 1.05,
            'bb_middle': close_prices,
            'bb_lower': close_prices * 0.95
        }, index=dates)
    
    def test_generate_signals(self):
        """Test signal generation."""
        signals = self.agent.generate_signals(self.sample_data)
        
        # Check if signals are generated
        self.assertIn('signal', signals.columns)
        self.assertIn('strength', signals.columns)
        self.assertIn('timestamp', signals.columns)
        
        # Check signal values
        self.assertTrue(all(signals['signal'].isin([-1, 0, 1, None])))
    
    def test_moving_average_crossover(self):
        """Test moving average crossover strategy."""
        # Create a clear crossover scenario
        df = pd.DataFrame({
            'close': [10]*10 + [20]*10,  # Price jumps from 10 to 20
            'sma_10': [10]*10 + [20]*10,  # Fast MA follows price
            'sma_30': [10]*20,            # Slow MA stays at 10
            'rsi_14': [50]*20             # Neutral RSI
        })
        
        signals = self.agent.moving_average_crossover(df)
        
        # Should be buy signal at crossover
        self.assertEqual(signals['signal'].iloc[10], 1)
        self.assertGreater(signals['strength'].iloc[10], 0)


class TestRiskManagerAgent(unittest.TestCase):
    """Test cases for the RiskManagerAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'max_position_size': 0.2,
            'max_portfolio_risk': 0.02,
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.10,
            'use_volatility_scaling': True,
            'volatility_lookback': 21,
            'target_volatility': 0.20
        }
        self.agent = RiskManagerAgent(self.config)
        
        # Sample price data
        np.random.seed(42)
        self.prices = pd.Series(np.random.normal(100, 5, 100).cumsum() + 1000)
    
    def test_calculate_position_size(self):
        """Test position size calculation."""
        # Test with different account sizes and risk parameters
        test_cases = [
            (100000, 100, 0.02, 50),  # 2% risk, $1000 risk, $50 stop -> 20 shares
            (50000, 50, 0.01, 10),    # 1% risk, $500 risk, $10 stop -> 50 shares
            (10000, 200, 0.05, 20)    # 5% risk, $500 risk, $20 stop -> 25 shares
        ]
        
        for account_size, price, risk_pct, stop_loss in test_cases:
            position_size = self.agent.calculate_position_size(
                account_size=account_size,
                entry_price=price,
                stop_loss_price=price * (1 - stop_loss/100) if stop_loss else None,
                risk_pct=risk_pct
            )
            
            # Calculate expected position size
            if stop_loss:
                risk_per_share = price * (stop_loss / 100)
                expected_size = int((account_size * risk_pct) / risk_per_share)
            else:
                expected_size = int((account_size * risk_pct) / (price * 0.01))
            
            self.assertEqual(position_size, expected_size)
    
    def test_stop_loss_take_profit(self):
        """Test stop loss and take profit calculation."""
        entry_price = 100
        
        # Test stop loss
        stop_loss = self.agent.calculate_stop_loss(entry_price)
        self.assertAlmostEqual(stop_loss, entry_price * (1 - self.config['stop_loss_pct']))
        
        # Test take profit
        take_profit = self.agent.calculate_take_profit(entry_price)
        self.assertAlmostEqual(take_profit, entry_price * (1 + self.config['take_profit_pct']))


class TestPortfolioManagerAgent(unittest.TestCase):
    """Test cases for the PortfolioManagerAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'initial_cash': 100000,
            'max_positions': 5,
            'commission_pct': 0.001,
            'slippage_pct': 0.0005,
            'min_position_size': 1000  # Minimum position size in USD
        }
        self.agent = PortfolioManagerAgent(self.config)
        
        # Sample price data
        self.timestamp = datetime(2023, 1, 1)
        self.price = 100.0
    
    def test_initial_state(self):
        """Test initial portfolio state."""
        self.assertEqual(self.agent.cash, self.config['initial_cash'])
        self.assertEqual(len(self.agent.positions), 0)
        self.assertEqual(len(self.agent.trade_history), 0)
    
    def test_buy_sell_cycle(self):
        """Test a complete buy and sell cycle."""
        ticker = 'AAPL'
        quantity = 100
        
        # Buy
        trade = self.agent.execute_trade(
            ticker=ticker,
            action='buy',
            quantity=quantity,
            price=self.price,
            timestamp=self.timestamp,
            reason='Test buy'
        )
        
        # Check trade execution
        self.assertEqual(trade['status'], 'success')
        self.assertEqual(trade['action'], 'buy')
        self.assertEqual(trade['quantity'], quantity)
        self.assertEqual(trade['price'], self.price)
        
        # Check portfolio state after buy
        self.assertIn(ticker, self.agent.positions)
        self.assertEqual(self.agent.positions[ticker]['quantity'], quantity)
        self.assertEqual(self.agent.positions[ticker]['cost_basis'], self.price)
        
        # Update price for sell
        new_price = self.price * 1.1  # 10% gain
        
        # Sell
        trade = self.agent.execute_trade(
            ticker=ticker,
            action='sell',
            quantity=quantity,
            price=new_price,
            timestamp=self.timestamp + timedelta(days=1),
            reason='Test sell'
        )
        
        # Check trade execution
        self.assertEqual(trade['status'], 'success')
        self.assertEqual(trade['action'], 'sell')
        self.assertEqual(trade['quantity'], quantity)
        self.assertEqual(trade['price'], new_price)
        
        # Check portfolio state after sell
        self.assertNotIn(ticker, self.agent.positions)  # Position should be closed
        
        # Check P&L
        self.assertGreater(self.agent.cash, self.config['initial_cash'])  # Should have made money
    
    def test_insufficient_funds(self):
        """Test trade with insufficient funds."""
        # Try to buy more than we can afford
        ticker = 'AAPL'
        quantity = int((self.config['initial_cash'] * 1.1) / self.price)  # 110% of portfolio
        
        trade = self.agent.execute_trade(
            ticker=ticker,
            action='buy',
            quantity=quantity,
            price=self.price,
            timestamp=self.timestamp,
            reason='Test insufficient funds'
        )
        
        # Should fail due to insufficient funds
        self.assertEqual(trade['status'], 'error')


class TestBacktestEngine(unittest.TestCase):
    """Test cases for the BacktestEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock agents
        class MockMarketDataAgent:
            def fetch_data(self):
                # Create sample price data
                dates = pd.date_range(start='2023-01-01', periods=100)
                close_prices = np.cumsum(np.random.randn(100)) + 100
                
                return {
                    'AAPL': pd.DataFrame({
                        'open': close_prices * 0.99,
                        'high': close_prices * 1.01,
                        'low': close_prices * 0.98,
                        'close': close_prices,
                        'volume': np.random.randint(1000000, 5000000, 100),
                        'sma_10': close_prices.rolling(10).mean(),
                        'sma_30': close_prices.rolling(30).mean(),
                        'rsi_14': np.random.uniform(30, 70, 100)
                    }, index=dates)
                }
        
        class MockQuantAgent:
            def generate_signals(self, data):
                # Generate random signals
                signals = pd.DataFrame(index=data.index)
                signals['signal'] = np.random.choice([-1, 0, 1], size=len(data), p=[0.2, 0.6, 0.2])
                signals['strength'] = np.random.uniform(0.5, 1.0, len(data))
                signals['timestamp'] = data.index
                return signals
        
        class MockRiskManagerAgent:
            def calculate_position_size(self, *args, **kwargs):
                return 100  # Fixed position size for testing
            
            def calculate_stop_loss(self, price):
                return price * 0.95
            
            def calculate_take_profit(self, price):
                return price * 1.10
        
        self.market_data_agent = MockMarketDataAgent()
        self.quant_agent = MockQuantAgent()
        self.risk_manager = MockRiskManagerAgent()
        self.portfolio_manager = PortfolioManagerAgent({
            'initial_cash': 100000,
            'max_positions': 5,
            'commission_pct': 0.001,
            'slippage_pct': 0.0005
        })
        
        self.backtest_config = {
            'output_dir': 'test_results',
            'save_plots': False,
            'show_plots': False,
            'save_trades': True
        }
    
    def test_run_backtest(self):
        """Test running a complete backtest."""
        engine = BacktestEngine(
            market_data_agent=self.market_data_agent,
            quant_agent=self.quant_agent,
            risk_manager=self.risk_manager,
            portfolio_manager=self.portfolio_manager,
            config=self.backtest_config
        )
        
        # Run backtest
        results = engine.run()
        
        # Check results
        self.assertIn('portfolio_value', results)
        self.assertIn('returns', results)
        self.assertIn('drawdowns', results)
        self.assertIn('trades', results)
        
        # Portfolio value should be a list of numbers
        self.assertIsInstance(results['portfolio_value'], list)
        self.assertGreater(len(results['portfolio_value']), 0)
        
        # Returns should be one less than portfolio values (daily returns)
        self.assertEqual(len(results['returns']), len(results['portfolio_value']) - 1)
        
        # Check if trades were executed
        self.assertGreater(len(results['trades']), 0)
        
        # Check performance metrics
        self.assertIn('total_return', results)
        self.assertIn('annualized_return', results)
        self.assertIn('sharpe_ratio', results)
        self.assertIn('max_drawdown', results)
        self.assertIn('win_rate', results)


class TestPerformanceMetrics(unittest.TestCase):
    """Test cases for performance metrics calculations."""
    
    def test_calculate_returns(self):
        """Test return calculations."""
        # Create sample price data
        prices = pd.Series([100, 101, 102.01, 100.98, 101.99])
        
        # Calculate returns
        returns = performance_metrics.calculate_returns(prices)
        
        # Check calculations
        expected_returns = pd.Series([np.nan, 0.01, 0.01, -0.0101, 0.01])
        pd.testing.assert_series_equal(
            returns.round(4),
            expected_returns.round(4),
            check_names=False
        )
    
    def test_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        # Create sample returns (5% annual return, 10% annual volatility)
        np.random.seed(42)
        daily_returns = np.random.normal(0.0002, 0.0063, 252)  # ~5% annual return, 10% vol
        
        # Calculate Sharpe ratio (risk-free rate = 0 for simplicity)
        sharpe = performance_metrics.sharpe_ratio(daily_returns, risk_free_rate=0.0, periods=252)
        
        # Should be approximately 0.5 (5% return / 10% vol)
        self.assertAlmostEqual(sharpe, 0.5, delta=0.1)
    
    def test_max_drawdown(self):
        """Test maximum drawdown calculation."""
        # Create sample equity curve with a drawdown
        equity_curve = pd.Series([100, 110, 105, 120, 90, 95, 100])
        
        # Calculate max drawdown
        mdd = performance_metrics.max_drawdown(equity_curve)
        
        # Expected drawdown: (120 - 90) / 120 = 0.25 or 25%
        self.assertAlmostEqual(mdd, 0.25)


class TestDataUtils(unittest.TestCase):
    """Test cases for data utility functions."""
    
    def test_sma(self):
        """Test simple moving average calculation."""
        # Create sample data
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        
        # Calculate SMA with window 3
        sma = data_utils.sma(data, window=3)
        
        # Check calculations
        expected = pd.Series([np.nan, np.nan, 2, 3, 4, 5, 6, 7, 8, 9])
        pd.testing.assert_series_equal(sma, expected)
    
    def test_rsi(self):
        """Test RSI calculation."""
        # Create sample data with known RSI values
        prices = pd.Series([44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 
                          45.10, 45.42, 45.84, 46.08, 45.89, 46.03])
        
        # Calculate RSI with period 6 (standard for this test case)
        rsi = data_utils.rsi(prices, period=6)
        
        # Known RSI value for this data (from standard RSI calculation)
        expected_rsi = 70.53
        
        # Check if calculated RSI is close to expected (allowing for small rounding differences)
        self.assertAlmostEqual(rsi.iloc[-1], expected_rsi, delta=0.1)


if __name__ == '__main__':
    # Create test directory if it doesn't exist
    os.makedirs('test_results', exist_ok=True)
    
    # Run tests
    unittest.main()
