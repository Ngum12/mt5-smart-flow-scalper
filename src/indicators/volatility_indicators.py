import numpy as np
import pandas as pd

def calculate_atr(high, low, close, period=14):
    """
    Calculate Average True Range (ATR)
    
    Parameters:
    high (array): High prices
    low (array): Low prices
    close (array): Close prices
    period (int): ATR period
    
    Returns:
    array: ATR values
    """
    high = np.array(high)
    low = np.array(low)
    close = np.array(close)
    
    # True Range calculations
    tr1 = high - low  # Current high - current low
    tr2 = np.abs(high - np.roll(close, 1))  # Current high - previous close
    tr3 = np.abs(low - np.roll(close, 1))  # Current low - previous close
    
    # Handle first element where previous close is invalid
    tr2[0] = tr1[0]
    tr3[0] = tr1[0]
    
    # True Range is the maximum of the three calculations
    tr = np.maximum(np.maximum(tr1, tr2), tr3)
    
    # Calculate ATR using Wilder's smoothing method
    atr = np.zeros_like(tr)
    atr[0:period] = np.nan  # First 'period' values are NaN
    
    # Initialize first ATR value with simple average
    if len(tr) >= period:
        atr[period-1] = np.mean(tr[:period])
        
        # Calculate subsequent ATR values
        for i in range(period, len(tr)):
            atr[i] = (atr[i-1] * (period-1) + tr[i]) / period
    
    return atr