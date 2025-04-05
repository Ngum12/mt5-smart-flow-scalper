def calculate_volume_average(volume_data, period):
    if len(volume_data) < period:
        return None
    return sum(volume_data[-period:]) / period

def calculate_volume_change(volume_data):
    if len(volume_data) < 2:
        return None
    return volume_data[-1] - volume_data[-2]

def calculate_volume_indicator(volume_data, period):
    average_volume = calculate_volume_average(volume_data, period)
    if average_volume is None:
        return None
    current_volume = volume_data[-1]
    return current_volume / average_volume if average_volume > 0 else None

def is_high_volume_signal(volume_indicator, threshold):
    return volume_indicator is not None and volume_indicator > threshold

def is_low_volume_signal(volume_indicator, threshold):
    return volume_indicator is not None and volume_indicator < threshold