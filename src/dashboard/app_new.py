import dash
from dash import dcc, html, callback_context, ctx
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import time
import threading
import os
import json
import random
import traceback

from ..strategies.smart_flow_scalper import SmartFlowScalper
from ..mt5_connector import initialize_mt5
from src.mt5_connector import initialize_mt5, place_order, get_account_info, get_symbol_type
from src.dashboard.chatbot import TradingChatbot  # Import the chatbot

# Global variables
strategy_instance = None
last_signals = pd.DataFrame()
trade_history = []
dashboard_active = True

# Initialize the chatbot
chatbot = TradingChatbot()

# Theme colors
DARK_THEME = {
    'background': '#1E1E1E',
    'text': '#FFFFFF',
    'grid': '#333333',
    'buy': '#26A69A',   # Green
    'sell': '#EF5350',  # Red
    'panel': '#2A2A2A',
    'header': '#303030',
    'accent': '#00B7FF'
}

# Define available symbols including all GainX and PainX variants
AVAILABLE_SYMBOLS = [
    "GainX 800",
    "PainX 800",
    "GainX 600",
    "PainX 600",
    "GainX 400",
    "PainX 999",
    "GainX 999",
    "PainX 1200",
    "GainX 1200"
]

# Symbol-specific settings
SYMBOL_SETTINGS = {
    # GainX series (bullish bias)
    "GainX 800": {
        "color": "#26A69A",  # Green
        "bias": "bullish",
        "volatility": "high",
        "recommended_lot": "0.01-0.05",
        "description": "High volatility with bullish bias"
    },
    "GainX 600": {
        "color": "#4CAF50",  # Green variant
        "bias": "bullish",
        "volatility": "medium-high",
        "recommended_lot": "0.02-0.10",
        "description": "Medium-high volatility with bullish bias"
    },
    "GainX 400": {
        "color": "#8BC34A",  # Light green
        "bias": "bullish",
        "volatility": "medium",
        "recommended_lot": "0.05-0.20",
        "description": "Medium volatility with bullish bias"
    },
    "GainX 999": {
        "color": "#00BFA5",  # Teal
        "bias": "bullish",
        "volatility": "very high",
        "recommended_lot": "0.01-0.03",
        "description": "Very high volatility with bullish bias"
    },
    "GainX 1200": {
        "color": "#009688",  # Darker green
        "bias": "bullish",
        "volatility": "extreme",
        "recommended_lot": "0.01",
        "description": "Extreme volatility with bullish bias"
    },
    
    # PainX series (bearish bias)
    "PainX 800": {
        "color": "#F44336",  # Red
        "bias": "bearish",
        "volatility": "high",
        "recommended_lot": "0.01-0.05",
        "description": "High volatility with bearish bias"
    },
    "PainX 600": {
        "color": "#E91E63",  # Pink/red
        "bias": "bearish",
        "volatility": "medium-high",
        "recommended_lot": "0.02-0.10",
        "description": "Medium-high volatility with bearish bias"
    },
    "PainX 999": {
        "color": "#FF5722",  # Deep orange
        "bias": "bearish",
        "volatility": "very high",
        "recommended_lot": "0.01-0.03",
        "description": "Very high volatility with bearish bias"
    },
    "PainX 1200": {
        "color": "#D32F2F",  # Dark red
        "bias": "bearish",
        "volatility": "extreme",
        "recommended_lot": "0.01",
        "description": "Extreme volatility with bearish bias"
    }
}

# Add these global variables
current_symbol = "GainX 800"  # Default symbol
previous_symbol = None
strategies = {}
symbol_data = {}
symbol_strategies = {}  # Dictionary to store strategy instances for each symbol

def create_strategy_instance():
    """Create a strategy instance and return it"""
    global strategy_instance
    if strategy_instance is None:
        # Initialize MT5 if not already done
        if not mt5.initialize():
            initialize_mt5()
        
        # Create strategy instance
        strategy_instance = SmartFlowScalper(
            symbol="GainX 800",
            timeframe=mt5.TIMEFRAME_M5,
            lot_size=0.01
        )
    return strategy_instance

def background_strategy_runner():
    """Run the strategy in the background"""
    global dashboard_active, last_signals, trade_history
    
    strategy = create_strategy_instance()
    
    while dashboard_active:
        try:
            # Get fresh data every cycle
            data = strategy.get_data(bars=100)
            signals = strategy.generate_signals(data)
            
            # Update the global variable with the latest data
            last_signals = signals
            
            # Check for new signals
            recent_signals = signals.iloc[-5:]  # Look at the last 5 candles
            
            if recent_signals['buy_signal'].any():
                buy_index = recent_signals[recent_signals['buy_signal']].index[-1]
                buy_price = signals.loc[buy_index, 'close']
                buy_time = signals.loc[buy_index, 'time']
                
                # Create trade record
                trade = {
                    'type': 'BUY',
                    'price': buy_price,
                    'time': buy_time,
                    'symbol': strategy.symbol
                }
                trade_history.append(trade)
                print(f"BUY SIGNAL detected at {buy_time} (price: {buy_price:.2f})")
                
            elif recent_signals['sell_signal'].any():
                sell_index = recent_signals[recent_signals['sell_signal']].index[-1]
                sell_price = signals.loc[sell_index, 'close']
                sell_time = signals.loc[sell_index, 'time']
                
                # Create trade record
                trade = {
                    'type': 'SELL',
                    'price': sell_price,
                    'time': sell_time,
                    'symbol': strategy.symbol
                }
                trade_history.append(trade)
                print(f"SELL SIGNAL detected at {sell_time} (price: {sell_price:.2f})")
            
            # Print latest price for monitoring
            if not signals.empty:
                latest = signals.iloc[-1]
                print(f"Latest price: {latest['close']:.2f} at {latest['time']}")
                
            # Sleep for a shorter time to update more frequently
            time.sleep(5)  # Update every 5 seconds instead of 30
            
        except Exception as e:
            print(f"Error in background strategy runner: {e}")
            time.sleep(10)

