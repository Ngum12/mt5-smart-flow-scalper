import json

def load_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def save_config(file_path, config):
    with open(file_path, 'w') as file:
        json.dump(config, file, indent=4)

# Default configuration settings
default_config = {
    "risk_parameters": {
        "max_drawdown": 0.1,
        "risk_per_trade": 0.02,
        "position_size": 1
    },
    "trading_limits": {
        "max_open_positions": 5,
        "max_daily_loss": 0.05
    },
    "api_keys": {
        "mt5": "YOUR_MT5_API_KEY"
    }
}

# Load configuration or use default
config_file_path = 'config.json'
try:
    config = load_config(config_file_path)
except FileNotFoundError:
    config = default_config
    save_config(config_file_path, config)