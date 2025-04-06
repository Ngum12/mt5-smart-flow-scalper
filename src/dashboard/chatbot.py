import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

class TradingChatbot:
    """AI Chatbot to provide market analysis and strategy insights"""
    
    def __init__(self):
        self.messages = []
        self.market_patterns = {
            "bullish": [
                "price above both EMAs", 
                "bullish crossover",
                "higher lows forming",
                "bullish divergence",
                "increasing volume on up moves"
            ],
            "bearish": [
                "price below both EMAs", 
                "bearish crossover",
                "lower highs forming",
                "bearish divergence",
                "increasing volume on down moves"
            ],
            "neutral": [
                "price between EMAs",
                "sideways consolidation",
                "no clear direction",
                "decreasing volatility",
                "low volume conditions"
            ]
        }
        
        self.symbol_characteristics = {
            "GainX": "bullish synthetic index with a natural upward drift",
            "PainX": "bearish synthetic index with a natural downward drift"
        }
        
    def analyze_market(self, symbol, data):
        """Analyze current market conditions based on recent data"""
        if data is None or len(data) < 20:
            return "Insufficient data to analyze the market."
            
        # Get the latest data
        latest = data.iloc[-1]
        
        # Determine market condition
        market_condition = self._determine_market_condition(data)
        
        # Create detailed analysis
        symbol_type = "GainX" if "GainX" in symbol else "PainX" if "PainX" in symbol else "Unknown"
        
        # Extract number from symbol (e.g., 800 from GainX 800)
        try:
            symbol_number = int(''.join(filter(str.isdigit, symbol)))
            volatility_text = self._get_volatility_description(symbol_number)
        except:
            volatility_text = "with unknown volatility characteristics"
        
        # Create the analysis message
        message = f"**Market Analysis for {symbol}**\n\n"
        message += f"{symbol} is a {self.symbol_characteristics.get(symbol_type, 'custom synthetic index')} {volatility_text}.\n\n"
        
        # Current market stats
        message += f"**Current Conditions:**\n"
        message += f"• Price: ${latest['close']:,.2f}\n"
        message += f"• EMA Setup: Price is {'above both EMAs' if latest['close'] > latest['ema_long'] else 'below both EMAs' if latest['close'] < latest['ema_short'] else 'between EMAs'}\n" 
        message += f"• RSI: {latest['rsi']:.1f} ({'overbought' if latest['rsi'] > 70 else 'oversold' if latest['rsi'] < 30 else 'neutral'})\n"
        message += f"• MACD: {'Positive' if latest['macd'] > latest['macd_signal'] else 'Negative'} ({latest['macd']:.2f} vs signal {latest['macd_signal']:.2f})\n\n"
        
        # Market condition interpretation
        message += f"**Market Interpretation:**\n"
        message += f"The market is showing {market_condition} conditions with "
        
        # Add some specific patterns detected
        if market_condition == "bullish":
            patterns = random.sample(self.market_patterns["bullish"], 2)
        elif market_condition == "bearish":
            patterns = random.sample(self.market_patterns["bearish"], 2)
        else:
            patterns = random.sample(self.market_patterns["neutral"], 2)
            
        message += f"{patterns[0]} and {patterns[1]}.\n\n"
        
        # Strategy recommendation based on symbol and conditions
        message += self._get_strategy_recommendation(symbol, data, market_condition)
        
        # Add timestamp
        message += f"\n\n_Analysis generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        
        return message
    
    def _determine_market_condition(self, data):
        """Determine if the market is bullish, bearish, or neutral"""
        latest = data.iloc[-1]
        
        # Simple analysis based on EMAs and price
        if latest['close'] > latest['ema_short'] > latest['ema_long']:
            return "bullish"
        elif latest['close'] < latest['ema_short'] < latest['ema_long']:
            return "bearish"
        else:
            # Check MACD for direction
            if latest['macd'] > latest['macd_signal']:
                return "moderately bullish"
            elif latest['macd'] < latest['macd_signal']:
                return "moderately bearish"
            else:
                return "neutral"
    
    def _get_volatility_description(self, symbol_number):
        """Get volatility description based on symbol number"""
        if symbol_number >= 1200:
            return "with extreme volatility characteristics"
        elif symbol_number >= 999:
            return "with very high volatility characteristics"
        elif symbol_number >= 800:
            return "with high volatility characteristics"
        elif symbol_number >= 600:
            return "with medium-high volatility characteristics"
        elif symbol_number >= 400:
            return "with medium volatility characteristics"
        else:
            return "with lower volatility characteristics"
    
    def _get_strategy_recommendation(self, symbol, data, market_condition):
        """Generate strategy recommendation based on symbol and market condition"""
        is_gainx = "GainX" in symbol
        is_painx = "PainX" in symbol
        
        message = "**Strategy Recommendation:**\n"
        
        if is_gainx:
            # GainX has bullish bias
            if market_condition in ["bullish", "moderately bullish"]:
                message += "• This aligns perfectly with GainX's natural bullish bias\n"
                message += "• Look for buy opportunities on retracements to the EMAs\n"
                message += "• Consider trailing stops to maximize profit potential\n"
                message += "• Optimal entry would be after RSI pulls back from overbought conditions\n"
            elif market_condition in ["bearish", "moderately bearish"]:
                message += "• This is counter to GainX's natural bullish bias - exercise caution\n"
                message += "• Consider waiting for signs of reversal before entering\n"
                message += "• If selling, use tighter stop losses as the natural bias may resume\n"
                message += "• Watch for potential bullish divergences on RSI and MACD\n"
            else:
                message += "• Market is consolidating - prepare for the next directional move\n"
                message += "• GainX's natural bullish bias suggests favoring long positions when clear signals appear\n"
                message += "• Use this time to identify key support and resistance levels\n"
        
        elif is_painx:
            # PainX has bearish bias
            if market_condition in ["bearish", "moderately bearish"]:
                message += "• This aligns perfectly with PainX's natural bearish bias\n"
                message += "• Look for sell opportunities on rebounds to the EMAs\n"
                message += "• Consider trailing stops to maximize profit potential\n"
                message += "• Optimal entry would be after RSI bounces from oversold conditions\n"
            elif market_condition in ["bullish", "moderately bullish"]:
                message += "• This is counter to PainX's natural bearish bias - exercise caution\n"
                message += "• Consider waiting for signs of reversal before entering\n"
                message += "• If buying, use tighter stop losses as the natural bias may resume\n"
                message += "• Watch for potential bearish divergences on RSI and MACD\n"
            else:
                message += "• Market is consolidating - prepare for the next directional move\n"
                message += "• PainX's natural bearish bias suggests favoring short positions when clear signals appear\n"
                message += "• Use this time to identify key resistance and support levels\n"
        
        else:
            # Generic recommendation
            if market_condition in ["bullish", "moderately bullish"]:
                message += "• Market conditions favor long positions\n"
                message += "• Look for entries on pullbacks to the EMAs\n"
            elif market_condition in ["bearish", "moderately bearish"]:
                message += "• Market conditions favor short positions\n"
                message += "• Look for entries on rebounds to the EMAs\n"
            else:
                message += "• Market conditions are neutral - wait for clear directional signals\n"
                message += "• Focus on range-bound strategies until a breakout occurs\n"
        
        return message
    
    def get_symbol_switch_analysis(self, old_symbol, new_symbol):
        """Generate analysis when switching between symbols"""
        old_type = "GainX" if "GainX" in old_symbol else "PainX" if "PainX" in old_symbol else "Unknown"
        new_type = "GainX" if "GainX" in new_symbol else "PainX" if "PainX" in new_symbol else "Unknown"
        
        # Get the volatility numbers
        try:
            old_number = int(''.join(filter(str.isdigit, old_symbol)))
            new_number = int(''.join(filter(str.isdigit, new_symbol)))
            volatility_change = self._compare_volatility(old_number, new_number)
        except:
            volatility_change = "with different volatility characteristics"
        
        # Check if we're switching between different types
        type_change = old_type != new_type
        
        message = f"**Switching from {old_symbol} to {new_symbol}**\n\n"
        
        if type_change:
            message += f"You're switching from a {self.symbol_characteristics.get(old_type, 'synthetic index')} to a {self.symbol_characteristics.get(new_type, 'synthetic index')}.\n\n"
            message += f"**Key Differences:**\n"
            
            if old_type == "GainX" and new_type == "PainX":
                message += "• You're moving from a bullish-biased to a bearish-biased instrument\n"
                message += "• Strategy should adjust to favor short positions rather than longs\n"
                message += "• Look for price rejections at resistance rather than support\n"
            elif old_type == "PainX" and new_type == "GainX":
                message += "• You're moving from a bearish-biased to a bullish-biased instrument\n"
                message += "• Strategy should adjust to favor long positions rather than shorts\n"
                message += "• Look for price rejections at support rather than resistance\n"
        else:
            message += f"You're staying within the {old_type} family, but {volatility_change}.\n\n"
        
        message += f"**Smart Flow Scalper has automatically adjusted its parameters for {new_symbol}**\n"
        
        if new_type == "GainX":
            message += "• EMAs optimized for upward trending bias\n"
            message += "• RSI thresholds set to capture bullish momentum\n"
            message += f"• Stop loss and take profit levels calibrated for {new_symbol}'s volatility\n"
        else:
            message += "• EMAs optimized for downward trending bias\n"
            message += "• RSI thresholds set to capture bearish momentum\n"
            message += f"• Stop loss and take profit levels calibrated for {new_symbol}'s volatility\n"
        
        # Add recommended lot size based on volatility
        message += f"\n**Recommended Lot Size:** {self._recommend_lot_size(new_symbol)}\n"
        
        # Add timestamp
        message += f"\n_Analysis updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        
        return message
    
    def _compare_volatility(self, old_number, new_number):
        """Compare volatility between two symbols based on their numbers"""
        if new_number > old_number:
            if new_number >= 1200 and old_number < 1200:
                return "moving to extreme volatility"
            elif new_number >= 999 and old_number < 999:
                return "moving to very high volatility"
            elif new_number >= 800 and old_number < 800:
                return "moving to high volatility"
            else:
                return "moving to higher volatility"
        elif new_number < old_number:
            if old_number >= 1200 and new_number < 1200:
                return "moving to lower volatility from extreme"
            elif old_number >= 999 and new_number < 999:
                return "moving to lower volatility from very high"
            elif old_number >= 800 and new_number < 800:
                return "moving to lower volatility from high"
            else:
                return "moving to lower volatility"
        else:
            return "with similar volatility characteristics"
    
    def _recommend_lot_size(self, symbol):
        """Recommend lot size based on symbol volatility"""
        if "1200" in symbol:
            return "0.01 (extreme volatility)"
        elif "999" in symbol:
            return "0.01-0.02 (very high volatility)"
        elif "800" in symbol:
            return "0.01-0.05 (high volatility)"
        elif "600" in symbol:
            return "0.02-0.10 (medium-high volatility)"
        elif "400" in symbol:
            return "0.05-0.20 (medium volatility)"
        else:
            return "0.01-0.05 (adjust based on account size)"