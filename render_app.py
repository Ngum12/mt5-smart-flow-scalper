import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Check if we're in render environment
is_render = os.environ.get('DEPLOY_ENV') == 'render'

# Only try to import MT5 if we're not in render
if not is_render:
    try:
        import MetaTrader5 as mt5
    except ImportError:
        print("MetaTrader5 module not found, running in demo mode")

# Theme colors (same as your original app)
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

# Sample data generator (for demo when MT5 is not available)
def generate_demo_data():
    """Generate simulated price data"""
    dates = pd.date_range(end=datetime.now(), periods=100, freq='5min')
    
    # Start price and generate random walk
    price = 93000 + np.random.normal(0, 500)
    closes = [price]
    
    # Generate OHLC data with some volatility
    for i in range(1, 100):
        close = closes[-1] * (1 + np.random.normal(0, 0.001))
        closes.append(close)
    
    # Create price series with some randomness
    closes = np.array(closes)
    opens = closes * (1 + np.random.normal(0, 0.0005, size=len(closes)))
    highs = np.maximum(opens, closes) * (1 + abs(np.random.normal(0, 0.001, size=len(closes))))
    lows = np.minimum(opens, closes) * (1 - abs(np.random.normal(0, 0.001, size=len(closes))))
    
    # Create DataFrame
    df = pd.DataFrame({
        'time': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'tick_volume': np.random.randint(10, 100, size=len(closes)),
        'spread': np.random.randint(1, 5, size=len(closes)),
        'real_volume': np.random.randint(1000, 10000, size=len(closes))
    })
    
    # Calculate indicators (simplified versions)
    # EMA 20
    df['ema_short'] = df['close'].ewm(span=20, adjust=False).mean()
    # EMA 50
    df['ema_long'] = df['close'].ewm(span=50, adjust=False).mean()
    # RSI (simplified)
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD (simplified)
    df['macd'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # Generate some signals
    df['buy_signal'] = False
    df['sell_signal'] = False
    
    # Add some sample signals
    for i in range(10, len(df)):
        # Random buy signals when conditions roughly align with strategy
        if (df['ema_short'].iloc[i] > df['ema_long'].iloc[i] and
            df['close'].iloc[i] > df['open'].iloc[i] and
            df['rsi'].iloc[i] > 50 and df['rsi'].iloc[i] < 70 and
            df['macd'].iloc[i] > df['macd_signal'].iloc[i] and
            np.random.random() < 0.1):  # 10% chance when conditions meet
            df.loc[df.index[i], 'buy_signal'] = True
            
        # Random sell signals
        elif (df['ema_short'].iloc[i] < df['ema_long'].iloc[i] and
              df['close'].iloc[i] < df['open'].iloc[i] and
              df['rsi'].iloc[i] < 50 and df['rsi'].iloc[i] > 30 and
              df['macd'].iloc[i] < df['macd_signal'].iloc[i] and
              np.random.random() < 0.1):  # 10% chance when conditions meet
            df.loc[df.index[i], 'sell_signal'] = True
    
    return df

# Generate sample data
sample_data = generate_demo_data()

# Sample trade history
sample_trades = [
    {
        'type': 'BUY',
        'price': 93245.67,
        'time': (datetime.now() - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
        'symbol': 'GainX 800'
    },
    {
        'type': 'SELL',
        'price': 93412.32,
        'time': (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        'symbol': 'GainX 800'
    },
    {
        'type': 'BUY',
        'price': 93360.15,
        'time': (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
        'symbol': 'GainX 800'
    }
]

# Create the Dash app
app = dash.Dash(__name__, title="Smart Flow Scalper Dashboard")
server = app.server  # Needed for Render deployment

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
        html.Div("DEMO MODE - Not connected to MT5", style={
            'backgroundColor': DARK_THEME['sell'],
            'padding': '5px 10px',
            'borderRadius': '4px',
            'display': 'inline-block',
            'marginTop': '10px',
            'fontSize': '12px',
            'fontWeight': 'bold'
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
                    interval=5*1000,  # 5 seconds for demo
                    n_intervals=0
                ),
                html.Button("Refresh", id='refresh-button', style={
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
                    html.Span(id='update-status', children="Demo Mode", 
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
                html.Div(id='trade-history')
            ]),
            
            # Strategy Performance (mock data)
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
                        html.Div("65%", id='win-rate', style={'textAlign': 'right'}),
                        html.Div("Profit Factor:"),
                        html.Div("2.3", id='profit-factor', style={'textAlign': 'right'}),
                        html.Div("Total Profit:"),
                        html.Div("$1,245.80", id='total-profit', style={'textAlign': 'right'}),
                        html.Div("Max Drawdown:"),
                        html.Div("-$320.25", id='max-drawdown', style={'textAlign': 'right'}),
                    ]),
                ]),
            ]),
        ]),
    ]),
])

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
     Output('update-status', 'style'),
     Output('live-price', 'children'),
     Output('live-price', 'style')],
    [Input('interval-component', 'n_intervals'),
     Input('refresh-button', 'n_clicks')]
)
def update_dashboard(n_intervals, n_clicks):
    # Generate slightly new data each time for the demo
    global sample_data
    
    # Add a new row at the end with some random walk for price
    last_row = sample_data.iloc[-1].copy()
    new_time = last_row['time'] + timedelta(minutes=5)
    close_change = np.random.normal(0, 30)  # Add some volatility
    new_close = last_row['close'] + close_change
    
    # Create new row with randomized values
    new_row = {
        'time': new_time,
        'open': last_row['close'],  # Open at last close
        'close': new_close,
        'high': max(last_row['close'], new_close) * (1 + abs(np.random.normal(0, 0.0005))),
        'low': min(last_row['close'], new_close) * (1 - abs(np.random.normal(0, 0.0005))),
        'tick_volume': np.random.randint(10, 100),
        'spread': np.random.randint(1, 5),
        'real_volume': np.random.randint(1000, 10000),
    }
    
    # Remove oldest row and add the new one
    sample_data = pd.concat([sample_data.iloc[1:], pd.DataFrame([new_row])], ignore_index=True)
    
    # Recalculate indicators
    sample_data['ema_short'] = sample_data['close'].ewm(span=20, adjust=False).mean()
    sample_data['ema_long'] = sample_data['close'].ewm(span=50, adjust=False).mean()
    
    # RSI recalculation
    delta = sample_data['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    sample_data['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD recalculation
    sample_data['macd'] = sample_data['close'].ewm(span=12, adjust=False).mean() - sample_data['close'].ewm(span=26, adjust=False).mean()
    sample_data['macd_signal'] = sample_data['macd'].ewm(span=9, adjust=False).mean()
    sample_data['macd_hist'] = sample_data['macd'] - sample_data['macd_signal']
    
    # Reset signals
    sample_data['buy_signal'] = False
    sample_data['sell_signal'] = False
    
    # Add new signals
    for i in range(max(10, len(sample_data)-10), len(sample_data)):
        # Buy signals
        if (sample_data['ema_short'].iloc[i] > sample_data['ema_long'].iloc[i] and
            sample_data['close'].iloc[i] > sample_data['open'].iloc[i] and
            sample_data['rsi'].iloc[i] > 50 and sample_data['rsi'].iloc[i] < 70 and
            sample_data['macd'].iloc[i] > sample_data['macd_signal'].iloc[i] and
            np.random.random() < 0.05):  # Lower chance for signals
            sample_data.loc[sample_data.index[i], 'buy_signal'] = True
            
        # Sell signals
        elif (sample_data['ema_short'].iloc[i] < sample_data['ema_long'].iloc[i] and
              sample_data['close'].iloc[i] < sample_data['open'].iloc[i] and
              sample_data['rsi'].iloc[i] < 50 and sample_data['rsi'].iloc[i] > 30 and
              sample_data['macd'].iloc[i] < sample_data['macd_signal'].iloc[i] and
              np.random.random() < 0.05):  # Lower chance for signals
            sample_data.loc[sample_data.index[i], 'sell_signal'] = True
    
    # Create the chart
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        specs=[[{"type": "candlestick"}],
               [{"type": "scatter"}]]
    )
    
    # Add candlestick chart
    candlestick = go.Candlestick(
        x=sample_data['time'],
        open=sample_data['open'],
        high=sample_data['high'],
        low=sample_data['low'],
        close=sample_data['close'],
        name="Price",
        increasing_line_color=DARK_THEME['buy'],
        decreasing_line_color=DARK_THEME['sell']
    )
    fig.add_trace(candlestick, row=1, col=1)
    
    # Add EMA lines
    fig.add_trace(
        go.Scatter(
            x=sample_data['time'],
            y=sample_data['ema_short'],
            name="EMA 20",
            line=dict(color='rgba(120, 220, 110, 0.8)', width=2)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=sample_data['time'],
            y=sample_data['ema_long'],
            name="EMA 50",
            line=dict(color='rgba(255, 191, 0, 0.8)', width=2)
        ),
        row=1, col=1
    )
    
    # Add RSI
    fig.add_trace(
        go.Scatter(
            x=sample_data['time'],
            y=sample_data['rsi'],
            name="RSI",
            line=dict(color='rgba(255, 255, 255, 0.8)', width=1.5)
        ),
        row=2, col=1
    )
    
    # Add RSI levels
    fig.add_shape(
        type="line", line_color="rgba(255, 255, 255, 0.3)", line_width=1, opacity=0.8,
        x0=sample_data['time'].iloc[0], y0=70, x1=sample_data['time'].iloc[-1], y1=70,
        row=2, col=1
    )
    fig.add_shape(
        type="line", line_color="rgba(255, 255, 255, 0.3)", line_width=1, opacity=0.8,
        x0=sample_data['time'].iloc[0], y0=30, x1=sample_data['time'].iloc[-1], y1=30,
        row=2, col=1
    )
    fig.add_shape(
        type="line", line_color="rgba(255, 255, 255, 0.2)", line_width=1, opacity=0.5,
        x0=sample_data['time'].iloc[0], y0=50, x1=sample_data['time'].iloc[-1], y1=50,
        row=2, col=1
    )
    
    # Add buy/sell markers
    buy_signals = sample_data[sample_data['buy_signal'] == True]
    if len(buy_signals) > 0:
        fig.add_trace(
            go.Scatter(
                x=buy_signals['time'],
                y=buy_signals['low'] * 0.999,
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
    
    sell_signals = sample_data[sample_data['sell_signal'] == True]
    if len(sell_signals) > 0:
        fig.add_trace(
            go.Scatter(
                x=sell_signals['time'],
                y=sell_signals['high'] * 1.001,
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
        transition_duration=500,
        uirevision='same',
        xaxis=dict(
            showgrid=True,
            gridcolor=DARK_THEME['grid'],
            zeroline=False
        ),
        yaxis=dict(
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
    
    # Get current price and indicators
    latest = sample_data.iloc[-1]
    
    current_price = f"${latest['close']:,.2f}"
    
    # Calculate price change
    price_change_abs = latest['close'] - sample_data.iloc[-2]['close']
    price_change_pct = price_change_abs / sample_data.iloc[-2]['close'] * 100
    price_change_text = f"Change: {price_change_abs:+,.2f} ({price_change_pct:+,.2f}%)"
    price_change_style = {
        'color': DARK_THEME['buy'] if price_change_abs >= 0 else DARK_THEME['sell'],
        'fontSize': '14px',
        'marginBottom': '15px'
    }
    
    # Indicators
    ema_20_value = f"{latest['ema_short']:,.2f}"
    ema_50_value = f"{latest['ema_long']:,.2f}"
    rsi_value = f"{latest['rsi']:.2f}"
    macd_value = f"{latest['macd']:.2f} (Signal: {latest['macd_signal']:.2f})"
    
    # Check for recent signals
    recent_signals = sample_data.iloc[-5:]
    latest_signals_components = []
    
    buy_signal_index = None
    sell_signal_index = None
    
    if recent_signals['buy_signal'].any():
        buy_signal_index = recent_signals[recent_signals['buy_signal']].index[-1]
    
    if recent_signals['sell_signal'].any():
        sell_signal_index = recent_signals[recent_signals['sell_signal']].index[-1]
    
    if buy_signal_index is not None:
        buy_time = sample_data.loc[buy_signal_index, 'time']
        buy_price = sample_data.loc[buy_signal_index, 'close']
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
        
        # Add to demo trades
        if np.random.random() < 0.3 and len(sample_trades) < 10:  # 30% chance to add to trades
            sample_trades.append({
                'type': 'BUY',
                'price': buy_price,
                'time': buy_time.strftime("%Y-%m-%d %H:%M:%S"),
                'symbol': 'GainX 800'
            })
    
    if sell_signal_index is not None:
        sell_time = sample_data.loc[sell_signal_index, 'time']
        sell_price = sample_data.loc[sell_signal_index, 'close']
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
        
        # Add to demo trades
        if np.random.random() < 0.3 and len(sample_trades) < 10:  # 30% chance to add to trades
            sample_trades.append({
                'type': 'SELL',
                'price': sell_price,
                'time': sell_time.strftime("%Y-%m-%d %H:%M:%S"),
                'symbol': 'GainX 800'
            })
    
    if len(latest_signals_components) == 0:
        latest_signals_components.append(
            html.Div("No recent signals detected", style={'color': '#999', 'marginTop': '10px'})
        )
    
    # Trade history components
    trade_history_components = []
    for trade in reversed(sample_trades[-5:]):  # Show last 5 trades
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
    
    if len(trade_history_components) == 0:
        trade_history_components.append(
            html.Div("No trades executed yet", style={'color': '#999', 'marginTop': '10px'})
        )
    
    # Live price style
    price_color = DARK_THEME['buy'] if price_change_abs >= 0 else DARK_THEME['sell']
    live_price_style = {'fontSize': '28px', 'fontWeight': 'bold', 'color': price_color}
    live_price = f"${latest['close']:,.2f}"
    
    update_status = f"Demo Update {datetime.now().strftime('%H:%M:%S')}"
    update_status_style = {'color': DARK_THEME['accent']}
    
    return (
        fig, current_price, price_change_text, price_change_style, 
        ema_20_value, ema_50_value, rsi_value, macd_value,
        html.Div(latest_signals_components), html.Div(trade_history_components),
        update_status, update_status_style, live_price, live_price_style
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run(host='0.0.0.0', port=port)