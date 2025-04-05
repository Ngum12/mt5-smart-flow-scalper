import json

class RiskManager:
    def __init__(self, config_file):
        self.config = self.load_config(config_file)
        self.risk_per_trade = self.config.get("risk_per_trade", 0.01)
        self.account_balance = self.config.get("account_balance", 10000)

    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            return json.load(file)

    def calculate_position_size(self, entry_price, stop_loss_price):
        risk_amount = self.account_balance * self.risk_per_trade
        risk_per_unit = abs(entry_price - stop_loss_price)
        position_size = risk_amount / risk_per_unit
        return position_size

    def validate_trade(self, position_size):
        if position_size <= 0:
            raise ValueError("Position size must be greater than zero.")
        if position_size > self.account_balance:
            raise ValueError("Position size exceeds account balance.")

    def set_trade_limits(self, max_drawdown):
        self.max_drawdown = max_drawdown

    def check_drawdown(self, current_balance):
        drawdown = (self.account_balance - current_balance) / self.account_balance
        if drawdown > self.max_drawdown:
            raise ValueError("Max drawdown limit exceeded.")