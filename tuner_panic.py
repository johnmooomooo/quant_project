import backtrader as bt
import pandas as pd
import itertools
import concurrent.futures
import json
from datetime import datetime

# 读取配置
SYMBOLS = ["AAPL", "TSLA", "0700.HK"]

# 调优参数
PARAM_GRID = {
    "drop_threshold": [0.05, 0.07],
    "volume_mult": [1.5, 2.0],
    "bb_period": [20],
    "bb_dev": [2],
    "takeprofit": [0.03, 0.05],
    "stoploss": [0.02, 0.03],
    "hold_days": [3, 5],
}

# 生成参数组合
all_params = list(itertools.product(
    PARAM_GRID["drop_threshold"],
    PARAM_GRID["volume_mult"],
    PARAM_GRID["bb_period"],
    PARAM_GRID["bb_dev"],
    PARAM_GRID["takeprofit"],
    PARAM_GRID["stoploss"],
    PARAM_GRID["hold_days"],
))


class PanicRebound(bt.Strategy):
    params = dict(
        drop_threshold=0.05,
        volume_mult=2.0,
        bb_period=20,
        bb_dev=2,
        takeprofit=0.05,
        stoploss=0.03,
        hold_days=5,
    )

    def __init__(self):
        self.order = None
        self.dataclose = dict()
        self.bbands = dict()
        self.buyprice = dict()
        self.hold_days_count = dict()
        self.entry_price = dict()

        for d in self.datas:
            name = d._name
            self.dataclose[name] = d.close
            self.bbands[name] = bt.indicators.BollingerBands(d.close, period=self.p.bb_period, devfactor=self.p.bb_dev)
            self.buyprice[name] = None
            self.hold_days_count[name] = 0
            self.entry_price[name] = None

    def next(self):
        for d in self.datas:
            name = d._name

            # 计算前一日跌幅
            if len(d) < 2:
                continue
            drop_pct = (d.close[-1] - d.close[0]) / d.close[-1]
            avg_vol = pd.Series(d.volume.get(size=20)).mean()
            vol = d.volume[0]

            if not self.getposition(d).size:
                if (
                    drop_pct <= -self.p.drop_threshold
                    and vol >= avg_vol * self.p.volume_mult
                    and d.close[0] < self.bbands[name].bot[0]
                ):
                    self.buy(data=d)
                    self.entry_price[name] = d.close[0]
                    self.hold_days_count[name] = 0
                    print(f"✅ [{name}] 恐慌买入: {self.data.datetime.date(0)} @ {d.close[0]:.2f}")
            else:
                self.hold_days_count[name] += 1
                current_pct = (d.close[0] - self.entry_price[name]) / self.entry_price[name]
                if (
                    current_pct >= self.p.takeprofit
                    or current_pct <= -self.p.stoploss
                    or self.hold_days_count[name] >= self.p.hold_days
                ):
                    self.close(data=d)
                    print(f"🎯 [{name}] 卖出: {self.data.datetime.date(0)} @ {d.close[0]:.2f}")


def run_backtest(
    symbol,
    drop_threshold,
    volume_mult,
    bb_period,
    bb_dev,
    takeprofit,
    stoploss,
    hold_days,
):
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(100000)

    # 读取 CSV
    df = pd.read_csv(f"{symbol}.csv", index_col=0, skiprows=[1], parse_dates=True)
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df.dropna()

    data = bt.feeds.PandasData(dataname=df, name=symbol)
    cerebro.adddata(data)

    cerebro.addstrategy(
        PanicRebound,
        drop_threshold=drop_threshold,
        volume_mult=volume_mult,
        bb_period=bb_period,
        bb_dev=bb_dev,
        takeprofit=takeprofit,
        stoploss=stoploss,
        hold_days=hold_days,
    )

    cerebro.run()
    pnl = cerebro.broker.getvalue() - 100000
    return dict(
        symbol=symbol,
        drop_threshold=drop_threshold,
        volume_mult=volume_mult,
        bb_period=bb_period,
        bb_dev=bb_dev,
        takeprofit=takeprofit,
        stoploss=stoploss,
        hold_days=hold_days,
        pnl=pnl
    )


# 并行多进程必须用非 lambda 函数
def worker(args):
    return run_backtest(*args)


if __name__ == "__main__":
    tasks = []
    for symbol in SYMBOLS:
        for param in all_params:
            tasks.append((symbol, *param))

    print(f"⚙️ 并行回测 {len(tasks)} 组参数...")

    results = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for res in executor.map(worker, tasks):
            results.append(res)
            print(f"✅ {res}")

    # 保存 json
    with open("tuner_panic_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("✅ 已保存到 tuner_panic_results.json")