# Helper functions for chart creation and signal processing
def empty_chart_figure():
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor=DARK_THEME['background'],
        paper_bgcolor=DARK_THEME['background'],
        height=800,
        annotations=[
            dict(
                text="No data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
        ]
    )
    return fig

def create_chart_figure(data, symbol):
    if data.empty:
        return empty_chart_figure()
    
    # Get symbol color from settings
    symbol_settings = SYMBOL_SETTINGS.get(symbol, {})
    primary_color = symbol_settings.get('color', DARK_THEME['accent'])
    
    # Create figure with subplots
    fig = make_subplots(rows=3, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.02,
                        row_heights=[0.6, 0.2, 0.2],
                        specs=[[{"secondary_y": True}], [{}], [{}]])
    
    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=data['time'],
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Price',
        increasing_line_color=DARK_THEME['buy'],
        decreasing_line_color=DARK_THEME['sell']
    ), row=1, col=1)
    
    # Add EMAs
    if 'ema_short' in data.columns and 'ema_long' in data.columns:
        fig.add_trace(go.Scatter(
            x=data['time'],
            y=data['ema_short'],
            name='EMA Short',
            line=dict(color=primary_color, width=1.5)
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=data['time'],
            y=data['ema_long'],
            name='EMA Long',
            line=dict(color='#9E9E9E', width=1.5)
        ), row=1, col=1)
    
    # Add buy/sell signals
    if 'buy_signal' in data.columns and 'sell_signal' in data.columns:
        buy_signals = data[data['buy_signal']]
        sell_signals = data[data['sell_signal']]
        
        fig.add_trace(go.Scatter(
            x=buy_signals['time'],
            y=buy_signals['low'] - (buy_signals['high'] - buy_signals['low']) * 0.2,
            mode='markers',
            marker=dict(symbol='triangle-up', size=10, color=DARK_THEME['buy']),
            name='Buy Signal'
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=sell_signals['time'],
            y=sell_signals['high'] + (sell_signals['high'] - sell_signals['low']) * 0.2,
            mode='markers',
            marker=dict(symbol='triangle-down', size=10, color=DARK_THEME['sell']),
            name='Sell Signal'
        ), row=1, col=1)
    
    # Add RSI
    if 'rsi' in data.columns:
        fig.add_trace(go.Scatter(
            x=data['time'],
            y=data['rsi'],
            name='RSI',
            line=dict(color=primary_color)
        ), row=2, col=1)
        
        # Add RSI horizontal lines
        fig.add_hline(y=70, line_dash="dash", line_color="#FF9800", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#2196F3", row=2, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="#9E9E9E", row=2, col=1)
    
    # Add MACD
    if 'macd' in data.columns and 'macd_signal' in data.columns:
        fig.add_trace(go.Scatter(
            x=data['time'],
            y=data['macd'],
            name='MACD',
            line=dict(color='#2196F3')
        ), row=3, col=1)
        
        fig.add_trace(go.Scatter(
            x=data['time'],
            y=data['macd_signal'],
            name='Signal',
            line=dict(color='#FF9800')
        ), row=3, col=1)
        
        # Add MACD histogram
        if 'macd_hist' in data.columns:
            hist_colors = [DARK_THEME['buy'] if val >= 0 else DARK_THEME['sell'] for val in data['macd_hist']]
            
            fig.add_trace(go.Bar(
                x=data['time'],
                y=data['macd_hist'],
                name='Histogram',
                marker_color=hist_colors
            ), row=3, col=1)
    
    # Update layout for dark theme
    fig.update_layout(
        title=f'{symbol} Chart',
        template="plotly_dark",
        plot_bgcolor=DARK_THEME['background'],
        paper_bgcolor=DARK_THEME['background'],
        xaxis_rangeslider_visible=False,
        height=800,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=30, b=10)
    )
    
    # Add labels
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    
    return fig

