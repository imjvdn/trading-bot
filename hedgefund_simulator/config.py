# Configuration for the Hedge Fund Simulator

# Market Data Configuration
MARKET_DATA_CONFIG = {
    'start_date': '2023-01-01',  # Start date for backtest (YYYY-MM-DD)
    'end_date': '2023-12-31',    # End date for backtest (YYYY-MM-DD)
    'interval': '1d',            # Data interval ('1d', '1h', etc.)
}

# Quant Agent Configuration
QUANT_CONFIG = {
    'fast_ma': 5,               # Fast moving average period
    'slow_ma': 20,              # Slow moving average period
    'rsi_overbought': 70,       # RSI overbought threshold
    'rsi_oversold': 30,         # RSI oversold threshold
}

# Risk Manager Configuration
RISK_CONFIG = {
    'max_position_size': 0.1,   # Maximum position size as percentage of portfolio
    'stop_loss_pct': 0.05,      # Stop loss percentage
    'take_profit_pct': 0.1,     # Take profit percentage
    'max_portfolio_risk': 0.02, # Maximum risk per trade as percentage of portfolio
}

# Portfolio Manager Configuration
PORTFOLIO_CONFIG = {
    'max_open_positions': 5,    # Maximum number of simultaneous positions
    'max_sector_exposure': 0.3, # Maximum exposure to any single sector
    'max_asset_exposure': 0.2,  # Maximum exposure to any single asset
}

# Backtest Configuration
BACKTEST_CONFIG = {
    'initial_cash': 100000.0,   # Initial cash amount
    'commission': 0.001,        # Commission per trade (percentage of trade value)
    'slippage': 0.0005,        # Slippage per trade (percentage of trade value)
}

# OpenAI Configuration (Optional)
OPENAI_CONFIG = {
    'enabled': False,           # Set to True to enable OpenAI integration
    'api_key': None,            # Will be loaded from environment variable
    'model': 'gpt-3.5-turbo',   # Model to use for analysis
    'max_tokens': 150,          # Maximum tokens for responses
}

# Combine all configurations
CONFIG = {
    'market_data': MARKET_DATA_CONFIG,
    'quant': QUANT_CONFIG,
    'risk': RISK_CONFIG,
    'portfolio': PORTFOLIO_CONFIG,
    'backtest': BACKTEST_CONFIG,
    'openai': OPENAI_CONFIG,
}
