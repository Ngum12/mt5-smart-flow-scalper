def calculate_ema(prices, period):
    """Calculate the Exponential Moving Average (EMA) for a given period."""
    ema = prices.ewm(span=period, adjust=False).mean()
    return ema

def calculate_ema_short(prices):
    """Calculate the short-term EMA (e.g., 9-period)."""
    return calculate_ema(prices, period=9)

def calculate_ema_long(prices):
    """Calculate the long-term EMA (e.g., 21-period)."""
    return calculate_ema(prices, period=21)

def calculate_ema_cross(prices):
    """Calculate the EMA crossover signals."""
    ema_short = calculate_ema_short(prices)
    ema_long = calculate_ema_long(prices)
    
    signals = []
    for i in range(1, len(prices)):
        if ema_short[i] > ema_long[i] and ema_short[i-1] <= ema_long[i-1]:
            signals.append(1)  # Buy signal
        elif ema_short[i] < ema_long[i] and ema_short[i-1] >= ema_long[i-1]:
            signals.append(-1)  # Sell signal
        else:
            signals.append(0)  # No signal
    return signals