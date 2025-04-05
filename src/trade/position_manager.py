import MetaTrader5 as mt5

class PositionManager:
    def __init__(self):
        self.open_positions = []

    def open_position(self, symbol, volume, order_type):
        if order_type == 'buy':
            order = mt5.ORDER_BUY
        elif order_type == 'sell':
            order = mt5.ORDER_SELL
        else:
            raise ValueError("Invalid order type. Use 'buy' or 'sell'.")

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order,
            "price": mt5.symbol_info_tick(symbol).ask if order_type == 'buy' else mt5.symbol_info_tick(symbol).bid,
            "sl": 0,
            "tp": 0,
            "deviation": 10,
            "magic": 123456,
            "comment": "Smart Flow Scalper",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to open position: {result.retcode}")
        else:
            self.open_positions.append(result)

    def close_position(self, position):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "volume": position.volume,
            "type": mt5.ORDER_SELL if position.type == mt5.ORDER_BUY else mt5.ORDER_BUY,
            "price": mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.ORDER_BUY else mt5.symbol_info_tick(position.symbol).ask,
            "deviation": 10,
            "magic": 123456,
            "comment": "Closing position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to close position: {result.retcode}")
        else:
            self.open_positions.remove(position)