import MetaTrader5 as mt5
import pandas as pd
import threading
import time
from src.mt5_connector import initialize_mt5
from src.strategies.smart_flow_scalper import SmartFlowScalper
from src.dashboard.app_new import run_dashboard

def list_available_symbols():
    """List symbols available in MT5"""
    print("Available symbols:")
    symbols = mt5.symbols_get()
    for symbol in symbols:
        print(f"- {symbol.name}")
        
    # Look specifically for gold-related symbols
    print("\nGold-related symbols:")
    gold_symbols = [sym.name for sym in symbols if "GOLD" in sym.name or "XAU" in sym.name]
    for symbol in gold_symbols:
        print(f"- {symbol}")

def main(with_dashboard=True):
    # Initialize MT5
    if not initialize_mt5():
        print("Failed to initialize MT5. Exiting.")
        return
    
    # Define available symbols
    symbols = [
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
    
    # Create a strategy instance for each symbol
    strategies = {}
    for symbol in symbols:
        strategies[symbol] = SmartFlowScalper(
            symbol=symbol,
            timeframe=mt5.TIMEFRAME_M5,
            auto_optimize=True  # Auto-optimize parameters based on symbol
        )
    
    # Start the dashboard in a separate thread if enabled
    if with_dashboard:
        dashboard_thread = threading.Thread(target=run_dashboard)
        dashboard_thread.daemon = True
        dashboard_thread.start()
        print("Dashboard started in background thread")
    
    # Run all strategies in a loop
    try:
        while True:
            for symbol, strategy in strategies.items():
                try:
                    print(f"\nChecking {symbol}...")
                    strategy.execute_trades()
                except Exception as e:
                    print(f"Error executing trades for {symbol}: {e}")
            
            # Sleep between checks
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("Strategy execution stopped by user")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    import sys
    with_dashboard = "--no-dashboard" not in sys.argv
    main(with_dashboard)