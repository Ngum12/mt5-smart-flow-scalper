import MetaTrader5 as mt5
import os
import sys

# Print Python version and architecture
print(f"Python version: {sys.version}")
print(f"Python architecture: {platform.architecture()[0]}")

# Try different initialization approaches
print("Trying direct initialization...")
if mt5.initialize():
    print("MT5 connected successfully!")
    account_info = mt5.account_info()
    if account_info is not None:
        print(f"Account: {account_info.login}, Balance: {account_info.balance}")
    mt5.shutdown()
else:
    print(f"Failed: {mt5.last_error()}")

    # Try with explicit path
    path = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"  # Update this path
    print(f"Trying with explicit path: {path}")
    if os.path.exists(path):
        if mt5.initialize(path=path):
            print("MT5 connected successfully with explicit path!")
            mt5.shutdown()
        else:
            print(f"Failed with explicit path: {mt5.last_error()}")
    else:
        print(f"Path does not exist: {path}")