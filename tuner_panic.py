import backtrader as bt
import config
from datetime import datetime

class MyStrategy(bt.Strategy):
    def __init__(self):
        pass

    def next(self):
        for d in self.datas:
            self.log(f"{d._name} 收盘价: {d.close[0]}")

    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f"{dt} {txt}")

if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MyStrategy)

    for symbol in config.SYMBOLS:
        data = bt.feeds.GenericCSVData(
            dataname=f"{symbol}.csv",
            dtformat="%Y-%m-%d",
            timeframe=bt.TimeFrame.Days,
            compression=1,
            openinterest=-1,
            nullvalue=0.0,
            fromdate=datetime(2020, 1, 1),
            todate=datetime(2025, 12, 31)
        )
        cerebro.adddata(data, name=symbol)

    cerebro.run()
