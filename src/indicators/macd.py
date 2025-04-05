import numpy as np
import pandas as pd

def calculate_macd(close_prices, fast_period=12, slow_period=26, signal_period=9):
    """
    Calculate the MACD indicator
    
    Parameters:
    close_prices (array): Array of close prices
    fast_period (int): Period for the fast EMA
    slow_period (int): Period for the slow EMA
    signal_period (int): Period for the signal line
    
    Returns:
    tuple: (macd, signal, histogram)
    """
    # Convert to numpy array for calculations
    close = np.array(close_prices)
    
    # Calculate the fast and slow EMAs
    ema_fast = np.zeros_like(close)
    ema_slow = np.zeros_like(close)
    
    # Initialize with simple moving averages
    ema_fast[:fast_period] = np.nan
    ema_slow[:slow_period] = np.nan
    
    # Calculate fast EMA
    alpha_fast = 2 / (fast_period + 1)
    ema_fast[fast_period-1] = np.mean(close[:fast_period])
    for i in range(fast_period, len(close)):  # Fixed the missing parenthesis here
        ema_fast[i] = (close[i] - ema_fast[i-1]) * alpha_fast + ema_fast[i-1]
    
    # Calculate slow EMA
    alpha_slow = 2 / (slow_period + 1)
    ema_slow[slow_period-1] = np.mean(close[:slow_period])
    for i in range(slow_period, len(close)):
        ema_slow[i] = (close[i] - ema_slow[i-1]) * alpha_slow + ema_slow[i-1]
    
    # Calculate MACD line
    macd_line = np.zeros_like(close)
    macd_line[:slow_period] = np.nan
    macd_line[slow_period:] = ema_fast[slow_period:] - ema_slow[slow_period:]
    
    # Calculate signal line
    signal_line = np.zeros_like(close)
    signal_line[:slow_period+signal_period-1] = np.nan
    
    # Initialize signal with SMA of MACD for the first signal_period points
    valid_macd = macd_line[slow_period:slow_period+signal_period]
    valid_macd = valid_macd[~np.isnan(valid_macd)]
    if len(valid_macd) > 0:
        signal_line[slow_period+signal_period-1] = np.mean(valid_macd)
    
    # Calculate EMA for signal line
    alpha_signal = 2 / (signal_period + 1)
    for i in range(slow_period+signal_period, len(close)):
        signal_line[i] = (macd_line[i] - signal_line[i-1]) * alpha_signal + signal_line[i-1]
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def get_macd_signal(macd_line, signal_line):
    """
    Generate buy/sell signals based on MACD and Signal line crossovers.
    
    Parameters:
    macd_line (array): The MACD line values.
    signal_line (array): The Signal line values.
    
    Returns:
    list: List of signals (1 for buy, -1 for sell, 0 for hold).
    """
    signals = []
    for i in range(1, len(macd_line)):
        if macd_line[i] > signal_line[i] and macd_line[i-1] <= signal_line[i-1]:
            signals.append(1)  # Buy signal
        elif macd_line[i] < signal_line[i] and macd_line[i-1] >= signal_line[i-1]:
            signals.append(-1)  # Sell signal
        else:
            signals.append(0)  # Hold signal
    return signals