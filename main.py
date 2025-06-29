import backtrader as bt
from datetime import datetime

class GoldenCross(bt.Strategy):
    params = (
        ("fast", 5),
        ("slow", 20),
    )

    def __init__(self):
        # 定义均线
        self.ma_fast = bt.indicators.SMA(self.data.close, period=self.p.fast)
        self.ma_slow = bt.indicators.SMA(self.data.close, period=self.p.slow)
        # 定义交叉
        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy(size=100)
                print(f"✅ 买入: {self.data.datetime.date(0)} @ {self.data.close[0]:.2f}")
        elif self.crossover < 0:
            self.close()
            print(f"❌ 卖出: {self.data.datetime.date(0)} @ {self.data.close[0]:.2f}")

if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(GoldenCross)

    # 加载 AAPL 一整年的数据
    data = bt.feeds.YahooFinanceData(
        dataname="AAPL",
        fromdate=datetime(2023, 1, 1),
        todate=datetime(2023, 12, 31)
    )
    cerebro.adddata(data)

    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.001)

    print(f"初始资金: {cerebro.broker.getvalue():.2f}")
    cerebro.run()
    print(f"结束资金: {cerebro.broker.getvalue():.2f}")

    cerebro.plot()