def create_signal_panel(data, strategy):
    if data.empty:
        return html.Div("No signals available")
    
    # Get the last 10 candles
    recent_data = data.tail(10)
    
    # Check for recent signals
    recent_buy = recent_data['buy_signal'].any()
    recent_sell = recent_data['sell_signal'].any()
    
    # Get latest indicator values
    latest = data.iloc[-1]
    
    # Create signal panel content
    content = []
    
    # Add signal if exists
    if recent_buy:
        buy_index = recent_data[recent_data['buy_signal']].index[-1]
        buy_price = data.loc[buy_index, 'close']
        buy_time = data.loc[buy_index, 'time']
        
        content.append(html.Div([
            html.Span("BUY SIGNAL", style={
                'backgroundColor': DARK_THEME['buy'],
                'color': 'white',
                'fontWeight': 'bold',
                'padding': '5px 10px',
                'borderRadius': '4px'
            }),
            html.Span(f" at {buy_price:.2f}", style={'marginLeft': '5px'})
        ], style={'marginBottom': '10px'}))
        
    elif recent_sell:
        sell_index = recent_data[recent_data['sell_signal']].index[-1]
        sell_price = data.loc[sell_index, 'close']
        sell_time = data.loc[sell_index, 'time']
        
        content.append(html.Div([
            html.Span("SELL SIGNAL", style={
                'backgroundColor': DARK_THEME['sell'],
                'color': 'white',
                'fontWeight': 'bold',
                'padding': '5px 10px',
                'borderRadius': '4px'
            }),
            html.Span(f" at {sell_price:.2f}", style={'marginLeft': '5px'})
        ], style={'marginBottom': '10px'}))
    else:
        content.append(html.Div([
            html.Span("NEUTRAL", style={
                'backgroundColor': '#9E9E9E',
                'color': 'white',
                'fontWeight': 'bold',
                'padding': '5px 10px',
                'borderRadius': '4px'
            }),
            html.Span(" - No current signal", style={'marginLeft': '5px'})
        ], style={'marginBottom': '10px'}))
    
    # Add indicator information
    ema_status = "Bullish" if latest['ema_short'] > latest['ema_long'] else "Bearish"
    ema_color = DARK_THEME['buy'] if latest['ema_short'] > latest['ema_long'] else DARK_THEME['sell']
    
    rsi_status = "Overbought" if latest['rsi'] > strategy.rsi_overbought else "Oversold" if latest['rsi'] < strategy.rsi_oversold else "Neutral"
    rsi_color = DARK_THEME['sell'] if latest['rsi'] > strategy.rsi_overbought else DARK_THEME['buy'] if latest['rsi'] < strategy.rsi_oversold else "#9E9E9E"
    
    macd_status = "Bullish" if latest['macd'] > latest['macd_signal'] else "Bearish"
    macd_color = DARK_THEME['buy'] if latest['macd'] > latest['macd_signal'] else DARK_THEME['sell']
    
    content.extend([
        html.Div([
            html.Span("EMA Trend: ", style={'fontWeight': 'bold'}),
            html.Span(ema_status, style={'color': ema_color})
        ]),
        html.Div([
            html.Span("RSI Status: ", style={'fontWeight': 'bold'}),
            html.Span(f"{rsi_status} ({latest['rsi']:.1f})", style={'color': rsi_color})
        ]),
        html.Div([
            html.Span("MACD: ", style={'fontWeight': 'bold'}),
            html.Span(macd_status, style={'color': macd_color})
        ])
    ])
    
    return content

