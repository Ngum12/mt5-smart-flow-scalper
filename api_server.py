from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import threading
import time
import traceback
import MetaTrader5 as mt5
from src.strategies.smart_flow_scalper import SmartFlowScalper

app = Flask(__name__)
CORS(app)  # Enable CORS to allow requests from your Render app

# Initialize connection to MT5 and strategy
strategy = None
trade_history = []
background_thread = None
running = False

def initialize():
    global strategy, running
    
    if not mt5.initialize():
        return False, "Failed to initialize MT5"
    
    print("MT5 connected successfully!")
    
    try:
        strategy = SmartFlowScalper(
            symbol="GainX 800", 
            timeframe=mt5.TIMEFRAME_M5,
            lot_size=0.01
        )
        running = True
        return True, "MT5 and strategy initialized successfully"
    except Exception as e:
        return False, f"Error initializing strategy: {str(e)}"

def background_strategy_runner():
    global strategy, trade_history, running
    
    while running:
        try:
            # Execute trades and generate signals
            if strategy:
                data = strategy.get_data(bars=100)
                signals = strategy.generate_signals(data)
                
                # Check for new signals in the last 5 candles
                if len(signals) > 5:
                    recent = signals.iloc[-5:]
                    
                    # Record buy signals
                    if recent['buy_signal'].any():
                        buy_index = recent[recent['buy_signal']].index[-1]
                        trade_history.append({
                            'type': 'BUY',
                            'price': signals.loc[buy_index, 'close'],
                            'time': signals.loc[buy_index, 'time'].strftime("%Y-%m-%d %H:%M:%S"),
                            'symbol': strategy.symbol
                        })
                        print(f"BUY signal recorded at {signals.loc[buy_index, 'time']}")
                    
                    # Record sell signals
                    if recent['sell_signal'].any():
                        sell_index = recent[recent['sell_signal']].index[-1]
                        trade_history.append({
                            'type': 'SELL',
                            'price': signals.loc[sell_index, 'close'],
                            'time': signals.loc[sell_index, 'time'].strftime("%Y-%m-%d %H:%M:%S"),
                            'symbol': strategy.symbol
                        })
                        print(f"SELL signal recorded at {signals.loc[sell_index, 'time']}")
                    
                # Limit trade history
                if len(trade_history) > 50:
                    trade_history = trade_history[-50:]
            
            time.sleep(10)  # Check every 10 seconds
        except Exception as e:
            print(f"Error in background runner: {str(e)}")
            traceback.print_exc()
            time.sleep(30)  # Wait longer after error

@app.route('/api/start', methods=['POST'])
def start_strategy():
    global background_thread, running
    
    success, message = initialize()
    if not success:
        return jsonify({'success': False, 'message': message})
    
    if background_thread is None or not background_thread.is_alive():
        running = True
        background_thread = threading.Thread(target=background_strategy_runner)
        background_thread.daemon = True
        background_thread.start()
        return jsonify({'success': True, 'message': 'Strategy started'})
    else:
        return jsonify({'success': True, 'message': 'Strategy already running'})

@app.route('/api/stop', methods=['POST'])
def stop_strategy():
    global running
    running = False
    mt5.shutdown()
    return jsonify({'success': True, 'message': 'Strategy stopped'})

@app.route('/api/status', methods=['GET'])
def get_status():
    global running, background_thread
    if background_thread is not None and background_thread.is_alive() and running:
        status = "running"
    else:
        status = "stopped"
    return jsonify({'status': status})

@app.route('/api/data', methods=['GET'])
def get_data():
    global strategy
    
    if not strategy:
        return jsonify({'success': False, 'message': 'Strategy not initialized'})
    
    try:
        # Fetch the latest data
        data = strategy.get_data(bars=100)
        signals = strategy.generate_signals(data)
        
        # Get the latest candle
        latest = signals.iloc[-1]
        
        # Format data for response
        response = {
            'success': True,
            'data': {
                'time': latest['time'].strftime("%Y-%m-%d %H:%M:%S"),
                'open': float(latest['open']),
                'high': float(latest['high']),
                'low': float(latest['low']),
                'close': float(latest['close']),
                'ema_short': float(latest['ema_short']),
                'ema_long': float(latest['ema_long']),
                'rsi': float(latest['rsi']),
                'macd': float(latest['macd']),
                'macd_signal': float(latest['macd_signal']),
                'buy_signal': bool(latest['buy_signal']),
                'sell_signal': bool(latest['sell_signal']),
            },
            'chart_data': signals.tail(100).to_dict(orient='records'),
            'trades': trade_history[-10:],  # Last 10 trades
        }
        
        # Convert times to strings for JSON serialization
        for item in response['chart_data']:
            if isinstance(item['time'], pd.Timestamp):
                item['time'] = item['time'].strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify(response)
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error fetching data: {str(e)}'})

if __name__ == '__main__':
    # Start the API server on a specific port
    app.run(host='0.0.0.0', port=5000, debug=False)