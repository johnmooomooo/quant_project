import backtrader as bt
import pandas as pd
import concurrent.futures
import itertools
import json
import os
import config

class PanicRebound(bt.Strategy):
    params = dict(
        drop_threshold=0.05,
        hold_days=5,
        takeprofit=0.05,
        stoploss=0.02,
    )

    def __init__(self):
        self.order = None
        self.buyprice = None
        self.buydate = None
        self.bar_executed = 0

    def next(self):
        d = self.datas[0]
        if self.order:
            return

        if not self.position:
            # 计算过去N日平均成交量
            lookback = 5
            if len(d) <= lookback:
                return
            avg_vol = sum(d.volume.get(size=lookback)) / lookback
            if d.close[-1] > 0:
                drop_pct = (d.close[-1] - d.close[0]) / d.close[-1]
                if drop_pct <= -self.p.drop_threshold and d.volume[0] > avg_vol:
                    self.order = self.buy()
                    self.buyprice = d.close[0]
                    self.bar_executed = len(self)
                    print(f"✅ [{d._name}] 恐慌买入: {d.datetime.date(0)} @ {d.close[0]:.2f}")
        else:
            # 持仓中
            if len(self) >= self.bar_executed + self.p.hold_days:
                self.close()
                print(f"⏰ [{d._name}] 超时卖出: {d.datetime.date(0)} @ {d.close[0]:.2f}")
            elif d.close[0] >= self.buyprice * (1 + self.p.takeprofit):
                self.close()
                print(f"🎯 [{d._name}] 止盈卖出: {d.datetime.date(0)} @ {d.close[0]:.2f}")
            elif d.close[0] <= self.buyprice * (1 - self.p.stoploss):
                self.close()
                print(f"🛑 [{d._name}] 止损卖出: {d.datetime.date(0)} @ {d.close[0]:.2f}")

def run_backtest(symbol, drop_threshold, hold_days, takeprofit, stoploss):
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000)

    df = pd.read_json(f"{symbol}.json")
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)

    data = bt.feeds.PandasData(dataname=df, name=symbol)
    cerebro.adddata(data)

    cerebro.addstrategy(
        PanicRebound,
        drop_threshold=drop_threshold,
        hold_days=hold_days,
        takeprofit=takeprofit,
        stoploss=stoploss,
    )

    cerebro.addsizer(bt.sizers.FixedSize, stake=10)
    cerebro.run()
    pnl = cerebro.broker.getvalue() - 100000
    return dict(
        symbol=symbol,
        drop=drop_threshold,
        hold=hold_days,
        tp=takeprofit,
        sl=stoploss,
        pnl=round(pnl, 2)
    )

if __name__ == "__main__":
    # 优化网格
    drop_thresholds = [0.03, 0.05, 0.08]
    hold_days_range = [3, 5, 7]
    takeprofits = [0.03, 0.05, 0.08]
    stoplosses = [0.02, 0.03, 0.05]

    param_grid = list(itertools.product(
        drop_thresholds,
        hold_days_range,
        takeprofits,
        stoplosses,
    ))

    tasks = []
    for symbol in config.SYMBOLS:
        for params in param_grid:
            tasks.append( (symbol, *params) )

    print(f"⚙️ 并行回测 {len(tasks)} 组参数...")

    results = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for res in executor.map(lambda args: run_backtest(*args), tasks):
            results.append(res)
            print(f"✅ {res}")

    # 保存为JSON，供 main.py 使用
    best = max(results, key=lambda x: x['pnl'])
    with open("best_panic_params.json", "w") as f:
        json.dump(best, f, indent=2)
    print(f"\n🏆 最佳参数：{best}")
