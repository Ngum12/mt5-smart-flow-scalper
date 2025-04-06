MT5 Smart Flow Scalper
A sophisticated algorithmic trading system for MetaTrader 5 featuring adaptive technical analysis, real-time signal generation, and a comprehensive web dashboard for monitoring trades.

<img alt="MT5 Smart Flow Scalper" src="https://via.placeholder.com/800x400?text=MT5+Smart+Flow+Scalper">
Table of Contents
Overview
Features
Installation
Dashboard Guide
Trading Logic
Symbol Information
Risk Management
Troubleshooting
License
Overview
MT5 Smart Flow Scalper is an advanced algorithmic trading system designed for MetaTrader 5. It combines multiple technical indicators to identify high-probability entry and exit points, with automatic stop-loss and take-profit management. The system adapts to different market conditions and volatility levels, with custom-tailored parameters for various synthetic symbols.

The system includes a powerful web dashboard built with Dash and Plotly for real-time monitoring of signals, trades, and performance metrics.

Features
Multi-Symbol Support: Trade multiple GainX and PainX synthetic instruments with optimized parameters
Real-Time Dashboard: Advanced visualization with candlestick charts, indicators, and trade history
Auto-Optimized Parameters: Trading parameters automatically adjust based on symbol volatility
AI Market Analysis: Built-in AI assistant provides market insights and analysis
Comprehensive Risk Management: Dynamic position sizing based on account balance and volatility
Visual Signals: Clear buy/sell signals with graphical representation
Performance Analytics: Track win rate, profit factor, and drawdown metrics
Automatic Trading: Fully automated entry and exit with customizable risk parameters
Installation
Prerequisites
Python 3.8+
MetaTrader 5 with active account
Required Python packages
Setup Instructions
Clone the repository:
Create and activate a virtual environment:
Install dependencies:
Ensure MetaTrader 5 is installed and running with AutoTrading enabled

Start the trading system:

Dashboard Guide
The dashboard provides a comprehensive view of your trading activity:

<img alt="Dashboard Overview" src="https://via.placeholder.com/800x400?text=Dashboard+Overview">
Key components:

Symbol Selector: Choose between different GainX and PainX instruments
Price Chart: Candlestick chart with EMA, RSI, and MACD indicators
Signal Panel: Shows current trading signals and indicator status
Trade History: Lists recent trades and outcomes
Performance Stats: Displays win rate, profit factor, and other metrics
AI Assistant: Provides AI-powered analysis of current market conditions
Trading Logic
The Smart Flow Scalper system makes trading decisions based on the following logic:

Entry Signals
BUY Signals
EMA short crosses above EMA long
RSI moves from oversold to neutral territory
MACD line crosses above signal line
SELL Signals
EMA short crosses below EMA long
RSI moves from overbought to neutral territory
MACD line crosses below signal line
Exit Mechanisms
The system has multiple ways to exit trades:

Take Profit (Profitable Exit):

Each trade is placed with an automatic take profit level
For BUY trades: take_profit = entry_price + (atr_multiplier * atr_value * risk_reward_ratio)
For SELL trades: take_profit = entry_price - (atr_multiplier * atr_value * risk_reward_ratio)
Profit Target: Typically 1.5-2x the risk amount (configurable risk-reward ratio)
Stop Loss (Loss Protection):

Each trade has a protective stop loss order
For BUY trades: stop_loss = entry_price - (atr_multiplier * atr_value)
For SELL trades: stop_loss = entry_price + (atr_multiplier * atr_value)
Based on ATR (Average True Range) to adapt to market volatility
Limits losses to a pre-defined percentage of account (usually 1%)
Dynamic Trailing Stop:

For winning trades, the stop loss moves in the direction of the trade
Secures profits while allowing trades to run
Symbol Information
The system is optimized for trading synthetic instruments with various volatility profiles:

Symbol	Bias	Volatility	Lot Size	Description
GainX 800	Bullish	High	0.01-0.05	High volatility with bullish bias
GainX 600	Bullish	Medium-high	0.02-0.10	Medium-high volatility with bullish bias
GainX 400	Bullish	Medium	0.05-0.20	Medium volatility with bullish bias
GainX 999	Bullish	Very high	0.01-0.03	Very high volatility with bullish bias
GainX 1200	Bullish	Extreme	0.01	Extreme volatility with bullish bias
PainX 800	Bearish	High	0.01-0.05	High volatility with bearish bias
PainX 600	Bearish	Medium-high	0.02-0.10	Medium-high volatility with bearish bias
PainX 999	Bearish	Very high	0.01-0.03	Very high volatility with bearish bias
PainX 1200	Bearish	Extreme	0.01	Extreme volatility with bearish bias
Risk Management
The system incorporates several risk management features:

Dynamic Position Sizing
The position size is automatically calculated based on:

Your account balance
Defined risk percentage (default: 1%)
Stop loss distance in pips
Symbol tick value
Volatility-Based Stops
Stop loss and take profit levels adapt to current market volatility using ATR:

Higher volatility = wider stops
Lower volatility = tighter stops
Adaptable Parameters
The system automatically adjusts parameters based on symbol characteristics:

Different EMA periods for different volatility profiles
Custom RSI parameters based on symbol bias
Adjusted MACD settings for fast/slow markets
Troubleshooting
Common Issues
AutoTrading Disabled
If you see "AutoTrading disabled by client" in the logs:

Open MT5 terminal
Click the "AutoTrading" button in the toolbar or press Alt+T
Confirm the button turns green indicating AutoTrading is enabled
Connection Issues
If the dashboard shows "MT5: Disconnected":

Ensure MetaTrader 5 is running
Restart the application
Check that your MT5 credentials are correct
Maximum Positions Error
If you see "position would exceed maximum positions":

Close some existing positions in MT5
Check your broker's maximum position limit
Adjust the system to work within your broker's limits
License
This project is licensed under the MIT License - see the LICENSE file for details.

© 2025 MT5 Smart Flow Scalper. All rights reserved.
