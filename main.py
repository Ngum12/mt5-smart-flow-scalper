import MetaTrader5 as mt5
import pandas as pd
from src.mt5_connector import initialize_mt5
from src.strategies.smart_flow_scalper import SmartFlowScalper
from src.dashboard.app import run_dashboard

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
    # Initialize connection to MetaTrader 5
    if not initialize_mt5():
        print("Failed to initialize MT5. Exiting...")
        return

    # Create an instance of the Smart Flow Scalper strategy
    scalper = SmartFlowScalper(
        symbol="GainX 800",
        timeframe=mt5.TIMEFRAME_M5,
        lot_size=0.01
    )

    # Run the trading strategy
    if not with_dashboard:
        scalper.run()  # Run strategy in continuous mode
    else:
        # Just run it once if dashboard will be handling updates
        scalper.execute_trades()
        print("Starting dashboard at http://127.0.0.1:8050")
        print("(If browser doesn't open, copy this URL manually)")
        run_dashboard()  # Run the dashboard, which handles strategy updates

if __name__ == "__main__":
    import sys
    with_dashboard = "--no-dashboard" not in sys.argv
    main(with_dashboard)