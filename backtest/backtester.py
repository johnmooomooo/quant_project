# quant_project/backtest/backtester.py

import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, initial_capital=100_000):
        self.initial_capital = initial_capital
        self.trades = []   # [{entry, exit, qty, pnl, entry_time, exit_time}]
        self.equity_curve = [initial_capital]

    def record_trade(self, entry, exit_, qty, entry_time, exit_time):
        pnl = (exit_ - entry) * qty
        trade = {
            "entry": entry,
            "exit": exit_,
            "qty": qty,
            "pnl": pnl,
            "entry_time": entry_time,
            "exit_time": exit_time,
        }
        self.trades.append(trade)
        # 更新净值
        self.equity_curve.append(self.equity_curve[-1] + pnl)

    def get_trades_df(self):
        return pd.DataFrame(self.trades)

    def compute_max_drawdown(self):
        curve = pd.Series(self.equity_curve)
        peak = curve.cummax()
        dd = (peak - curve) / peak
        return dd.max()

    def compute_sharpe(self):
        returns = pd.Series(self.equity_curve).pct_change().dropna()
        if returns.std() == 0:
            return 0
        sharpe = returns.mean() / returns.std() * np.sqrt(252)
        return sharpe

    def summary(self):
        df = self.get_trades_df()
        max_dd = self.compute_max_drawdown()
        sharpe = self.compute_sharpe()
        return {
            "total_pnl": self.equity_curve[-1] - self.initial_capital,
            "max_drawdown": max_dd,
            "sharpe": sharpe,
            "total_trades": len(df)
        }
