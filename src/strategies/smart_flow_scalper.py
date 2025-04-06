import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import json
from datetime import datetime, timedelta
from ..indicators.ma_indicators import calculate_ema
from ..indicators.rsi import calculate_rsi
from ..indicators.macd import calculate_macd
from ..indicators.volume_indicators import calculate_volume_indicator
from ..indicators.volatility_indicators import calculate_atr

class SmartFlowScalper:
    def __init__(self, symbol, timeframe, lot_size=0.01, auto_optimize=True):
        self.symbol = symbol
        self.timeframe = timeframe
        self.lot_size = lot_size
        self.auto_optimize = auto_optimize
        
        # Default parameters (will be overridden if auto_optimize=True)
        self.ema_short = 20
        self.ema_long = 50
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.atr_period = 14
        self.atr_multiplier = 2.0
        self.reward_risk_ratio = 1.5
        
        # Add this line to define the missing attribute
        self.use_trailing_stop = True  # Enable trailing stops by default
        
        # Risk parameters
        self.risk_percent = 1.0  # Risk 1% of balance per trade
        
        # If auto-optimize is enabled, adjust parameters based on symbol
        if auto_optimize:
            self._optimize_for_symbol()
        
        self.logger = self._setup_logger()
        self.logger.info(f"Smart Flow Scalper initialized for {symbol} with {'auto-optimized' if auto_optimize else 'default'} parameters")
        self.logger.info(f"Parameters: EMA {self.ema_short}/{self.ema_long}, RSI {self.rsi_oversold}/{self.rsi_overbought}, ATR {self.atr_multiplier}x")

    def _optimize_for_symbol(self):
        """Optimize strategy parameters based on symbol characteristics"""
        symbol_info = self._get_symbol_type()
        
        # Load optimization history if available
        optimization_path = f"data/optimization_{self.symbol.replace(' ', '_')}.json"
        try:
            with open(optimization_path, 'r') as f:
                optimization_data = json.load(f)
                self.logger.info(f"Loaded optimization history for {self.symbol}")
        except (FileNotFoundError, json.JSONDecodeError):
            optimization_data = {"iterations": 0, "best_params": {}}
        
        # Symbol type-based optimization
        if "GainX" in self.symbol:
            # GainX series - optimize for bullish bias
            if "1200" in self.symbol:  # Extreme volatility
                self.ema_short = 10
                self.ema_long = 30
                self.rsi_overbought = 75  # Higher threshold due to bullish bias
                self.rsi_oversold = 30
                self.atr_multiplier = 2.5  # Wider stops for volatility
            elif "999" in self.symbol:  # Very high volatility
                self.ema_short = 12
                self.ema_long = 35
                self.rsi_overbought = 73
                self.rsi_oversold = 30
                self.atr_multiplier = 2.3
            elif "800" in self.symbol:  # High volatility
                self.ema_short = 15
                self.ema_long = 40
                self.rsi_overbought = 72
                self.rsi_oversold = 30
                self.atr_multiplier = 2.0
            elif "600" in self.symbol:  # Medium-high volatility
                self.ema_short = 18
                self.ema_long = 45
                self.rsi_overbought = 71
                self.rsi_oversold = 32
                self.atr_multiplier = 1.8
            else:  # 400 or other - Medium volatility
                self.ema_short = 20
                self.ema_long = 50
                self.rsi_overbought = 70
                self.rsi_oversold = 35
                self.atr_multiplier = 1.5
            
            # MACD adjustments for bullish bias
            self.macd_fast = 10
            self.macd_slow = 24
            self.macd_signal = 8
            
        elif "PainX" in self.symbol:
            # PainX series - optimize for bearish bias
            if "1200" in self.symbol:  # Extreme volatility
                self.ema_short = 10
                self.ema_long = 30
                self.rsi_overbought = 70
                self.rsi_oversold = 25  # Lower threshold due to bearish bias
                self.atr_multiplier = 2.5  # Wider stops for volatility
            elif "999" in self.symbol:  # Very high volatility
                self.ema_short = 12
                self.ema_long = 35
                self.rsi_overbought = 68
                self.rsi_oversold = 27
                self.atr_multiplier = 2.3
            elif "800" in self.symbol:  # High volatility
                self.ema_short = 15
                self.ema_long = 40
                self.rsi_overbought = 67
                self.rsi_oversold = 28
                self.atr_multiplier = 2.0
            elif "600" in self.symbol:  # Medium-high volatility
                self.ema_short = 18
                self.ema_long = 45
                self.rsi_overbought = 65
                self.rsi_oversold = 30
                self.atr_multiplier = 1.8
            else:  # 400 or other - Medium volatility
                self.ema_short = 20
                self.ema_long = 50
                self.rsi_overbought = 65
                self.rsi_oversold = 30
                self.atr_multiplier = 1.5
                
            # MACD adjustments for bearish bias
            self.macd_fast = 12
            self.macd_slow = 26
            self.macd_signal = 9
        
        # Apply any saved optimization improvements
        if optimization_data.get("best_params"):
            best_params = optimization_data["best_params"]
            # Apply optimized parameters but limit how far they can deviate
            self.ema_short = max(5, min(30, int(best_params.get("ema_short", self.ema_short))))
            self.ema_long = max(20, min(100, int(best_params.get("ema_long", self.ema_long))))
            self.rsi_overbought = max(60, min(80, best_params.get("rsi_overbought", self.rsi_overbought)))
            self.rsi_oversold = max(20, min(40, best_params.get("rsi_oversold", self.rsi_oversold)))
            
        # Save volatility info for later reference
        self.symbol_volatility = self._get_volatility_category(self.symbol)
        self.symbol_bias = "bullish" if "GainX" in self.symbol else "bearish" if "PainX" in self.symbol else "neutral"

    def _get_volatility_category(self, symbol):
        """Get volatility category based on the symbol name"""
        if "1200" in symbol:
            return "extreme"
        elif "999" in symbol:
            return "very high"
        elif "800" in symbol:
            return "high"
        elif "600" in symbol:
            return "medium-high"
        elif "400" in symbol:
            return "medium"
        else:
            return "unknown"

    def _get_symbol_type(self):
        """Determine symbol type and characteristics"""
        
        if "GainX" in self.symbol:
            bias = "bullish"
            index_type = "gain"
        elif "PainX" in self.symbol:
            bias = "bearish"
            index_type = "pain"
        else:
            bias = "neutral"
            index_type = "unknown"
        
        # Extract the number part
        try:
            number = int(''.join(filter(str.isdigit, self.symbol)))
        except:
            number = 0
        
        # Estimate volatility based on the number
        if number >= 1200:
            volatility = "extreme"
        elif number >= 999:
            volatility = "very high"
        elif number >= 800:
            volatility = "high"
        elif number >= 600:
            volatility = "medium-high"
        elif number >= 400:
            volatility = "medium"
        else:
            volatility = "low"
            
        return {
            "name": self.symbol,
            "bias": bias,
            "type": index_type,
            "number": number,
            "volatility": volatility
        }

    def _setup_logger(self):
        """Set up a logger for the strategy"""
        import logging
        import sys
        
        # Create a logger
        logger = logging.getLogger(f"smart_flow_scalper_{self.symbol}")
        logger.setLevel(logging.INFO)
        
        # Create a formatter without emoji characters for console output
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create console handler with UTF-8 encoding
        console_handler = logging.StreamHandler(stream=sys.stdout)  # Use stdout explicitly
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Add the handler to the logger
        logger.addHandler(console_handler)
        
        # Try to create a file handler if log directory exists
        try:
            import os
            log_dir = "logs"
            
            # Create log directory if it doesn't exist
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            # Create a file handler - file can handle emojis
            file_handler = logging.FileHandler(
                f"{log_dir}/smart_flow_scalper_{self.symbol.replace(' ', '_')}.log",
                encoding='utf-8'  # Specify UTF-8 encoding
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(console_formatter)
            
            # Add the handler to the logger
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to set up file logging: {e}")
        
        return logger

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
        try:
            data = self.get_data(bars=100)
            if data.empty:
                self.logger.warning(f"No data received for {self.symbol}, skipping execution")
                return

            signals = self.generate_signals(data)
            
            # Skip if we have no data
            if len(signals) == 0:
                return
            
            # First, manage existing positions (trailing stops)
            self.manage_open_positions()
            
            # Print the latest prices and indicators
            latest = signals.iloc[-1]
            self.logger.info(f"Latest data for {self.symbol} at {latest['time']}:")
            self.logger.info(f"Price: {latest['close']:.2f}")
            
            # Only print indicators if they exist and are not NaN
            if 'ema_short' in latest and not pd.isna(latest['ema_short']):
                self.logger.info(f"EMA {self.ema_short}: {latest['ema_short']:.2f}")
            if 'ema_long' in latest and not pd.isna(latest['ema_long']):
                self.logger.info(f"EMA {self.ema_long}: {latest['ema_long']:.2f}")
            if 'rsi' in latest and not pd.isna(latest['rsi']):
                self.logger.info(f"RSI: {latest['rsi']:.2f}")
            if 'macd' in latest and 'macd_signal' in latest and not pd.isna(latest['macd']) and not pd.isna(latest['macd_signal']):
                self.logger.info(f"MACD: {latest['macd']:.2f}, Signal: {latest['macd_signal']:.2f}")
            
            # Check for signals
            recent_signals = signals.iloc[-5:]  # Look at the last 5 candles for signals
            
            # Get open positions to avoid duplicate entries
            positions = mt5.positions_get(symbol=self.symbol)
            has_open_position = positions is not None and len(positions) > 0
            
            # ENHANCED: Check if we have an open position matching our strategy
            our_position = False
            if has_open_position:
                for position in positions:
                    if position.magic == 12345:  # Only check positions from our EA
                        our_position = True
                        break
            
            # ENHANCED: Only block new trades if we have our own position open
            if not our_position:  # Changed from has_open_position to our_position
                if recent_signals['buy_signal'].any() or recent_signals['sell_signal'].any():
                    # Try to close existing positions first if we're getting error 10027
                    self.close_all_positions()
                    
                    # Then proceed with opening new position
                    if recent_signals['buy_signal'].any():
                        buy_index = recent_signals[recent_signals['buy_signal']].index[-1]
                        buy_price = signals.loc[buy_index, 'close']
                        self.logger.info(f"BUY SIGNAL detected at {signals.loc[buy_index, 'time']} (price: {buy_price:.2f})")
                        
                        # Place the trade with retry logic
                        for attempt in range(3):  # Try up to 3 times
                            result = self.place_order(mt5.ORDER_TYPE_BUY)
                            if result:
                                self.logger.info(f"BUY order executed successfully after {attempt+1} attempts")
                                break
                            else:
                                self.logger.warning(f"BUY order failed, attempt {attempt+1}/3")
                                time.sleep(1)  # Wait before retry
                    
                    elif recent_signals['sell_signal'].any():
                        sell_index = recent_signals[recent_signals['sell_signal']].index[-1]
                        sell_price = signals.loc[sell_index, 'close']
                        self.logger.info(f"SELL SIGNAL detected at {signals.loc[sell_index, 'time']} (price: {sell_price:.2f})")
                        
                        # Place the trade with retry logic
                        for attempt in range(3):  # Try up to 3 times
                            result = self.place_order(mt5.ORDER_TYPE_SELL)
                            if result:
                                self.logger.info(f"SELL order executed successfully after {attempt+1} attempts")
                                break
                            else:
                                self.logger.warning(f"SELL order failed, attempt {attempt+1}/3")
                                time.sleep(1)  # Wait before retry
                    
                    else:
                        self.logger.info("No trading signals detected")
            else:
                self.logger.info(f"Skipping new entries due to existing position for {self.symbol}")
        
        except Exception as e:
            self.logger.error(f"Error in execute_trades: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def place_order(self, order_type):
        """Place a market order with dynamic position sizing"""
        action = "BUY" if order_type == mt5.ORDER_TYPE_BUY else "SELL"
        self.logger.info(f"Preparing {action} order for {self.symbol}...")
        
        try:
            # Check if autotrading is enabled
            if not mt5.terminal_info().trade_allowed:
                self.logger.error("AutoTrading is disabled in MT5! Order cannot be placed.")
                self.logger.error("Enable AutoTrading in MT5 by clicking the 'AutoTrading' button or pressing Alt+T")
                return False
                
            # Get symbol info
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                self.logger.error(f"Failed to get symbol info for {self.symbol}: {mt5.last_error()}")
                return False
                
            # Ensure the symbol is available in Market Watch
            if not symbol_info.visible:
                self.logger.info(f"Adding {self.symbol} to Market Watch...")
                if not mt5.symbol_select(self.symbol, True):
                    self.logger.error(f"Failed to select {self.symbol}: {mt5.last_error()}")
                    return False
            
            # Get the current price
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                self.logger.error(f"Failed to get current price for {self.symbol}: {mt5.last_error()}")
                return False
                
            price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
            
            # Get account info for position sizing
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.error(f"Failed to get account info: {mt5.last_error()}")
                return False
            
            # Get latest data for ATR-based stops
            data = self.get_data(bars=self.atr_period + 10)  # Get enough bars for ATR
            if len(data) == 0:
                self.logger.error("Failed to get price data for stop calculation")
                return False
            
            # Calculate ATR
            atr_value = calculate_atr(data['high'], data['low'], data['close'], self.atr_period)[-1]
            if np.isnan(atr_value):
                self.logger.warning("ATR value is NaN, using fixed pip stop instead")
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
            
            self.logger.info(f"Risk-based position sizing: {position_size:.2f} lots (risking {self.risk_percent}% = ${risk_amount:.2f})")
            
            # ENHANCED: Check if position size is too small
            if position_size < symbol_info.volume_min:
                self.logger.warning(f"Calculated position size {position_size} is below minimum {symbol_info.volume_min}, using minimum")
                position_size = symbol_info.volume_min
            
            # Convert NumPy values to Python native types
            sl = float(sl)
            tp = float(tp)
            price = float(price)
            position_size = float(position_size)
            
            # Round prices to proper digits
            sl = round(sl, symbol_info.digits)
            tp = round(tp, symbol_info.digits)
            price = round(price, symbol_info.digits)
            
            # Prepare the request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": position_size,
                "type": order_type,
                "price": price,
                "sl": sl,  # Now using Python float
                "tp": tp,  # Now using Python float
                "deviation": 20,  # maximum price deviation in points
                "magic": 12345,   # unique identifier
                "comment": "Smart Flow Scalper",
                "type_time": mt5.ORDER_TIME_GTC,  # Good Till Canceled
                "type_filling": mt5.ORDER_FILLING_FOK,  # Fill or Kill
            }
            
            # Send the order request
            self.logger.info(f"Sending order: {request}")
            result = mt5.order_send(request)
            
            # Check the result
            if result is None:
                self.logger.error(f"Order failed: MT5 returned None, error: {mt5.last_error()}")
                return False
                
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                # ENHANCED: Log detailed error for specific error codes
                error_code = result.retcode
                error_details = {
                    10004: "Trade request rejected - order already exists",
                    10006: "Trade request rejected - no connection to trade server",
                    10007: "Trade request rejected - invalid price",
                    10008: "Trade request rejected - invalid stops",
                    10009: "Trade request rejected - order was disabled",
                    10010: "Trade request rejected - not enough money",
                    10011: "Trade request rejected - selling prohibited",
                    10013: "Trade request rejected - trading disabled",
                    10014: "Trade request rejected - not enough money",
                    10015: "Trade request rejected - buying prohibited",
                    10016: "Trade request rejected - insufficient margin",
                    10017: "Trade request rejected - order limit reached",
                    10018: "Trade request rejected - market closed",
                    10019: "Trade request rejected - hedging prohibited",
                    10020: "Trade request rejected - order prohibited by FIFO rule",
                    10021: "Trade request rejected - volume too small",
                    10022: "Trade request rejected - requote",
                    10023: "Trade request rejected - order locked",
                    10026: "Trade request rejected - volume limit exceeded",
                    10027: "Trade request rejected - position would exceed maximum positions"
                }
                
                error_description = error_details.get(error_code, "Unknown error")
                
                self.logger.error(f"Order failed: {error_code} - {error_description}")
                self.logger.error(f"MT5 error details: {mt5.last_error()}")
                self.logger.error(f"Result info: comment={result.comment}, request_id={result.request_id}")
                
                return False
            else:
                self.logger.info(f"Order placed successfully: {action} {position_size} lot(s) of {self.symbol} at {price}")
                self.logger.info(f"Stop Loss: {sl}, Take Profit: {tp} (ATR: {atr_value:.2f})")
                
                # Add notification here
                self.send_notification(f"{action} SIGNAL: {self.symbol} at {price}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error in place_order: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

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

    def close_all_positions(self):
        """Close all positions for this symbol"""
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None or len(positions) == 0:
            return True
        
        success = True
        for position in positions:
            # Skip positions not created by our EA
            if position.magic != 12345:
                continue
                
            order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
            
            # Create the request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": position.ticket,
                "price": 0.0,  # Market order
                "deviation": 20,
                "magic": 12345,
                "comment": "Smart Flow Scalper Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            # Send the order
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Failed to close position {position.ticket}: {result.retcode}")
                success = False
            else:
                self.logger.info(f"Successfully closed position {position.ticket}")
        
        return success

    def run(self):
        """Run the trading strategy continuously"""
        self.logger.info(f"Starting Smart Flow Scalper strategy for {self.symbol}...")
        try:
            # Check MT5 connection first
            if not mt5.initialize():
                self.logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                self.logger.info("Attempting to reconnect...")
                for i in range(3):
                    if mt5.initialize():
                        self.logger.info("MT5 reconnected successfully!")
                        break
                    time.sleep(5)
                else:
                    self.logger.error("Failed to reconnect to MT5 after 3 attempts. Exiting.")
                    return
            
            # Execute trades once initially
            self.execute_trades()
            
            # Run the strategy in a loop
            check_count = 0
            while True:
                # Sleep less time to be more responsive
                time.sleep(20)  # Check every 20 seconds instead of 60
                
                check_count += 1
                if check_count % 3 == 0:  # Full check every minute
                    self.logger.info("\nRunning full signal check...")
                    self.execute_trades()
                else:
                    # Quick position management check more frequently
                    self.manage_open_positions()
                    
        except KeyboardInterrupt:
            self.logger.info("Strategy stopped manually.")
        except Exception as e:
            self.logger.error(f"Error in Smart Flow Scalper: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

def check_max_positions():
    """Check if we've reached the maximum allowed positions"""
    # Get account info
    account_info = mt5.account_info()
    
    # Get all open positions
    positions = mt5.positions_get()
    if positions is None:
        return False, 0, "Failed to get positions"
    
    # Count positions
    position_count = len(positions)
    
    # Check if we've reached the limit (usually around 100-200 positions based on broker)
    max_positions = 100  # Default assumption - adjust based on your broker
    
    # Try to get the actual limit from account info if available
    if hasattr(account_info, 'limit_positions'):
        max_positions = account_info.limit_positions
    
    is_max_reached = position_count >= max_positions
    
    return is_max_reached, position_count, f"{position_count}/{max_positions}"

# Add this check in your execute_trades function:
def execute_trades(self):
    # ... existing code ...
    
    # Check maximum positions before placing orders
    max_reached, count, positions_info = check_max_positions()
    if max_reached:
        self.logger.warning(f"Maximum positions reached ({positions_info}). Cannot open new positions.")
        return
    
    # ... rest of your code ...