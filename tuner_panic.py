import backtrader as bt
import pandas as pd
import numpy as np
import itertools
import concurrent.futures
import json
from config import SYMBOLS

class PanicRebound(bt.Strategy):
    params = dict(
        drop_threshold=0.05,
        volume_ratio=1.5,
        hold_days=5,
        takeprofit=0.05,
        stoploss=0.03,
    )

    def __init__(self):
        self.orders = {}
        self.holding_days = {}
        self.bbands = {}
        for d in self.datas:
            self.orders[d._name] = None
            self.holding_days[d._name] = 0
            self.bbands[d._name] = bt.indicators.BollingerBands(d.close, period=20)

    def next(self):
        for d in self.datas:
            name = d._name
            pos = self.getposition(d).size

            # 计算当日和均量
            hist_vol = d.volume.get(size=20)
            avg_vol = np.mean(hist_vol)

            if len(d.close) > 1:
                drop = (d.close[-1] - d.close[0]) / d.close[-1]
                drop_pct = -drop

                if (
                    drop_pct > self.p.drop_threshold
                    and d.volume[0] > avg_vol * self.p.volume_ratio
                    and d.close[0] < self.bbands[name].bot[0]
                    and pos == 0
                ):
                    size = int(self.broker.getcash() / len(self.datas) / d.close[0])
                    self.orders[name] = self.buy(data=d, size=size)
                    self.holding_days[name] = 0
                    print(f"✅ [{name}] 恐慌买入: {d.datetime.date(0)} @ {d.close[0]:.2f}")

            if pos:
                self.holding_days[name] += 1
                entry_price = self.getposition(d).price

                if d.close[0] >= entry_price * (1 + self.p.takeprofit):
                    self.close(data=d)
                    print(f"🎯 [{name}] 止盈卖出: {d.datetime.date(0)} @ {d.close[0]:.2f}")
                elif d.close[0] <= entry_price * (1 - self.p.stoploss):
                    self.close(data=d)
                    print(f"🛑 [{name}] 止损卖出: {d.datetime.date(0)} @ {d.close[0]:.2f}")
                elif self.holding_days[name] >= self.p.hold_days:
                    self.close(data=d)
                    print(f"⏰ [{name}] 超时卖出: {d.datetime.date(0)} @ {d.close[0]:.2f}")

def run_backtest(symbol, drop_threshold, volume_ratio, hold_days, takeprofit, stoploss):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(
        PanicRebound,
        drop_threshold=drop_threshold,
        volume_ratio=volume_ratio,
        hold_days=hold_days,
        takeprofit=takeprofit,
        stoploss=stoploss,
    )
    cerebro.broker.set_cash(100000)

    df = pd.read_csv(f"{symbol}.csv", index_col=0, skiprows=[1], parse_dates=True)
    df = df[~df.index.isin(['Date'])]   # 清除"Date"列标题行
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df.dropna()  # 去掉NaT
    df = df.astype(float)

    data = bt.feeds.PandasData(dataname=df, name=symbol)
    cerebro.adddata(data)

    cerebro.run()
    pnl = cerebro.broker.getvalue() - 100000
    return {
        "symbol": symbol,
        "drop_threshold": drop_threshold,
        "volume_ratio": volume_ratio,
        "hold_days": hold_days,
        "takeprofit": takeprofit,
        "stoploss": stoploss,
        "pnl": pnl
    }

if __name__ == "__main__":
    # 超参数网格
    drop_thresholds = [0.03, 0.05, 0.08]
    volume_ratios = [1.2, 1.5, 2.0]
    hold_days = [3, 5, 7]
    takeprofits = [0.03, 0.05]
    stoplosses = [0.02, 0.03]

    param_grid = list(itertools.product(
        drop_thresholds, volume_ratios, hold_days, takeprofits, stoplosses
    ))

    tasks = []
    for symbol in SYMBOLS:
        for params in param_grid:
            tasks.append((symbol, *params))

    print(f"⚙️ 并行回测 {len(tasks)} 组参数...")

    results = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for res in executor.map(lambda args: run_backtest(*args), tasks):
            results.append(res)
            print(f"✅ {res}")

    # 保存
    with open("tuner_panic_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # 输出最佳
    best = max(results, key=lambda x: x["pnl"])
    print(f"\n🏆 最佳参数: {best}")
