import numpy as np

class Backtester:
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.trades = []

    def record_trade(self, entry, exit_, qty, entry_time, exit_time):
        pnl = (exit_ - entry) * qty
        self.trades.append({
            "entry": entry,
            "exit": exit_,
            "qty": qty,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "pnl": pnl
        })
        print(f"✅ 记录交易: {qty} 股 {entry_time} 买入 {entry:.2f} → {exit_time} 卖出 {exit_:.2f}, PnL={pnl:.2f}")

    def summary(self):
        total_pnl = sum(trade['pnl'] for trade in self.trades)
        returns = [trade['pnl']/self.initial_capital for trade in self.trades]
        if len(returns) > 1:
            sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(len(returns))
        else:
            sharpe = 0.0

        max_dd = self._calculate_max_drawdown()
        print(f"🏁 回测完成，总收益:{total_pnl:.2f}，最大回撤:{max_dd:.2%}，夏普:{sharpe:.2f}")
        return {
            "total_pnl": total_pnl,
            "max_drawdown": max_dd,
            "sharpe": sharpe,
            "total_trades": len(self.trades)
        }

    def _calculate_max_drawdown(self):
        equity = [self.initial_capital]
        capital = self.initial_capital
        for trade in self.trades:
            capital += trade['pnl']
            equity.append(capital)
        peak = equity[0]
        max_dd = 0
        for x in equity:
            if x > peak:
                peak = x
            dd = (peak - x) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd
