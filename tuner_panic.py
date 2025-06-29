import backtrader as bt
import pandas as pd
import itertools
import concurrent.futures
import json
import os

# 读取 symbols
SYMBOLS = ["AAPL", "TSLA", "0700.HK"]

# 定义可调参数
param_grid = {
    "drop_pct": [5, 6, 7],           # 恐慌下跌阈值
    "volume_mult": [1.2, 1.5],       # 放量因子
    "takeprofit": [0.03, 0.05],      # 止盈
    "stoploss": [0.02, 0.03],        # 止损
}

# 组合参数
all_params = list(itertools.product(
    param_grid["drop_pct"],
    param_grid["volume_mult"],
    param_grid["takeprofit"],
    param_grid["stoploss"]
))

# 回测策略
class PanicRebound(bt.Strategy):
    params = dict(
        drop_pct=5,
        volume_mult=1.5,
        takeprofit=0.05,
        stoploss=0.02,
        maxhold=5
    )

    def __init__(self):
        self.order = None
        self.buyprice = None

    def next(self):
        if self.position:
            # 止盈
            if self.data.close[0] >= self.buyprice * (1 + self.p.takeprofit):
                self.close()
                print(f"🎯 [{self.data._name}] 止盈卖出: {self.data.datetime.date(0)} @ {self.data.close[0]:.2f}")
            # 止损
            elif self.data.close[0] <= self.buyprice * (1 - self.p.stoploss):
                self.close()
                print(f"🛑 [{self.data._name}] 止损卖出: {self.data.datetime.date(0)} @ {self.data.close[0]:.2f}")
            # 超时
            elif len(self) - self.bar_executed >= self.p.maxhold:
                self.close()
                print(f"⏰ [{self.data._name}] 超时卖出: {self.data.datetime.date(0)} @ {self.data.close[0]:.2f}")
        else:
            # 检测恐慌下跌
            if len(self.data.close) < 2:
                return
            prev_close = self.data.close[-1]
            drop = (prev_close - self.data.close[0]) / prev_close
            avg_vol = pd.Series(self.data.volume.get(size=20)).mean()
            if (
                drop >= self.p.drop_pct / 100
                and self.data.volume[0] >= avg_vol * self.p.volume_mult
            ):
                self.buy()
                self.buyprice = self.data.close[0]
                self.bar_executed = len(self)
                print(f"✅ [{self.data._name}] 恐慌买入: {self.data.datetime.date(0)} @ {self.data.close[0]:.2f}")

def run_backtest(symbol, drop_pct, volume_mult, takeprofit, stoploss):
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(100000)

    df = pd.read_csv(f"{symbol}.csv", index_col=0, skiprows=[1], parse_dates=True)
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df.astype(float)

    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data, name=symbol)

    cerebro.addstrategy(
        PanicRebound,
        drop_pct=drop_pct,
        volume_mult=volume_mult,
        takeprofit=takeprofit,
        stoploss=stoploss,
    )

    cerebro.run()
    pnl = cerebro.broker.getvalue() - 100000
    return dict(
        symbol=symbol,
        drop_pct=drop_pct,
        volume_mult=volume_mult,
        takeprofit=takeprofit,
        stoploss=stoploss,
        pnl=round(pnl, 2)
    )

# 解决 lambda 无法被多进程序列化
def worker(args):
    return run_backtest(*args)

if __name__ == "__main__":
    tasks = []
    for symbol in SYMBOLS:
        for drop_pct, volume_mult, takeprofit, stoploss in all_params:
            tasks.append((symbol, drop_pct, volume_mult, takeprofit, stoploss))

    results = []
    print(f"⚙️ 并行回测 {len(tasks)} 组参数...")

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for res in executor.map(worker, tasks):
            print(
                f"✅ {res['symbol']} drop={res['drop_pct']} vol_mult={res['volume_mult']} "
                f"tp={res['takeprofit']} sl={res['stoploss']} → PnL={res['pnl']}"
            )
            results.append(res)

    # 保存成 JSON
    with open("panic_tuning_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("🏁 参数调优已完成，结果保存在 panic_tuning_results.json")
