import backtrader as bt
import pandas as pd
import multiprocessing
import json
import os

class PanicRebound(bt.Strategy):
    params = dict(
        drop_threshold=0.05,
        volume_multiplier=1.5,
        hold_days=5,
        takeprofit=0.05,
        stoploss=0.03
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.bar_executed = None

    def next(self):
        if self.position:
            # 止盈
            if self.dataclose[0] >= self.buyprice * (1 + self.p.takeprofit):
                self.close()
            # 止损
            elif self.dataclose[0] <= self.buyprice * (1 - self.p.stoploss):
                self.close()
            # 超过最大持仓
            elif len(self) - self.bar_executed >= self.p.hold_days:
                self.close()
        else:
            if len(self.datas[0]) < 21:
                return
            drop_pct = (self.dataclose[-1] - self.dataclose[0]) / self.dataclose[-1]
            avg_vol = sum(self.datas[0].volume.get(size=20)) / 20.0
            if (
                drop_pct <= -self.p.drop_threshold
                and self.datas[0].volume[0] > avg_vol * self.p.volume_multiplier
            ):
                self.buyprice = self.dataclose[0]
                self.order = self.buy()
                self.bar_executed = len(self)

def run_backtest(symbol, params):
    df = pd.read_csv(f"{symbol}.csv", index_col=0, skiprows=[1], parse_dates=True)
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df.dropna()

    data = bt.feeds.PandasData(dataname=df)

    cerebro = bt.Cerebro()
    cerebro.addstrategy(PanicRebound, **params)
    cerebro.adddata(data)
    cerebro.broker.set_cash(100_000)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.run()

    return cerebro.broker.getvalue() - 100_000

def worker(symbol, param_set):
    pnl = run_backtest(symbol, param_set)
    return (symbol, param_set, pnl)

if __name__ == "__main__":
    symbols = ["AAPL", "TSLA", "0700.HK"]
    param_grid = []
    for drop in [0.05, 0.08]:
        for volmult in [1.5, 2]:
            for hold in [3, 5]:
                for tp in [0.03, 0.05]:
                    for sl in [0.02, 0.03]:
                        param_grid.append(dict(
                            drop_threshold=drop,
                            volume_multiplier=volmult,
                            hold_days=hold,
                            takeprofit=tp,
                            stoploss=sl
                        ))

    tasks = []
    with multiprocessing.Pool() as pool:
        for symbol in symbols:
            for params in param_grid:
                tasks.append(pool.apply_async(worker, (symbol, params)))

        results = [task.get() for task in tasks]

    best = max(results, key=lambda x: x[2])
    print(f"🏆 最佳参数: {best}")

    with open("best_panic_params.json", "w") as f:
        json.dump(best, f, indent=2)

    print("✅ 最佳参数已写入 best_panic_params.json")
