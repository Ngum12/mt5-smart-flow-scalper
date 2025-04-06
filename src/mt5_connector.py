import MetaTrader5 as mt5
import os
import time
import pandas as pd

def initialize_mt5():
    """Initialize MT5 connection with proper checks"""
    import MetaTrader5 as mt5
    
    print("Initializing MT5 connection...")
    # Initialize MT5
    if not mt5.initialize():
        print(f"Failed to initialize MT5: {mt5.last_error()}")
        return False
    
    # Check if AutoTrading is enabled
    if not mt5.terminal_info().trade_allowed:
        print("⚠️ WARNING: AutoTrading is DISABLED in MT5 terminal!")
        print("Please enable AutoTrading in MetaTrader 5:")
        print("1. Click the 'AutoTrading' button in the toolbar (or press Alt+T)")
        print("2. Make sure the button is highlighted and shows 'AutoTrading Enabled'")
        print("3. Check that your EA has proper permissions in MT5 settings")
        
        # You can try to enable it programmatically, but user action is more reliable
        try:
            # Try to enable autotrading (may not work depending on MT5 security settings)
            import ctypes
            user32 = ctypes.windll.user32
            # Simulate Alt+T keystroke - this attempts to toggle AutoTrading
            # Note: This may not work on all systems due to security restrictions
            user32.keybd_event(0x12, 0, 0, 0)  # ALT key down
            user32.keybd_event(0x54, 0, 0, 0)  # T key down
            user32.keybd_event(0x54, 0, 0x2, 0)  # T key up
            user32.keybd_event(0x12, 0, 0x2, 0)  # ALT key up
            
            # Check if it worked
            import time
            time.sleep(1)
            if mt5.terminal_info().trade_allowed:
                print("✅ AutoTrading successfully enabled!")
            else:
                print("❌ Failed to enable AutoTrading automatically.")
                print("Please enable it manually using the steps above.")
        except Exception as e:
            print(f"Error trying to enable AutoTrading: {e}")
            print("Please enable it manually.")
    
    # Check account information
    account_info = mt5.account_info()
    if account_info is None:
        print(f"Failed to get account info: {mt5.last_error()}")
        return False
    
    print(f"Connected to MT5 - Account: {account_info.login} ({account_info.company})")
    print(f"Balance: ${account_info.balance:.2f}, Equity: ${account_info.equity:.2f}")
    
    return True

def shutdown_mt5():
    mt5.shutdown()

def get_account_info():
    account_info = mt5.account_info()
    if account_info is None:
        print(f"Failed to get account info: {mt5.last_error()}")
        return None
    return account_info

def get_symbol_info(symbol):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Failed to get symbol info for {symbol}: {mt5.last_error()}")
        return None
    return symbol_info

def get_last_tick(symbol):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"Failed to get last tick for {symbol}: {mt5.last_error()}")
        return None
    return tick

def get_symbol_type(symbol):
    """
    Determine the type of the symbol based on its name
    
    Parameters:
    symbol (str): Symbol name
    
    Returns:
    dict: Information about symbol type and characteristics
    """
    if "GainX" in symbol:
        bias = "bullish"
        index_type = "gain"
    elif "PainX" in symbol:
        bias = "bearish"
        index_type = "pain"
    else:
        bias = "neutral"
        index_type = "unknown"
    
    # Extract the number part (e.g., 800 from GainX 800)
    try:
        number = int(''.join(filter(str.isdigit, symbol)))
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
        "name": symbol,
        "bias": bias,
        "type": index_type,
        "number": number,
        "volatility": volatility
    }

