import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from ..indicators.ma_indicators import calculate_ema
from ..indicators.rsi import calculate_rsi
from ..indicators.macd import calculate_macd
from ..indicators.volume_indicators import calculate_volume_indicator
from ..indicators.volatility_indicators import calculate_atr

class SmartFlowScalper:
    def __init__(self, symbol, timeframe, lot_size):
        self.symbol = symbol
        self.timeframe = timeframe
        self.lot_size = lot_size
        
        # Strategy parameters
        self.ema_short = 20
        self.ema_long = 50
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.rsi_middle = 50
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        # Risk management parameters
        self.risk_percent = 1.0        # Risk 1% of account per trade
        self.atr_period = 14           # Period for ATR calculation
        self.atr_multiplier = 2.0      # Multiple of ATR for stop loss
        self.reward_risk_ratio = 2.0   # Reward to risk ratio
        self.use_trailing_stop = True  # Enable trailing stops
        
        print(f"Smart Flow Scalper initialized for {symbol} on M{timeframe} timeframe")

    def get_data(self, bars=100):
        """Get historical data for the symbol"""
        # Make sure the symbol is available in Market Watch
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            print(f"Symbol {self.symbol} not found")
            return pd.DataFrame()
            
        # If the symbol is not visible in Market Watch, add it
        if not symbol_info.visible:
            print(f"Adding {self.symbol} to Market Watch...")
            if not mt5.symbol_select(self.symbol, True):
                print(f"Failed to select {self.symbol}")
                return pd.DataFrame()
        
        # Get the rates
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, bars)
        if rates is None or len(rates) == 0:
            print(f"No data available for {self.symbol}")
            return pd.DataFrame()
    
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        
        # Convert time in seconds into datetime
        if len(df) > 0:
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
        return df

    def generate_signals(self, data):
        """Generate trading signals based on the Smart Flow Scalper strategy"""
        if len(data) == 0:
            print(f"Warning: No data received for {self.symbol}")
            return pd.DataFrame()
            
        # Print column names to debug
        print(f"Available columns: {data.columns.tolist()}")
        
        # Calculate indicators
        data['ema_short'] = calculate_ema(data['close'], self.ema_short)  # EMA 20
        data['ema_long'] = calculate_ema(data['close'], self.ema_long)    # EMA 50
        data['rsi'] = calculate_rsi(data['close'], self.rsi_period)
        data['macd'], data['macd_signal'], data['macd_hist'] = calculate_macd(
            data['close'], self.macd_fast, self.macd_slow, self.macd_signal
        )
        
        # Calculate ATR for dynamic stops
        data['atr'] = calculate_atr(data['high'], data['low'], data['close'], self.atr_period)
        
        # Initialize signal columns
        data['buy_signal'] = False
        data['sell_signal'] = False
        
        # Calculate crossovers and pullbacks
        data['ema_crossover_bullish'] = (data['ema_short'] > data['ema_long']) & (data['ema_short'].shift(1) <= data['ema_long'].shift(1))
        data['ema_crossover_bearish'] = (data['ema_short'] < data['ema_long']) & (data['ema_short'].shift(1) >= data['ema_long'].shift(1))
        
        # Loop through data to find setup conditions (skip first few rows where indicators might be NaN)
        valid_start = max(self.ema_long, self.macd_slow + self.macd_signal)  # Skip until all indicators have valid values
        for i in range(valid_start, len(data)-1):
            # Skip if any indicator is NaN
            if (np.isnan(data['ema_short'].iloc[i]) or 
                np.isnan(data['ema_long'].iloc[i]) or 
                np.isnan(data['rsi'].iloc[i]) or 
                np.isnan(data['macd'].iloc[i]) or 
                np.isnan(data['macd_signal'].iloc[i])):
                continue
                
            # BUY SETUP - "Smart Bull Push"
            if (
                # EMA 20 above EMA 50 (bullish trend)
                data['ema_short'].iloc[i] > data['ema_long'].iloc[i] and
                # Price pulled back and bounced from EMA 20 or EMA 50
                (
                    (data['low'].iloc[i] <= data['ema_short'].iloc[i] and data['close'].iloc[i] > data['ema_short'].iloc[i]) or
                    (data['low'].iloc[i] <= data['ema_long'].iloc[i] and data['close'].iloc[i] > data['ema_long'].iloc[i])
                ) and
                # RSI is above 50 but below 70 (not overbought)
                data['rsi'].iloc[i] > 50 and data['rsi'].iloc[i] < 70 and
                # Bullish candle pattern (green candle)
                data['close'].iloc[i] > data['open'].iloc[i] and
                # MACD confirmation
                data['macd'].iloc[i] > data['macd_signal'].iloc[i]
            ):
                data.loc[data.index[i], 'buy_signal'] = True
                
            # SELL SETUP - "Smart Bear Drop"
            elif (
                # EMA 20 below EMA 50 (bearish trend)
                data['ema_short'].iloc[i] < data['ema_long'].iloc[i] and
                # Price pulled back and rejected EMA 20 or EMA 50
                (
                    (data['high'].iloc[i] >= data['ema_short'].iloc[i] and data['close'].iloc[i] < data['ema_short'].iloc[i]) or
                    (data['high'].iloc[i] >= data['ema_long'].iloc[i] and data['close'].iloc[i] < data['ema_long'].iloc[i])
                ) and
                # RSI is below 50, ideally in the 35-45 range
                data['rsi'].iloc[i] < 50 and data['rsi'].iloc[i] > 35 and
                # Bearish candle pattern (red candle)
                data['close'].iloc[i] < data['open'].iloc[i] and
                # MACD confirmation
                data['macd'].iloc[i] < data['macd_signal'].iloc[i]
            ):
                data.loc[data.index[i], 'sell_signal'] = True
        
        return data

    def execute_trades(self):
        """Execute trades based on the generated signals"""
        data = self.get_data(bars=100)
        signals = self.generate_signals(data)
        
        # Skip if we have no data
        if len(signals) == 0:
            return
        
        # First, manage existing positions (trailing stops)
        self.manage_open_positions()
        
        # Print the latest prices and indicators
        latest = signals.iloc[-1]
        print(f"\nLatest data for {self.symbol} at {latest['time']}:")
        print(f"Price: {latest['close']:.2f}")
        
        # Only print indicators if they exist and are not NaN
        if 'ema_short' in latest and not pd.isna(latest['ema_short']):
            print(f"EMA 20: {latest['ema_short']:.2f}")
        if 'ema_long' in latest and not pd.isna(latest['ema_long']):
            print(f"EMA 50: {latest['ema_long']:.2f}")
        if 'rsi' in latest and not pd.isna(latest['rsi']):
            print(f"RSI: {latest['rsi']:.2f}")
        if 'macd' in latest and 'macd_signal' in latest and not pd.isna(latest['macd']) and not pd.isna(latest['macd_signal']):
            print(f"MACD: {latest['macd']:.2f}, Signal: {latest['macd_signal']:.2f}")
        
        # Check for signals
        recent_signals = signals.iloc[-5:]  # Look at the last 5 candles for signals
        
        # Get open positions to avoid duplicate entries
        positions = mt5.positions_get(symbol=self.symbol)
        has_open_position = positions is not None and len(positions) > 0
        
        if not has_open_position:  # Only enter new trades if we don't have an open position
            if recent_signals['buy_signal'].any():
                buy_index = recent_signals[recent_signals['buy_signal']].index[-1]
                buy_price = signals.loc[buy_index, 'close']
                print(f"\n🟢 BUY SIGNAL detected at {signals.loc[buy_index, 'time']} (price: {buy_price:.2f})")
                self.place_order(mt5.ORDER_TYPE_BUY)
            
            elif recent_signals['sell_signal'].any():
                sell_index = recent_signals[recent_signals['sell_signal']].index[-1]
                sell_price = signals.loc[sell_index, 'close']
                print(f"\n🔴 SELL SIGNAL detected at {signals.loc[sell_index, 'time']} (price: {sell_price:.2f})")
                self.place_order(mt5.ORDER_TYPE_SELL)
            
            else:
                print("\nNo trading signals detected")
        else:
            print("\nSkipping new entries due to existing position")

    def place_order(self, order_type):
        """Place a market order with dynamic position sizing"""
        action = "BUY" if order_type == mt5.ORDER_TYPE_BUY else "SELL"
        print(f"Preparing {action} order for {self.symbol}...")
        
        # Get symbol info
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            print(f"Failed to get symbol info for {self.symbol}")
            return
            
        # Ensure the symbol is available in Market Watch
        if not symbol_info.visible:
            if not mt5.symbol_select(self.symbol, True):
                print(f"Failed to select {self.symbol}")
                return
        
        # Get the current price
        tick = mt5.symbol_info_tick(self.symbol)
        price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
        
        # Get account info for position sizing
        account_info = mt5.account_info()
        if account_info is None:
            print("Failed to get account info")
            return
        
        # Get latest data for ATR-based stops
        data = self.get_data(bars=self.atr_period + 10)  # Get enough bars for ATR
        if len(data) == 0:
            print("Failed to get price data for stop calculation")
            return
        
        # Calculate ATR
        atr_value = calculate_atr(data['high'], data['low'], data['close'], self.atr_period)[-1]
        if np.isnan(atr_value):
            print("ATR value is NaN, using fixed pip stop instead")
            atr_value = 30 * symbol_info.point  # Default to 30 pips
        
        # Calculate dynamic stop loss in price terms
        stop_distance = self.atr_multiplier * atr_value
        
        # Set stop loss and take profit levels
        if order_type == mt5.ORDER_TYPE_BUY:
            sl = price - stop_distance
            tp = price + (stop_distance * self.reward_risk_ratio)
        else:
            sl = price + stop_distance
            tp = price - (stop_distance * self.reward_risk_ratio)
        
        # Calculate position size based on risk percentage
        risk_amount = account_info.balance * (self.risk_percent / 100)
        stop_distance_pips = stop_distance / symbol_info.point
        
        # Value per pip calculation
        pip_value = symbol_info.trade_tick_value * (symbol_info.trade_tick_size / symbol_info.point)
        
        # Position size in lots
        if stop_distance_pips > 0 and pip_value > 0:
            position_size = risk_amount / (stop_distance_pips * pip_value)
            # Round to nearest lot step
            position_size = round(position_size / symbol_info.volume_step) * symbol_info.volume_step
            # Apply minimum and maximum lot size constraints
            position_size = max(min(position_size, symbol_info.volume_max), symbol_info.volume_min)
        else:
            position_size = self.lot_size  # Fallback to fixed lot size
        
        print(f"Risk-based position sizing: {position_size:.2f} lots (risking {self.risk_percent}% = ${risk_amount:.2f})")
        
        # Prepare the request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": position_size,
            "type": order_type,
            "price": price,
            "sl": round(sl, symbol_info.digits),  # Stop Loss
            "tp": round(tp, symbol_info.digits),  # Take Profit
            "deviation": 20,  # maximum price deviation in points
            "magic": 12345,   # unique identifier
            "comment": "Smart Flow Scalper",
            "type_time": mt5.ORDER_TIME_GTC,  # Good Till Canceled
        }
        
        # Send the order request
        result = mt5.order_send(request)
        
        # Check the result
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order failed: {result.retcode, mt5.last_error()}")
        else:
            print(f"Order placed successfully: {action} {position_size} lot(s) of {self.symbol} at {price}")
            print(f"Stop Loss: {sl}, Take Profit: {tp} (ATR: {atr_value:.2f})")
            
            # Add notification here
            self.send_notification(f"{action} SIGNAL: {self.symbol} at {price}")

    def send_notification(self, message):
        """Send notification of signal (can be extended to email/SMS/etc)"""
        print(f"\n🔔 ALERT: {message}")
        # You could add email or other notification methods here

    def manage_open_positions(self):
        """Manage open positions with trailing stops"""
        if not self.use_trailing_stop:
            return
            
        # Get open positions
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None or len(positions) == 0:
            return
            
        # Get latest data for ATR calculation
        data = self.get_data(bars=self.atr_period + 10)
        if len(data) == 0:
            return
            
        # Current ATR value for trailing stop distance
        atr_value = calculate_atr(data['high'], data['low'], data['close'], self.atr_period)[-1]
        if np.isnan(atr_value):
            return
            
        # Current price
        tick = mt5.symbol_info_tick(self.symbol)
        
        # Process each position
        for position in positions:
            # Only manage positions from this EA
            if position.magic != 12345:
                continue
                
            # Calculate trailing stop level
            trailing_distance = self.atr_multiplier * atr_value
            
            # For buy positions
            if position.type == mt5.POSITION_TYPE_BUY:
                # New stop level based on current price - trailing distance
                new_stop = tick.bid - trailing_distance
                # Only move stop if it would be higher than current stop
                if new_stop > position.sl and tick.bid > position.price:
                    self.modify_position_sl(position.ticket, new_stop)
                    
            # For sell positions
            elif position.type == mt5.POSITION_TYPE_SELL:
                # New stop level based on current price + trailing distance
                new_stop = tick.ask + trailing_distance
                # Only move stop if it would be lower than current stop
                if (new_stop < position.sl or position.sl == 0) and tick.ask < position.price:
                    self.modify_position_sl(position.ticket, new_stop)

    def modify_position_sl(self, ticket, new_sl):
        """Modify a position's stop loss"""
        # Get position info
        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            print(f"Position {ticket} not found")
            return
            
        position = position[0]
        
        # Prepare request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": position.ticket,
            "sl": new_sl,
            "tp": position.tp,
        }
        
        # Send request
        result = mt5.order_send(request)
        
        # Check result
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to modify SL: {result.retcode, mt5.last_error()}")
        else:
            print(f"Trailing stop moved to {new_sl:.2f} for position {ticket}")

    def run(self):
        """Run the trading strategy continuously"""
        print(f"Starting Smart Flow Scalper strategy for {self.symbol}...")
        try:
            # Execute trades once initially
            self.execute_trades()
            
            # Run the strategy in a loop
            while True:
                time.sleep(60)  # Wait 1 minute between checks
                print("\nChecking for new signals...")
                self.execute_trades()
                self.manage_open_positions()
                
        except KeyboardInterrupt:
            print("Strategy stopped manually.")
        except Exception as e:
            print(f"Error in Smart Flow Scalper: {e}")
            import traceback
            traceback.print_exc()