# Main function to create dashboard
def create_dashboard():
    """Create the dashboard layout"""
    app = dash.Dash(__name__, title="Smart Flow Scalper Dashboard")
    
    app.layout = html.Div(style={
        'backgroundColor': DARK_THEME['background'],
        'color': DARK_THEME['text'],
        'fontFamily': 'Segoe UI, Roboto, sans-serif',
        'padding': '20px'
    }, children=[
        # Header
        html.Div(style={
            'backgroundColor': DARK_THEME['header'],
            'padding': '20px',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
        }, children=[
            html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}, children=[
                html.Div(children=[
                    html.H1("Smart Flow Scalper Dashboard", style={
                        'marginBottom': '5px',
                        'color': DARK_THEME['accent']
                    }),
                    html.H3(id='symbol-title', children="GainX 800 (M5 Timeframe)", style={
                        'marginTop': '0'
                    }),
                ]),
                html.Div(style={'minWidth': '220px'}, children=[
                    html.Label("Select Symbol", style={'display': 'block', 'marginBottom': '5px', 'color': '#999'}),
                    dcc.Dropdown(
                        id='symbol-dropdown',
                        options=[{'label': symbol, 'value': symbol} for symbol in AVAILABLE_SYMBOLS],
                        value='GainX 800',
                        style={
                            'backgroundColor': DARK_THEME['panel'],
                            'color': 'white',
                            'border': f'1px solid {DARK_THEME["grid"]}',
                        }
                    ),
                ]),
            ]),
            html.Div(id='symbol-details', style={
                'marginTop': '15px',
                'padding': '10px',
                'backgroundColor': 'rgba(0,0,0,0.2)',
                'borderRadius': '4px',
                'fontSize': '14px'
            })
        ]),
        
        # Main content
        html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px'}, children=[
            # Left column - Chart and controls
            html.Div(style={
                'flex': '2',
                'minWidth': '600px',
                'backgroundColor': DARK_THEME['panel'],
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
            }, children=[
                # Price chart
                html.H3("Price Chart & Signals", style={'marginTop': '0'}),
                dcc.Graph(id='price-chart', style={'height': '500px'}),
                
                # Refresh controls
                html.Div(style={'display': 'flex', 'alignItems': 'center', 'marginTop': '10px'}, children=[
                    html.Button("Refresh Now", id='refresh-button', style={
                        'backgroundColor': DARK_THEME['accent'],
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'borderRadius': '4px',
                        'marginRight': '15px',
                        'cursor': 'pointer'
                    }),
                    html.Div("Auto-updates every 5 seconds", style={'color': '#999'}),
                    html.Div([
                        html.Span("Status: ", style={'marginRight': '5px'}),
                        html.Span(id='update-status', children="Idle", 
                                  style={'color': DARK_THEME['accent']})
                    ], style={'marginLeft': '15px'}),
                ]),
            ]),
            
            # Right column - Stats and signals
            html.Div(style={
                'flex': '1',
                'minWidth': '300px',
                'display': 'flex',
                'flexDirection': 'column',
                'gap': '20px'
            }, children=[
                # Current market data
                html.Div(style={
                    'backgroundColor': DARK_THEME['panel'],
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
                }, children=[
                    html.H3("Current Market Data", style={'marginTop': '0', 'marginBottom': '15px'}),
                    html.Div(id='current-price', style={'fontSize': '24px', 'fontWeight': 'bold'}),
                    html.Div(id='price-change', style={'marginBottom': '15px'}),
                    html.Hr(),
                    
                    html.Div([
                        html.Span("LIVE PRICE", style={
                            'backgroundColor': DARK_THEME['accent'],
                            'color': 'white',
                            'padding': '2px 8px',
                            'borderRadius': '4px',
                            'fontSize': '12px',
                            'marginRight': '10px'
                        }),
                        html.Span(id='live-price', style={
                            'fontSize': '28px', 
                            'fontWeight': 'bold'
                        }),
                    ], style={'marginBottom': '10px'}),

                    html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '10px'}, children=[
                        html.Div("EMA 20:"),
                        html.Div(id='ema-20-value', style={'textAlign': 'right'}),
                        html.Div("EMA 50:"),
                        html.Div(id='ema-50-value', style={'textAlign': 'right'}),
                        html.Div("RSI:"),
                        html.Div(id='rsi-value', style={'textAlign': 'right'}),
                        html.Div("MACD:"),
                        html.Div(id='macd-value', style={'textAlign': 'right'}),
                    ]),
                ]),
                
                # Latest signals
                html.Div(style={
                    'backgroundColor': DARK_THEME['panel'],
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
                }, children=[
                    html.H3("Latest Signals", style={'marginTop': '0', 'marginBottom': '15px'}),
                    html.Div(id='latest-signals', children=[
                        html.Div("No signals detected yet", style={'color': '#999', 'marginTop': '10px'})
                    ]),
                ]),
                
                # Trade history
                html.Div(style={
                    'backgroundColor': DARK_THEME['panel'],
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
                }, children=[
                    html.H3("Trade History", style={'marginTop': '0', 'marginBottom': '15px'}),
                    html.Div(id='trade-history', children=[
                        html.Div("No trades executed yet", style={'color': '#999', 'marginTop': '10px'})
                    ]),
                ]),
                
                # Performance panel
                html.Div(style={
                    'backgroundColor': DARK_THEME['panel'],
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                    'marginTop': '20px'
                }, children=[
                    html.H3("Strategy Performance", style={'marginTop': '0', 'marginBottom': '15px'}),
                    html.Div(id='performance-stats', children=[
                        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '10px'}, children=[
                            html.Div("Win Rate:"),
                            html.Div(id='win-rate', style={'textAlign': 'right'}),
                            html.Div("Profit Factor:"),
                            html.Div(id='profit-factor', style={'textAlign': 'right'}),
                            html.Div("Total Profit:"),
                            html.Div(id='total-profit', style={'textAlign': 'right'}),
                            html.Div("Max Drawdown:"),
                            html.Div(id='max-drawdown', style={'textAlign': 'right'}),
                        ]),
                    ]),
                ]),
                
                # Add AI chatbot section
                html.Div(style={
                    'backgroundColor': DARK_THEME['panel'],
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                    'marginTop': '20px',
                    'transition': 'all 0.3s ease'
                }, children=[
                    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}, children=[
                        html.H3("Smart Flow AI Assistant", style={'marginTop': '0', 'color': DARK_THEME['accent']}),
                        html.Button("Analyze Market", id='analyze-button', style={
                            'backgroundColor': DARK_THEME['accent'],
                            'color': 'white',
                            'border': 'none',
                            'padding': '8px 15px',
                            'borderRadius': '4px',
                            'cursor': 'pointer'
                        })
                    ]),
                    html.Div(id='chatbot-content', style={
                        'marginTop': '15px',
                        'padding': '15px',
                        'backgroundColor': 'rgba(0, 0, 0, 0.2)',
                        'borderRadius': '8px',
                        'maxHeight': '300px',
                        'overflowY': 'auto',
                        'fontSize': '14px'
                    }, children=[
                        html.Div("Welcome to Smart Flow AI Assistant! Click 'Analyze Market' for AI-powered insights on the current symbol.", 
                                style={'color': '#999'})
                    ]),
                    
                    # Visual transition effect for symbol changes
                    html.Div(id="symbol-transition", style={
                        'marginTop': '15px',
                        'display': 'none'
                    }),
                ]),
                
                # Add strategy adaptation panel
                html.Div(id='strategy-adaptation', style={
                    'backgroundColor': DARK_THEME['panel'],
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                    'marginTop': '20px',
                    'display': 'none',  # Start hidden, show after symbol change
                    'transition': 'all 0.5s ease'
                }),
                
                # Add signal panel
                html.Div(id='signal-panel', style={
                    'backgroundColor': DARK_THEME['panel'],
                    'padding': '15px',
                    'borderRadius': '8px',
                    'marginTop': '15px'
                })
            ]),
        ]),
        
        # Intervals and stored data
        dcc.Interval(id='interval-component', interval=5*1000, n_intervals=0),
        dcc.Interval(id='refresh-interval', interval=5*1000, n_intervals=0),
        dcc.Store(id="previous-symbol", data=""),
        dcc.Store(id="api-status", data="connected")
    ])
    
    # CALLBACKS
    # One main callback that handles all updates
    @app.callback(
        [Output('price-chart', 'figure'),
         Output('current-price', 'children'),
         Output('price-change', 'children'),
         Output('price-change', 'style'),
         Output('live-price', 'children'),  # This was missing in the return statement
         Output('ema-20-value', 'children'),
         Output('ema-50-value', 'children'),
         Output('rsi-value', 'children'),
         Output('macd-value', 'children'),
         Output('latest-signals', 'children'),
         Output('trade-history', 'children'),
         Output('update-status', 'children'),
         Output('update-status', 'style'),
         Output('signal-panel', 'children')],
        [Input('interval-component', 'n_intervals'),
         Input('refresh-button', 'n_clicks'),
         Input('symbol-dropdown', 'value')],
        [State('api-status', 'data')]
    )
    def update_dashboard(n_intervals, n_clicks, selected_symbol, api_status):
        global current_symbol, symbol_strategies, last_signals, trade_history
        
        # Determine which input triggered this callback
        trigger_id = ctx.triggered_id if not None else 'interval-component'
        
        # Track if symbol has changed
        symbol_changed = selected_symbol != current_symbol
        if symbol_changed:
            print(f"Switching from {current_symbol} to {selected_symbol}")
            current_symbol = selected_symbol
        
        # Get or create strategy instance for this symbol
        if selected_symbol not in symbol_strategies:
            # Create new strategy instance for this symbol
            symbol_strategies[selected_symbol] = SmartFlowScalper(
                symbol=selected_symbol,
                timeframe=mt5.TIMEFRAME_M5,
                auto_optimize=True
            )
            
        # Use the strategy for the selected symbol
        strategy = symbol_strategies[selected_symbol]
        
        # Get fresh data
        data = strategy.get_data(bars=100)
        
        if data.empty:
            # Define defaults for empty data
            empty_fig = empty_chart_figure()
            price_display = "Price: N/A"
            price_change_text = "Change: N/A"
            price_change_style = {'color': '#999', 'fontSize': '14px', 'marginBottom': '15px'}
            live_price = "N/A"  # Make sure this is included
            ema_20_value = "N/A"
            ema_50_value = "N/A"
            rsi_value = "N/A"
            macd_value = "N/A"
            signal_panel = html.Div("No signal available")
            latest_signals = html.Div("No data available", style={'color': '#999', 'marginTop': '10px'})
            trade_history_display = html.Div("No trades executed yet", style={'color': '#999', 'marginTop': '10px'})
            update_status = "No data available"
            update_status_style = {'color': DARK_THEME['sell']}
            
            return (empty_fig, price_display, price_change_text, price_change_style, live_price,
                    ema_20_value, ema_50_value, rsi_value, macd_value, latest_signals, 
                    trade_history_display, update_status, update_status_style, signal_panel)
        
        # Generate signals for this symbol
        signals = strategy.generate_signals(data)
        last_signals = signals  # Update global signals
        
        # Create the chart figure
        fig = create_chart_figure(signals, selected_symbol)
        
        # Get the latest price and indicators
        latest = signals.iloc[-1]
        current_price = f"${latest['close']:,.2f}"
        
        # Set live price (same as current price)
        live_price = f"${latest['close']:,.2f}"
        
        # Calculate price change
        if len(signals) >= 2:
            price_change_abs = latest['close'] - signals.iloc[-2]['close']
            price_change_pct = price_change_abs / signals.iloc[-2]['close'] * 100
            price_change_text = f"Change: {price_change_abs:+,.2f} ({price_change_pct:+,.2f}%)"
            price_change_style = {
                'color': DARK_THEME['buy'] if price_change_abs >= 0 else DARK_THEME['sell'],
                'fontSize': '14px',
                'marginBottom': '15px'
            }
        else:
            price_change_text = "Change: N/A"
            price_change_style = {'color': '#999', 'fontSize': '14px', 'marginBottom': '15px'}
        
        # Indicators
        ema_20_value = f"{latest['ema_short']:,.2f}" if 'ema_short' in latest and not pd.isna(latest['ema_short']) else "N/A"
        ema_50_value = f"{latest['ema_long']:,.2f}" if 'ema_long' in latest and not pd.isna(latest['ema_long']) else "N/A"
        rsi_value = f"{latest['rsi']:.2f}" if 'rsi' in latest and not pd.isna(latest['rsi']) else "N/A"
        
        if 'macd' in latest and 'macd_signal' in latest and not pd.isna(latest['macd']) and not pd.isna(latest['macd_signal']):
            macd_value = f"{latest['macd']:.2f} (Signal: {latest['macd_signal']:.2f})"
        else:
            macd_value = "N/A"
        
        # Create signal panel content
        signal_panel = create_signal_panel(signals, strategy)
        
        # Latest signals
        latest_signals_components = []
        # Check recent signals (last 5 candles)
        recent_signals = signals.iloc[-5:]
        
        buy_signal_index = None
        sell_signal_index = None
        
        if recent_signals['buy_signal'].any():
            buy_signal_index = recent_signals[recent_signals['buy_signal']].index[-1]
        
        if recent_signals['sell_signal'].any():
            sell_signal_index = recent_signals[recent_signals['sell_signal']].index[-1]
        
        if buy_signal_index is not None:
            buy_time = signals.loc[buy_signal_index, 'time']
            buy_price = signals.loc[buy_signal_index, 'close']
            latest_signals_components.append(
                html.Div([
                    html.Div("BUY SIGNAL", style={
                        'backgroundColor': DARK_THEME['buy'],
                        'color': 'white',
                        'padding': '8px 15px',
                        'borderRadius': '4px',
                        'fontWeight': 'bold',
                        'display': 'inline-block'
                    }),
                    html.Div(f"at {buy_time} (${buy_price:,.2f})", style={
                        'marginTop': '5px',
                        'marginBottom': '10px'
                    })
                ])
            )
        
        if sell_signal_index is not None:
            sell_time = signals.loc[sell_signal_index, 'time']
            sell_price = signals.loc[sell_signal_index, 'close']
            latest_signals_components.append(
                html.Div([
                    html.Div("SELL SIGNAL", style={
                        'backgroundColor': DARK_THEME['sell'],
                        'color': 'white',
                        'padding': '8px 15px',
                        'borderRadius': '4px',
                        'fontWeight': 'bold',
                        'display': 'inline-block'
                    }),
                    html.Div(f"at {sell_time} (${sell_price:,.2f})", style={
                        'marginTop': '5px',
                        'marginBottom': '10px'
                    })
                ])
            )
            
        # If no signals, show "no signals"
        if len(latest_signals_components) == 0:
            latest_signals_components.append(
                html.Div("No recent signals detected", style={'color': '#999', 'marginTop': '10px'})
            )
        
        # Create trade history display
        if trade_history:
            trade_history_items = []
            for i, trade in enumerate(trade_history[-10:]): # Show last 10 trades
                trade_type = trade['type']
                trade_color = DARK_THEME['buy'] if trade_type == 'BUY' else DARK_THEME['sell']
                trade_history_items.append(
                    html.Div([
                        html.Span(trade_type, style={
                            'backgroundColor': trade_color,
                            'color': 'white',
                            'padding': '3px 8px',
                            'borderRadius': '4px',
                            'fontWeight': 'bold',
                            'fontSize': '12px',
                            'marginRight': '8px'
                        }),
                        html.Span(f"{trade['symbol']} @ ${trade['price']:.2f}", style={'marginRight': '8px'}),
                        html.Span(f"{trade['time']}", style={'fontSize': '12px', 'color': '#999'})
                    ], style={'marginBottom': '5px'})
                )
            trade_history_display = html.Div(trade_history_items)
        else:
            trade_history_display = html.Div("No trades executed yet", style={'color': '#999', 'marginTop': '10px'})
        
        update_status = f"Updated {datetime.now().strftime('%H:%M:%S')}"
        update_status_style = {'color': DARK_THEME['buy']}
        
        return (fig, current_price, price_change_text, price_change_style, live_price,
                ema_20_value, ema_50_value, rsi_value, macd_value, 
                html.Div(latest_signals_components), trade_history_display, 
                update_status, update_status_style, signal_panel)
    
    # Symbol selection and details callback
    @app.callback(
        [Output('symbol-title', 'children'),
         Output('symbol-details', 'children')],
        [Input('symbol-dropdown', 'value')]
    )
    def update_symbol_selection(selected_symbol):
        global current_symbol
        current_symbol = selected_symbol
        
        settings = SYMBOL_SETTINGS.get(selected_symbol, {})
        
        # Create symbol details panel
        details = [
            html.Div([
                html.Span("Bias: ", style={'fontWeight': 'bold', 'marginRight': '5px'}),
                html.Span(settings.get('bias', 'neutral').capitalize(), style={
                    'color': {
                        'bullish': '#26A69A', 
                        'bearish': '#F44336',
                        'neutral': '#FFC107'
                    }.get(settings.get('bias', 'neutral'), 'white')
                })
            ]),
            html.Div([
                html.Span("Volatility: ", style={'fontWeight': 'bold', 'marginRight': '5px'}),
                html.Span(settings.get('volatility', 'medium').capitalize(), style={
                    'color': {
                        'low': '#4CAF50',
                        'medium': '#8BC34A',
                        'medium-high': '#FFC107',
                        'high': '#FF9800',
                        'very high': '#FF5722',
                        'extreme': '#F44336'
                    }.get(settings.get('volatility', 'medium'), 'white')
                })
            ]),
            html.Div([
                html.Span("Recommended lot size: ", style={'fontWeight': 'bold', 'marginRight': '5px'}),
                html.Span(settings.get('recommended_lot', '0.01-0.05'))
            ]),
            html.Div([
                html.Span("Description: ", style={'fontWeight': 'bold', 'marginRight': '5px'}),
                html.Span(settings.get('description', '-'))
            ]),
        ]
        
        # Return the new title and details
        return f"{selected_symbol} (M5 Timeframe)", details
    
    # Chatbot callback
    @app.callback(
        [Output('chatbot-content', 'children'),
         Output('chatbot-content', 'style')],
        [Input('analyze-button', 'n_clicks'),
         Input('symbol-dropdown', 'value')],
        [State('chatbot-content', 'children'),
         State('previous-symbol', 'data')],
        prevent_initial_call=True
    )
    def update_chatbot(analyze_clicks, symbol, current_content, prev_symbol):
        trigger = ctx.triggered_id
        global symbol_data, current_symbol
        
        # Default style
        style = {
            'marginTop': '15px',
            'padding': '15px',
            'backgroundColor': 'rgba(0, 0, 0, 0.2)',
            'borderRadius': '8px',
            'maxHeight': '300px',
            'overflowY': 'auto',
            'fontSize': '14px',
            'transition': 'all 0.3s ease'
        }
        
        if trigger == 'analyze-button':
            # Generate market analysis with AI
            if symbol in symbol_data and symbol_data[symbol] is not None:
                analysis = chatbot.analyze_market(symbol, symbol_data[symbol])
                
                # Convert markdown-like syntax to HTML
                analysis = analysis.replace('**', '<b>').replace('**', '</b>')
                analysis = analysis.replace('_', '<i>').replace('_', '</i>')
                analysis = analysis.replace('\n\n', '<br><br>')
                analysis = analysis.replace('\n•', '<br>•')
                
                return [
                    html.Div([
                        html.Div(
                            dangerously_allow_html=True,
                            children=analysis
                        )
                    ], style={'animation': 'fadeIn 0.5s'}),
                    {**style, 'border': f'1px solid {SYMBOL_SETTINGS[symbol]["color"]}'}
                ]
            else:
                return [
                    html.Div("No data available for analysis. Please ensure your MT5 connection is active.", 
                            style={'color': DARK_THEME['sell']}),
                    style
                ]
        
        elif trigger == 'symbol-dropdown' and prev_symbol and prev_symbol != symbol:
            # Generate symbol switch analysis
            switch_analysis = chatbot.get_symbol_switch_analysis(prev_symbol, symbol)
            
            # Convert markdown-like syntax to HTML
            switch_analysis = switch_analysis.replace('**', '<b>').replace('**', '</b>')
            switch_analysis = switch_analysis.replace('_', '<i>').replace('_', '</i>')
            switch_analysis = switch_analysis.replace('\n\n', '<br><br>')
            switch_analysis = switch_analysis.replace('\n•', '<br>•')
            
            # Get the new symbol's color for styling
            new_color = SYMBOL_SETTINGS[symbol]["color"]
            
            return [
                html.Div([
                    html.Div(
                        dangerously_allow_html=True,
                        children=switch_analysis
                    )
                ], style={'animation': 'fadeIn 0.5s'}),
                {**style, 'border': f'1px solid {new_color}'}
            ]
        
        raise PreventUpdate
    
    # Symbol transition and strategy adaptation callback
    @app.callback(
        [Output('symbol-transition', 'style'),
         Output('symbol-transition', 'children'),
         Output('previous-symbol', 'data'),
         Output('strategy-adaptation', 'style'),
         Output('strategy-adaptation', 'children')],
        [Input('symbol-dropdown', 'value')],
        [State('previous-symbol', 'data')]
    )
    def handle_symbol_transition(new_symbol, prev_symbol):
        if not prev_symbol or prev_symbol == new_symbol:
            # Store the initial symbol
            return {'display': 'none'}, [], new_symbol, {'display': 'none'}, []
        
        # Get colors for transition effect
        prev_color = SYMBOL_SETTINGS[prev_symbol]["color"] if prev_symbol in SYMBOL_SETTINGS else "#FFFFFF"
        new_color = SYMBOL_SETTINGS[new_symbol]["color"] if new_symbol in SYMBOL_SETTINGS else "#FFFFFF"
        
        # Create transition animation
        transition_style = {
            'display': 'block',
            'padding': '20px',
            'backgroundColor': 'rgba(0, 0, 0, 0.3)',
            'borderRadius': '8px',
            'marginTop': '15px',
            'textAlign': 'center',
            'animation': 'pulse 1s',
            'border': f'1px solid {new_color}',
            'transition': 'all 0.5s ease'
        }
        
        # Create transition message
        transition_content = [
            html.Div(f"Switching from {prev_symbol} to {new_symbol}", 
                    style={'fontSize': '18px', 'fontWeight': 'bold', 'marginBottom': '10px'}),
            html.Div([
                html.Span("Smart Flow Scalper is optimizing strategy parameters...", 
                        style={'marginRight': '10px'}),
                html.Div(className="loading-dots", children=[
                    html.Span(".", style={'animationDelay': '0s'}),
                    html.Span(".", style={'animationDelay': '0.2s'}),
                    html.Span(".", style={'animationDelay': '0.4s'})
                ])
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})
        ]
        
        # Get new symbol's settings for the strategy adaptation panel
        new_settings = SYMBOL_SETTINGS.get(new_symbol, {})
        
        # Create strategy adaptation panel
        adaptation_style = {
            'backgroundColor': DARK_THEME['panel'],
            'padding': '20px',
            'borderRadius': '8px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'marginTop': '20px',
            'display': 'block',
            'borderLeft': f'4px solid {new_color}',
            'animation': 'fadeIn 1s'
        }
        
        # Customized parameters based on symbol
        is_gainx = "GainX" in new_symbol
        ema_short = 10 if "1200" in new_symbol or "999" in new_symbol else 15 if "800" in new_symbol else 18 if "600" in new_symbol else 20
        ema_long = 30 if "1200" in new_symbol or "999" in new_symbol else 40 if "800" in new_symbol else 45 if "600" in new_symbol else 50
        rsi_ob = 75 if is_gainx and ("1200" in new_symbol or "999" in new_symbol) else 72 if is_gainx and "800" in new_symbol else 70
        rsi_os = 25 if not is_gainx and ("1200" in new_symbol or "999" in new_symbol) else 28 if not is_gainx and "800" in new_symbol else 30
        
        adaptation_content = [
            html.H4("Strategy Auto-Adaptation", style={'marginTop': '0', 'marginBottom': '15px'}),
            html.Div("Smart Flow Scalper has automatically optimized parameters for " + 
                    html.Span(new_symbol, style={'fontWeight': 'bold', 'color': new_color}),
                    style={'marginBottom': '10px'}),
            
            # Parameter visualization with horizontal bars
            html.Div([
                # EMA Short
                html.Div([
                    html.Div("EMA Short", style={'width': '100px'}),
                    html.Div(style={
                        'flex': '1',
                        'backgroundColor': 'rgba(0,0,0,0.2)',
                        'borderRadius': '4px',
                        'marginLeft': '10px',
                        'position': 'relative',
                        'height': '20px'
                    }, children=[
                        html.Div(style={
                            'position': 'absolute',
                            'backgroundColor': new_color,
                            'width': f'{(ema_short/30)*100}%',
                            'height': '100%',
                            'borderRadius': '4px',
                            'transition': 'width 1s ease-in-out'
                        }),
                        html.Div(f"{ema_short}", style={
                            'position': 'absolute',
                            'right': '10px',
                            'color': 'white',
                            'lineHeight': '20px'
                        })
                    ])
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
                
                # EMA Long
                html.Div([
                    html.Div("EMA Long", style={'width': '100px'}),
                    html.Div(style={
                        'flex': '1',
                        'backgroundColor': 'rgba(0,0,0,0.2)',
                        'borderRadius': '4px',
                        'marginLeft': '10px',
                        'position': 'relative',
                        'height': '20px'
                    }, children=[
                        html.Div(style={
                            'position': 'absolute',
                            'backgroundColor': new_color,
                            'width': f'{(ema_long/100)*100}%',
                            'height': '100%',
                            'borderRadius': '4px',
                            'transition': 'width 1s ease-in-out'
                        }),
                        html.Div(f"{ema_long}", style={
                            'position': 'absolute',
                            'right': '10px',
                            'color': 'white',
                            'lineHeight': '20px'
                        })
                    ])
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
                
                # RSI Levels
                html.Div([
                    html.Div("RSI Levels", style={'width': '100px'}),
                    html.Div(style={
                        'flex': '1',
                        'backgroundColor': 'rgba(0,0,0,0.2)',
                        'borderRadius': '4px',
                        'marginLeft': '10px',
                        'position': 'relative',
                        'height': '20px'
                    }, children=[
                        html.Div(style={
                            'position': 'absolute',
                            'left': f'{rsi_os}%',
                            'width': f'{rsi_ob - rsi_os}%',
                            'height': '100%',
                            'backgroundColor': new_color,
                            'borderRadius': '4px',
                            'transition': 'all 1s ease-in-out'
                        }),
                        html.Div(f"{rsi_os} - {rsi_ob}", style={
                            'position': 'absolute',
                            'right': '10px',
                            'color': 'white',
                            'lineHeight': '20px'
                        })
                    ])
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
                
                # Volatility Adaptation
                html.Div([
                    html.Div("Volatility", style={'width': '100px'}),
                    html.Div(style={
                        'display': 'flex',
                        'flex': '1',
                        'backgroundColor': 'rgba(0,0,0,0.2)',
                        'borderRadius': '4px',
                        'marginLeft': '10px',
                        'overflow': 'hidden'
                    }, children=[
                        html.Div("LOW", style={
                            'padding': '0 10px',
                            'backgroundColor': '#4CAF50' if "400" in new_symbol else 'transparent',
                            'color': 'white',
                            'transition': 'all 0.5s ease'
                        }),
                        html.Div("MEDIUM", style={
                            'padding': '0 10px',
                            'backgroundColor': '#FFC107' if "600" in new_symbol else 'transparent',
                            'color': 'white',
                            'transition': 'all 0.5s ease'
                        }),
                        html.Div("HIGH", style={
                            'padding': '0 10px',
                            'backgroundColor': '#FF9800' if "800" in new_symbol else 'transparent',
                            'color': 'white',
                            'transition': 'all 0.5s ease'
                        }),
                        html.Div("VERY HIGH", style={
                            'padding': '0 10px',
                            'backgroundColor': '#FF5722' if "999" in new_symbol else 'transparent',
                            'color': 'white',
                            'transition': 'all 0.5s ease'
                        }),
                        html.Div("EXTREME", style={
                            'padding': '0 10px',
                            'backgroundColor': '#F44336' if "1200" in new_symbol else 'transparent',
                            'color': 'white',
                            'transition': 'all 0.5s ease'
                        })
                    ])
                ], style={'display': 'flex', 'alignItems': 'center'}),
            ], style={'marginTop': '15px'})
        ]
        
        return transition_style, transition_content, new_symbol, adaptation_style, adaptation_content
        
    
    # Check AutoTrading status
    @app.callback(
        [Output('autotrading-status', 'children'),
         Output('autotrading-status', 'style')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_autotrading_status(n):
        if not mt5.initialize():
            return [
                [html.Span("MT5: ", style={'marginRight': '5px'}), 
                 html.Span("Disconnected")],
                {'backgroundColor': 'rgba(255, 23, 68, 0.7)', 'color': 'white', 'padding': '8px 12px',
                 'borderRadius': '4px', 'fontWeight': 'bold', 'display': 'flex', 'alignItems': 'center'}
            ]
        
        trade_allowed = mt5.terminal_info().trade_allowed
        
        if trade_allowed:
            return [
                [html.Span("AutoTrading: ", style={'marginRight': '5px'}), 
                 html.Span("Enabled")],
                {'backgroundColor': 'rgba(0, 200, 83, 0.7)', 'color': 'white', 'padding': '8px 12px',
                 'borderRadius': '4px', 'fontWeight': 'bold', 'display': 'flex', 'alignItems': 'center'}
            ]
        else:
            return [
                [html.Span("AutoTrading: ", style={'marginRight': '5px'}), 
                 html.Span("DISABLED")],
                {'backgroundColor': 'rgba(255, 23, 68, 0.7)', 'color': 'white', 'padding': '8px 12px',
                 'borderRadius': '4px', 'fontWeight': 'bold', 'display': 'flex', 'alignItems': 'center'}
            ]
    
    return app

def run_dashboard():
    """Run the dashboard"""
    global dashboard_active
    
    # Start the background thread for running the strategy
    thread = threading.Thread(target=background_strategy_runner)
    thread.daemon = True
    thread.start()
    
    # Create and run the dashboard
    try:
        app = create_dashboard()
        app.run(debug=False, port=8050, host='0.0.0.0')
    finally:
        dashboard_active = False
        mt5.shutdown()

if __name__ == "__main__":
    run_dashboard()