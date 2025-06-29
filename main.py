import backtrader as bt
import pandas as pd
import config

class GoldenCrossWithRSI(bt.Strategy):
    params = dict(
        fast=5,
        slow=20,
        rsi_period=14,
        rsi_limit=50,
        takeprofit=0.05,
        stoploss=0.03,
    )

    def __init__(self):
        self.mas = dict()
        self.crossovers = dict()
        self.rsis = dict()
        self.buyprices = dict()

        for d in self.datas:
            self.mas[d._name] = {
                "fast": bt.indicators.SMA(d.close, period=self.p.fast),
                "slow": bt.indicators.SMA(d.close, period=self.p.slow)
            }
            self.crossovers[d._name] = bt.indicators.CrossOver(
                self.mas[d._name]["fast"],
                self.mas[d._name]["slow"]
            )
            self.rsis[d._name] = bt.indicators.RSI(d.close, period=self.p.rsi_period)
            self.buyprices[d._name] = 0.0

    def next(self):
        for d in self.datas:
            pos = self.getposition(d)
            crossover = self.crossovers[d._name]
            rsi = self.rsis[d._name][0]

            # 已经持仓
            if pos:
                # 止盈
                if d.close[0] >= self.buyprices[d._name] * (1 + self.p.takeprofit):
                    print(f"🎯 [{d._name}] 止盈卖出: {d.datetime.date(0)} @ {d.close[0]:.2f}")
                    self.close(data=d)

                # 止损
                elif d.close[0] <= self.buyprices[d._name] * (1 - self.p.stoploss):
                    print(f"⚠️ [{d._name}] 止损卖出: {d.datetime.date(0)} @ {d.close[0]:.2f}")
                    self.close(data=d)

                # 均线死叉
                elif crossover < 0:
                    self.close(data=d)
                    print(f"❌ [{d._name}] 均线死叉卖出: {d.datetime.date(0)} @ {d.close[0]:.2f}")

            # 无仓位
            else:
                if crossover > 0 and rsi < self.p.rsi_limit:
                    self.buy(data=d, size=100)
                    self.buyprices[d._name] = d.close[0]
                    print(f"✅ [{d._name}] 买入: {d.datetime.date(0)} @ {d.close[0]:.2f} (RSI={rsi:.1f})")

if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(GoldenCrossWithRSI)

    for symbol in config.SYMBOLS:
        df = pd.read_csv(f"{symbol}.csv", index_col=0, parse_dates=True, skiprows=[1,2])
        df = df[["Close","High","Low","Open","Volume"]]
        df = df.dropna()
        df = df.astype(float)
        data = bt.feeds.PandasData(dataname=df)
        data._name = symbol
        cerebro.adddata(data)

    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.001)

    print(f"初始资金: {cerebro.broker.getvalue():.2f}")
    cerebro.run()
    print(f"结束资金: {cerebro.broker.getvalue():.2f}")

    # cerebro.plot()
