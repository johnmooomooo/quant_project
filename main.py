import backtrader as bt
import pandas as pd

class GoldenCross(bt.Strategy):
    params = (("fast", 5), ("slow", 20),)

    def __init__(self):
        self.mas = dict()
        self.crossovers = dict()

        for d in self.datas:
            # 对每只股票都单独设置指标
            self.mas[d._name] = {
                "fast": bt.indicators.SMA(d.close, period=self.p.fast),
                "slow": bt.indicators.SMA(d.close, period=self.p.slow)
            }
            self.crossovers[d._name] = bt.indicators.CrossOver(
                self.mas[d._name]["fast"],
                self.mas[d._name]["slow"]
            )

    def next(self):
        for d in self.datas:
            pos = self.getposition(d)
            crossover = self.crossovers[d._name]
            if not pos:
                if crossover > 0:
                    self.buy(data=d, size=100)
                    print(f"✅ [{d._name}] 买入: {d.datetime.date(0)} @ {d.close[0]:.2f}")
            else:
                if crossover < 0:
                    self.close(data=d)
                    print(f"❌ [{d._name}] 卖出: {d.datetime.date(0)} @ {d.close[0]:.2f}")

if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(GoldenCross)

    symbols = ["AAPL", "TSLA"]
    for symbol in symbols:
        df = pd.read_csv(f"{symbol}.csv", index_col=0, parse_dates=True, skiprows=[1,2])
        df = df[["Close","High","Low","Open","Volume"]]
        df = df.dropna()
        df = df.astype(float)
        data = bt.feeds.PandasData(dataname=df)
        data._name = symbol  # 给每个data取名
        cerebro.adddata(data)

    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.001)

    print(f"初始资金: {cerebro.broker.getvalue():.2f}")
    cerebro.run()
    print(f"结束资金: {cerebro.broker.getvalue():.2f}")

    # 如果需要画图就取消注释
    # cerebro.plot()
