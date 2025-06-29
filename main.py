import backtrader as bt
import json
import pandas as pd

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
            if self.dataclose[0] >= self.buyprice * (1 + self.p.takeprofit):
                print(f"🎯 止盈卖出: {self.datas[0].datetime.date(0)} @ {self.dataclose[0]:.2f}")
                self.close()
            elif self.dataclose[0] <= self.buyprice * (1 - self.p.stoploss):
                print(f"🛑 止损卖出: {self.datas[0].datetime.date(0)} @ {self.dataclose[0]:.2f}")
                self.close()
            elif len(self) - self.bar_executed >= self.p.hold_days:
                print(f"⏰ 超时卖出: {self.datas[0].datetime.date(0)} @ {self.dataclose[0]:.2f}")
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
                print(f"✅ 恐慌买入: {self.datas[0].datetime.date(0)} @ {self.dataclose[0]:.2f}")
                self.buyprice = self.dataclose[0]
                self.order = self.buy()
                self.bar_executed = len(self)

if __name__ == "__main__":
    with open("best_panic_params.json") as f:
        best = json.load(f)
        symbol = best[0]
        params = best[1]
        print(f"▶ 使用最佳参数运行: {params}")

    df = pd.read_csv(f"{symbol}.csv", index_col=0, skiprows=[1], parse_dates=True)
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df.dropna()

    data = bt.feeds.PandasData(dataname=df)

    cerebro = bt.Cerebro()
    cerebro.addstrategy(PanicRebound, **params)
    cerebro.adddata(data)
    cerebro.broker.set_cash(100_000)
    cerebro.broker.setcommission(commission=0.001)

    print(f"🚀 初始资金: {cerebro.broker.getvalue():.2f}")
    cerebro.run()
    print(f"🏁 结束资金: {cerebro.broker.getvalue():.2f}")
