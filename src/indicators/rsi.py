import numpy as np

def calculate_rsi(prices, period=14):
    """
    Calculate the Relative Strength Index (RSI) for a given price series.

    :param prices: List or array of prices
    :param period: The number of periods to use for the RSI calculation
    :return: RSI value as a float
    """
    if len(prices) < period:
        return None

    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])

    if avg_loss == 0:
        return 100  # Prevent division by zero; RSI is 100 if no losses

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi