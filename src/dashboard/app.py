import dash
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import time
import threading

from ..strategies.smart_flow_scalper import SmartFlowScalper
from ..mt5_connector import initialize_mt5

# Global variables
strategy_instance = None
last_signals = pd.DataFrame()
trade_history = []
dashboard_active = True

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
                print(f"\n🟢 BUY SIGNAL detected at {buy_time} (price: {buy_price:.2f})")
                
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
                print(f"\n🔴 SELL SIGNAL detected at {sell_time} (price: {sell_price:.2f})")
            
            # Print latest price for monitoring
            if not signals.empty:
                latest = signals.iloc[-1]
                print(f"Latest price: {latest['close']:.2f} at {latest['time']}")
                
            # Sleep for a shorter time to update more frequently
            time.sleep(5)  # Update every 5 seconds instead of 30
            
        except Exception as e:
            print(f"Error in background strategy runner: {e}")
            time.sleep(10)

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
            html.H1("Smart Flow Scalper Dashboard", style={
                'marginBottom': '5px',
                'color': DARK_THEME['accent']
            }),
            html.H3(id='symbol-title', children="GainX 800 (M5 Timeframe)", style={
                'marginTop': '0'
            }),
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
                    dcc.Interval(
                        id='interval-component',
                        interval=5*1000,  # 5 seconds instead of 10 seconds
                        n_intervals=0
                    ),
                    html.Button("Refresh Now", id='refresh-button', style={
                        'backgroundColor': DARK_THEME['accent'],
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'borderRadius': '4px',
                        'marginRight': '15px',
                        'cursor': 'pointer'
                    }),
                    html.Div("Auto-updates every 10 seconds", style={'color': '#999'}),
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
            ]),
        ]),
    ])
    
    # Callbacks
    @app.callback(
        [Output('price-chart', 'figure'),
         Output('current-price', 'children'),
         Output('price-change', 'children'),
         Output('price-change', 'style'),
         Output('ema-20-value', 'children'),
         Output('ema-50-value', 'children'),
         Output('rsi-value', 'children'),
         Output('macd-value', 'children'),
         Output('latest-signals', 'children'),
         Output('trade-history', 'children'),
         Output('update-status', 'children'),
         Output('update-status', 'style')],
        [Input('interval-component', 'n_intervals'),
         Input('refresh-button', 'n_clicks')]
    )
    def update_dashboard(n_intervals, n_clicks):
        global last_signals, trade_history
        
        # Check if we have signals data
        if last_signals.empty:
            strategy = create_strategy_instance()
            data = strategy.get_data(bars=100)
            signals = strategy.generate_signals(data)
            last_signals = signals
        else:
            signals = last_signals
            
        # Create the price chart
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            specs=[[{"type": "candlestick"}],
                   [{"type": "scatter"}]]
        )
        
        # Check if we have enough data
        if len(signals) > 0:
            # Add candlestick chart
            candlestick = go.Candlestick(
                x=signals['time'],
                open=signals['open'],
                high=signals['high'],
                low=signals['low'],
                close=signals['close'],
                name="Price",
                increasing_line_color=DARK_THEME['buy'],
                decreasing_line_color=DARK_THEME['sell']
            )
            fig.add_trace(candlestick, row=1, col=1)
            
            # Add EMA lines
            if 'ema_short' in signals.columns:
                fig.add_trace(
                    go.Scatter(
                        x=signals['time'],
                        y=signals['ema_short'],
                        name="EMA 20",
                        line=dict(color='rgba(120, 220, 110, 0.8)', width=2)
                    ),
                    row=1, col=1
                )
            
            if 'ema_long' in signals.columns:
                fig.add_trace(
                    go.Scatter(
                        x=signals['time'],
                        y=signals['ema_long'],
                        name="EMA 50",
                        line=dict(color='rgba(255, 191, 0, 0.8)', width=2)
                    ),
                    row=1, col=1
                )
            
            # Add RSI
            if 'rsi' in signals.columns:
                fig.add_trace(
                    go.Scatter(
                        x=signals['time'],
                        y=signals['rsi'],
                        name="RSI",
                        line=dict(color='rgba(255, 255, 255, 0.8)', width=1.5)
                    ),
                    row=2, col=1
                )
                
                # Add RSI levels
                fig.add_shape(
                    type="line", line_color="rgba(255, 255, 255, 0.3)", line_width=1, opacity=0.8,
                    x0=signals['time'].iloc[0], y0=70, x1=signals['time'].iloc[-1], y1=70,
                    row=2, col=1
                )
                fig.add_shape(
                    type="line", line_color="rgba(255, 255, 255, 0.3)", line_width=1, opacity=0.8,
                    x0=signals['time'].iloc[0], y0=30, x1=signals['time'].iloc[-1], y1=30,
                    row=2, col=1
                )
                fig.add_shape(
                    type="line", line_color="rgba(255, 255, 255, 0.2)", line_width=1, opacity=0.5,
                    x0=signals['time'].iloc[0], y0=50, x1=signals['time'].iloc[-1], y1=50,
                    row=2, col=1
                )
            
            # Add buy/sell markers
            buy_signals = signals[signals['buy_signal'] == True]
            if len(buy_signals) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=buy_signals['time'],
                        y=buy_signals['low'] * 0.999,  # Position slightly below the candle
                        mode='markers',
                        marker=dict(
                            symbol='triangle-up',
                            size=12,
                            color=DARK_THEME['buy'],
                            line=dict(width=1, color='rgba(0, 0, 0, 0.5)')
                        ),
                        name="Buy Signal"
                    ),
                    row=1, col=1
                )
            
            sell_signals = signals[signals['sell_signal'] == True]
            if len(sell_signals) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=sell_signals['time'],
                        y=sell_signals['high'] * 1.001,  # Position slightly above the candle
                        mode='markers',
                        marker=dict(
                            symbol='triangle-down',
                            size=12,
                            color=DARK_THEME['sell'],
                            line=dict(width=1, color='rgba(0, 0, 0, 0.5)')
                        ),
                        name="Sell Signal"
                    ),
                    row=1, col=1
                )
        
        # Update layout
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor=DARK_THEME['background'],
            paper_bgcolor=DARK_THEME['background'],
            margin=dict(l=0, r=10, t=0, b=0),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(0,0,0,0.3)"
            ),
            transition_duration=500,  # Add smooth transitions
            uirevision='same',  # Preserve zoom level during updates
            xaxis=dict(
                showgrid=True,
                gridcolor=DARK_THEME['grid'],
                zeroline=False
            ),
            xaxis2=dict(
                showgrid=True,
                gridcolor=DARK_THEME['grid'],
                zeroline=False
            ),
            yaxis2=dict(
                showgrid=True,
                gridcolor=DARK_THEME['grid'],
                zeroline=False,
                range=[0, 100]  # RSI range
            )
        )
        
        # Current price and indicators
        if not signals.empty:
            latest = signals.iloc[-1]
            
            current_price = f"${latest['close']:,.2f}"
            
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
        else:
            current_price = "Data not available"
            price_change_text = "Change: N/A"
            price_change_style = {'color': '#999', 'fontSize': '14px', 'marginBottom': '15px'}
            ema_20_value = "N/A"
            ema_50_value = "N/A"
            rsi_value = "N/A"
            macd_value = "N/A"
        
        # Latest signals
        latest_signals_components = []
        # Check recent signals (last 5 candles)
        if not signals.empty:
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
        else:
            latest_signals_components.append(
                html.Div("Data not available", style={'color': '#999', 'marginTop': '10px'})
            )
        
        # Trade history
        trade_history_components = []
        if len(trade_history) > 0:
            for trade in reversed(trade_history[-5:]):  # Show last 5 trades
                trade_type = trade['type']
                trade_price = trade['price']
                trade_time = trade['time']
                
                trade_history_components.append(
                    html.Div([
                        html.Div(trade_type, style={
                            'backgroundColor': DARK_THEME['buy'] if trade_type == 'BUY' else DARK_THEME['sell'],
                            'color': 'white',
                            'padding': '5px 10px',
                            'borderRadius': '4px',
                            'fontWeight': 'bold',
                            'display': 'inline-block',
                            'fontSize': '12px'
                        }),
                        html.Span(f" {trade['symbol']} at ${trade_price:,.2f}", style={
                            'marginLeft': '8px',
                        }),
                        html.Div(f"{trade_time}", style={
                            'color': '#999',
                            'fontSize': '12px',
                            'marginBottom': '8px'
                        })
                    ], style={'marginBottom': '8px'})
                )
        else:
            trade_history_components.append(
                html.Div("No trades executed yet", style={'color': '#999', 'marginTop': '10px'})
            )
        
        update_status = f"Updated {datetime.now().strftime('%H:%M:%S')}"
        update_status_style = {'color': DARK_THEME['buy']}
        
        return (fig, current_price, price_change_text, price_change_style, 
                ema_20_value, ema_50_value, rsi_value, macd_value,
                html.Div(latest_signals_components), html.Div(trade_history_components),
                update_status, update_status_style)
        
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