import backtrader as bt

class GoldenCross(bt.Strategy):
    params = (
        ("fast", 5),
        ("slow", 20)
    )

    def __init__(self):
        self.ma_fast = bt.indicators.SMA(self.data.close, period=self.p.fast)
        self.ma_slow = bt.indicators.SMA(self.data.close, period=self.p.slow)
        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy(size=100)
                print(f"买入: {self.data.datetime.date(0)} @ {self.data.close[0]}")
        elif self.crossover < 0:
            self.close()
            print(f"卖出: {self.data.datetime.date(0)} @ {self.data.close[0]}")

if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(GoldenCross)

    data = bt.feeds.YahooFinanceData(dataname="AAPL", fromdate=pd.Timestamp('2023-01-01'), todate=pd.Timestamp('2023-12-31'))
    cerebro.adddata(data)

    cerebro.broker.setcash(100000)
    cerebro.run()
    cerebro.plot()
