import MetaTrader5 as mt5
import os
import time

def initialize_mt5(attempts=3, delay=5):
    """
    Initialize connection to MetaTrader 5 terminal
    
    Parameters:
    attempts (int): Number of connection attempts
    delay (int): Delay between attempts in seconds
    
    Returns:
    bool: True if initialization was successful, False otherwise
    """
    # Try to find MT5 terminal path
    mt5_paths = [
        "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
        "C:\\Program Files (x86)\\MetaTrader 5\\terminal.exe",
        # Weltrade specific paths
        "C:\\Program Files\\Weltrade MT5\\terminal64.exe",
        "C:\\Program Files (x86)\\Weltrade MT5\\terminal.exe",
        # Add the actual path from your installation
        # Look for where you installed MetaTrader 5
    ]
    
    for _ in range(attempts):
        # Try direct initialization
        if mt5.initialize():
            print("MT5 connected successfully!")
            return True
            
        # Try with explicit path if direct initialization failed
        for path in mt5_paths:
            if os.path.exists(path):
                print(f"Trying to connect using path: {path}")
                if mt5.initialize(path=path):
                    print("MT5 connected successfully!")
                    return True
        
        print(f"Failed to connect to MT5. Retrying in {delay} seconds...")
        time.sleep(delay)
    
    print(f"Failed to initialize MT5 after {attempts} attempts: {mt5.last_error()}")
    return False

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

def place_order(symbol, order_type, volume, price=None, sl=None, tp=None):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price if price else mt5.symbol_info_tick(symbol).ask,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 123456,
        "comment": "Smart Flow Scalper",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to place order: {result.retcode}, {mt5.last_error()}")
        return None
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