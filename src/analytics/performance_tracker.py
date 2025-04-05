import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import os

class PerformanceTracker:
    def __init__(self, strategy_name):
        self.strategy_name = strategy_name
        self.trades_file = f"trades_{strategy_name.lower().replace(' ', '_')}.csv"
        self.trades = self._load_trades()
        
    def _load_trades(self):
        """Load existing trades from CSV file or create a new dataframe"""
        if os.path.exists(self.trades_file):
            return pd.read_csv(self.trades_file)
        else:
            return pd.DataFrame(columns=[
                'ticket', 'symbol', 'type', 'entry_time', 'entry_price', 
                'lot_size', 'stop_loss', 'take_profit', 'exit_time', 
                'exit_price', 'profit', 'pips', 'duration', 'status'
            ])
    
    def save_trades(self):
        """Save trades to CSV file"""
        self.trades.to_csv(self.trades_file, index=False)
        
    def add_trade_entry(self, ticket, symbol, trade_type, entry_price, lot_size, stop_loss, take_profit):
        """Add a new trade entry"""
        new_trade = {
            'ticket': ticket,
            'symbol': symbol,
            'type': trade_type,
            'entry_time': datetime.now(),
            'entry_price': entry_price,
            'lot_size': lot_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'exit_time': None,
            'exit_price': None,
            'profit': None,
            'pips': None,
            'duration': None,
            'status': 'OPEN'
        }
        
        self.trades = pd.concat([self.trades, pd.DataFrame([new_trade])], ignore_index=True)
        self.save_trades()
        
    def update_trade_exit(self, ticket, exit_price, profit):
        """Update a trade when it's closed"""
        if ticket not in self.trades['ticket'].values:
            print(f"Trade {ticket} not found in trade history")
            return
            
        # Get the trade index
        idx = self.trades[self.trades['ticket'] == ticket].index[0]
        
        # Update trade info
        self.trades.loc[idx, 'exit_time'] = datetime.now()
        self.trades.loc[idx, 'exit_price'] = exit_price
        self.trades.loc[idx, 'profit'] = profit
        
        # Calculate pips
        entry_price = self.trades.loc[idx, 'entry_price']
        trade_type = self.trades.loc[idx, 'type']
        
        if trade_type == 'BUY':
            pips = (exit_price - entry_price) * 10000  # For forex pairs
        else:
            pips = (entry_price - exit_price) * 10000
            
        self.trades.loc[idx, 'pips'] = pips
        
        # Calculate duration (in minutes)
        entry_time = pd.to_datetime(self.trades.loc[idx, 'entry_time'])
        exit_time = pd.to_datetime(self.trades.loc[idx, 'exit_time'])
        duration = (exit_time - entry_time).total_seconds() / 60
        self.trades.loc[idx, 'duration'] = duration
        
        # Update status
        self.trades.loc[idx, 'status'] = 'WIN' if profit > 0 else 'LOSS'
        
        self.save_trades()
        
    def get_performance_stats(self):
        """Calculate performance statistics"""
        if len(self.trades) == 0:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'average_win': 0,
                'average_loss': 0,
                'max_drawdown': 0,
                'average_trade': 0
            }
            
        # Filter closed trades
        closed_trades = self.trades[self.trades['status'].isin(['WIN', 'LOSS'])]
        
        if len(closed_trades) == 0:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'average_win': 0,
                'average_loss': 0,
                'max_drawdown': 0,
                'average_trade': 0
            }
            
        # Basic stats
        wins = closed_trades[closed_trades['status'] == 'WIN']
        losses = closed_trades[closed_trades['status'] == 'LOSS']
        
        total_trades = len(closed_trades)
        win_count = len(wins)
        win_rate = win_count / total_trades if total_trades > 0 else 0
        
        # Profit metrics
        total_profit = closed_trades['profit'].sum()
        gross_profits = wins['profit'].sum() if len(wins) > 0 else 0
        gross_losses = abs(losses['profit'].sum()) if len(losses) > 0 else 0
        profit_factor = gross_profits / gross_losses if gross_losses > 0 else float('inf')
        
        # Average trade metrics
        average_win = wins['profit'].mean() if len(wins) > 0 else 0
        average_loss = losses['profit'].mean() if len(losses) > 0 else 0
        average_trade = closed_trades['profit'].mean()
        
        # Calculate drawdown
        equity_curve = closed_trades['profit'].cumsum()
        max_equity = equity_curve.cummax()
        drawdown = max_equity - equity_curve
        max_drawdown = drawdown.max()
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'average_win': average_win,
            'average_loss': average_loss,
            'max_drawdown': max_drawdown,
            'average_trade': average_trade,
            'total_profit': total_profit
        }
        
    def plot_equity_curve(self):
        """Plot equity curve and drawdown"""
        if len(self.trades) == 0:
            print("No trades available for plotting")
            return
            
        # Filter closed trades
        closed_trades = self.trades[self.trades['status'].isin(['WIN', 'LOSS'])]
        
        if len(closed_trades) == 0:
            print("No closed trades available for plotting")
            return
            
        # Create equity curve
        closed_trades = closed_trades.sort_values('exit_time')
        equity_curve = closed_trades['profit'].cumsum()
        
        # Calculate drawdown
        max_equity = equity_curve.cummax()
        drawdown = max_equity - equity_curve
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Plot equity curve
        ax1.plot(equity_curve.values, color='blue', lw=2)
        ax1.set_title(f'{self.strategy_name} Equity Curve', fontsize=14)
        ax1.set_ylabel('Equity ($)', fontsize=12)
        ax1.grid(True)
        
        # Plot drawdown
        ax2.fill_between(range(len(drawdown)), 0, drawdown.values, color='red', alpha=0.3)
        ax2.set_title('Drawdown', fontsize=14)
        ax2.set_xlabel('Trade Number', fontsize=12)
        ax2.set_ylabel('Drawdown ($)', fontsize=12)
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(f"{self.strategy_name.lower().replace(' ', '_')}_performance.png")
        plt.close()