# Enhance the place_order function with symbol-aware adjustments
def place_order(symbol, order_type, volume, price=None, sl=None, tp=None, auto_adjust=True):
    """
    Place an order with symbol-specific adjustments
    
    Parameters:
    symbol (str): Symbol name
    order_type (int): Order type (BUY/SELL)
    volume (float): Trade volume in lots
    price (float, optional): Order price
    sl (float, optional): Stop loss price
    tp (float, optional): Take profit price
    auto_adjust (bool): Whether to adjust parameters based on symbol characteristics
    
    Returns:
    object: Order result
    """
    # Get symbol info
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Failed to get symbol info for {symbol}: {mt5.last_error()}")
        return None
    
    # Get tick info
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"Failed to get tick info for {symbol}: {mt5.last_error()}")
        return None
    
    # Set price based on order type if not specified
    entry_price = price
    if entry_price is None:
        entry_price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
    
    # If auto-adjust is enabled, modify parameters based on symbol characteristics
    if auto_adjust:
        symbol_type = get_symbol_type(symbol)
        
        # Adjust volume based on volatility
        if symbol_type["volatility"] == "extreme":
            volume = min(volume, 0.01)  # Cap at 0.01 for extreme volatility
        elif symbol_type["volatility"] == "very high":
            volume = min(volume, 0.03)  # Cap at 0.03 for very high volatility
            
        # Auto-calculate SL/TP if not provided
        point = symbol_info.point
        digits = symbol_info.digits
        
        if sl is None or tp is None:
            # Base stop loss and take profit distances on volatility
            if symbol_type["volatility"] == "extreme":
                sl_pips = 300  # Wide stop loss for extreme volatility
                tp_pips = 450  # 1.5:1 reward:risk ratio
            elif symbol_type["volatility"] == "very high":
                sl_pips = 200
                tp_pips = 300
            elif symbol_type["volatility"] == "high":
                sl_pips = 150
                tp_pips = 225
            elif symbol_type["volatility"] == "medium-high":
                sl_pips = 100
                tp_pips = 150
            else:
                sl_pips = 80
                tp_pips = 120
                
            # Convert pips to price levels
            sl_distance = sl_pips * point
            tp_distance = tp_pips * point
            
            # Set SL and TP based on order type
            if sl is None:
                if order_type == mt5.ORDER_TYPE_BUY:
                    sl = round(entry_price - sl_distance, digits)
                else:
                    sl = round(entry_price + sl_distance, digits)
                    
            if tp is None:
                if order_type == mt5.ORDER_TYPE_BUY:
                    tp = round(entry_price + tp_distance, digits)
                else:
                    tp = round(entry_price - tp_distance, digits)
    
    # Create order request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": entry_price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 123456,
        "comment": "Smart Flow Scalper",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    # Send order
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to place order: {result.retcode}, {mt5.last_error()}")
        return None
    
    print(f"Order placed successfully: {symbol} {'BUY' if order_type == mt5.ORDER_TYPE_BUY else 'SELL'} {volume} lots at {entry_price}, SL: {sl}, TP: {tp}")
    return result

def get_open_positions():
    positions = mt5.positions_get()
    if positions is None:
        print(f"Failed to get open positions: {mt5.last_error()}")
        return []
    return positions

def close_position(ticket):
    position = mt5.positions_get(ticket=ticket)
    if position is None or len(position) == 0:
        print(f"Position with ticket {ticket} not found.")
        return False

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": ticket,
        "volume": position[0].volume,
        "type": mt5.ORDER_SELL if position[0].type == mt5.ORDER_BUY else mt5.ORDER_BUY,
        "deviation": 10,
        "magic": 123456,
        "comment": "Closing position",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to close position: {result.retcode}, {mt5.last_error()}")
        return False
    return True

def get_candles(symbol, timeframe, count=100):
    """
    Get candlestick data for a specific symbol and timeframe
    
    Parameters:
    symbol (str): Symbol name
    timeframe (int): MT5 timeframe constant (e.g., mt5.TIMEFRAME_M5)
    count (int): Number of candles to fetch
    
    Returns:
    pandas.DataFrame: Candlestick data with columns: time, open, high, low, close, volume, etc.
    """
    # Make sure the symbol is available in Market Watch
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Symbol {symbol} not found")
        return pd.DataFrame()
        
    # If the symbol is not visible in Market Watch, add it
    if not symbol_info.visible:
        print(f"Adding {symbol} to Market Watch...")
        if not mt5.symbol_select(symbol, True):
            print(f"Failed to select {symbol}")
            return pd.DataFrame()
    
    # Get the rates
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        print(f"No data available for {symbol}")
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(rates)
    
    # Convert time in seconds into datetime
    if len(df) > 0:
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
    return df