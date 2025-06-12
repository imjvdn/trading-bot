"""
OpenAI integration utilities for the hedge fund simulator.

This module provides functions to interact with OpenAI's API for:
- Sentiment analysis of market news
- Natural language explanations of trades
- Strategy generation from natural language descriptions
"""

import os
import json
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime

# Import OpenAI (will be handled gracefully if not available)
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not available. Some features will be disabled.")

from .config_utils import get_openai_api_key, is_openai_enabled

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = None
if OPENAI_AVAILABLE and is_openai_enabled():
    api_key = get_openai_api_key()
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        logger.warning("OpenAI API key not found. OpenAI features will be disabled.")
        OPENAI_AVAILABLE = False

class OpenAIFeatureDisabledError(Exception):
    """Exception raised when trying to use OpenAI features that are disabled."""
    pass

def check_openai_available() -> bool:
    """Check if OpenAI features are available and enabled.
    
    Returns:
        bool: True if OpenAI features are available and enabled
    """
    if not OPENAI_AVAILABLE:
        return False
    if not is_openai_enabled():
        return False
    if client is None:
        return False
    return True

def analyze_sentiment(
    text: str, 
    model: str = "gpt-3.5-turbo",
    ticker: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze the sentiment of a piece of text (e.g., news article, tweet).
    
    Args:
        text: The text to analyze
        model: The OpenAI model to use
        ticker: Optional stock ticker for context
        
    Returns:
        Dictionary with sentiment analysis results
        
    Raises:
        OpenAIFeatureDisabledError: If OpenAI features are not available
    """
    if not check_openai_available():
        raise OpenAIFeatureDisabledError("OpenAI features are disabled or not configured")
    
    try:
        # Prepare the prompt
        prompt = f"""Analyze the sentiment of the following financial text. 
        {f'Focus on the impact on {ticker} stock. ' if ticker else ''}
        Consider both the tone (positive/negative/neutral) and the confidence level.
        Also identify any key themes or events mentioned that could affect the market.
        
        Text: {text}
        
        Respond with a JSON object containing:
        - sentiment: 'positive', 'negative', or 'neutral'
        - confidence: float between 0 and 1
        - themes: array of key themes or events mentioned
        - summary: a brief summary of the sentiment and key points
        """
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a financial analyst specializing in sentiment analysis of market news."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        content = response.choices[0].message.content
        result = json.loads(content)
        
        return {
            'success': True,
            'sentiment': result.get('sentiment', 'neutral'),
            'confidence': float(result.get('confidence', 0.5)),
            'themes': result.get('themes', []),
            'summary': result.get('summary', ''),
            'model': model,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

explain_trade_system_prompt = """You are an experienced financial analyst explaining trading decisions in clear, 
concise language. Your audience includes both professional traders and retail investors.

For each trade, provide:
1. A brief explanation of why the trade was made based on the provided signals
2. The key technical indicators or factors that influenced the decision
3. The risk-reward rationale
4. Any relevant market context

Keep explanations under 3 sentences and avoid financial jargon when possible.
"""

def explain_trade(
    ticker: str,
    action: str,
    price: float,
    quantity: int,
    indicators: Dict[str, Any],
    market_context: Optional[Dict[str, Any]] = None,
    model: str = "gpt-3.5-turbo"
) -> Dict[str, Any]:
    """Generate a natural language explanation for a trade.
    
    Args:
        ticker: Stock ticker symbol
        action: 'buy' or 'sell'
        price: Execution price
        quantity: Number of shares
        indicators: Dictionary of technical indicators and their values
        market_context: Optional dictionary with market context (e.g., VIX, sector performance)
        model: The OpenAI model to use
        
    Returns:
        Dictionary with the explanation and metadata
        
    Raises:
        OpenAIFeatureDisabledError: If OpenAI features are not available
    """
    if not check_openai_available():
        raise OpenAIFeatureDisabledError("OpenAI features are disabled or not configured")
    
    try:
        # Format the indicators for the prompt
        indicators_str = "\n".join([f"- {k}: {v}" for k, v in indicators.items()])
        
        # Add market context if available
        context_str = ""
        if market_context:
            context_str = "\nMarket context:\n" + "\n".join(
                [f"- {k}: {v}" for k, v in market_context.items()]
            )
        
        # Create the user message
        user_message = f"""Explain this {action.upper()} trade in simple terms:
        
        Ticker: {ticker}
        Action: {action.upper()}
        Price: ${price:.2f}
        Quantity: {quantity}
        
        Technical indicators:
        {indicators_str}
        {context_str}
        
        Provide a clear, concise explanation that would be helpful for a trader to understand the rationale.
        """
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": explain_trade_system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3
        )
        
        explanation = response.choices[0].message.content.strip()
        
        return {
            'success': True,
            'explanation': explanation,
            'ticker': ticker,
            'action': action,
            'price': price,
            'quantity': quantity,
            'model': model,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating trade explanation: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

generate_strategy_system_prompt = """You are an expert quantitative strategist with deep knowledge of algorithmic trading. 
Your task is to generate Python code for trading strategies based on natural language descriptions.

When generating code:
1. Use clear, well-documented Python code
2. Include all necessary imports
3. Implement the strategy as a class that follows the BaseStrategy pattern
4. Include parameter validation
5. Add type hints for better code clarity
6. Include example usage
7. Add comments explaining the strategy logic

Only respond with the Python code, no additional explanation or markdown formatting.
"""

def generate_strategy_code(
    description: str,
    model: str = "gpt-4"
) -> Dict[str, Any]:
    """Generate Python code for a trading strategy from a natural language description.
    
    Args:
        description: Natural language description of the strategy
        model: The OpenAI model to use
        
    Returns:
        Dictionary with the generated code and metadata
        
    Raises:
        OpenAIFeatureDisabledError: If OpenAI features are not available
    """
    if not check_openai_available():
        raise OpenAIFeatureDisabledError("OpenAI features are disabled or not configured")
    
    try:
        # Create the user message
        user_message = f"""Generate Python code for the following trading strategy:
        
        {description}
        
        Please provide a complete, well-documented Python class that implements this strategy.
        """
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": generate_strategy_system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,
            max_tokens=2000
        )
        
        code = response.choices[0].message.content.strip()
        
        # Clean up the response (remove markdown code blocks if present)
        if '```python' in code:
            code = code.split('```python')[1].split('```')[0]
        elif '```' in code:
            code = code.split('```')[1].split('```')[0]
        
        return {
            'success': True,
            'code': code,
            'model': model,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating strategy code: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
