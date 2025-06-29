import backtrader as bt
import pandas as pd
import itertools
import config

class GoldenCrossWithRSI(bt.Strategy):
    params = dict(
        fast=5,
        slow=20,
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
            self.rsis[d._name] = bt.indicators.RSI(d.close, period=14)
            self.buyprices[d._name] = 0.0

    def next(self):
        for d in self.datas:
            pos = self.getposition(d)
            crossover = self.crossovers[d._name]
            rsi = self.rsis[d._name][0]

            if pos:
                # 止盈
                if d.close[0] >= self.buyprices[d._name] * (1 + self.p.takeprofit):
                    self.close(data=d)

                # 止损
                elif d.close[0] <= self.buyprices[d._name] * (1 - self.p.stoploss):
                    self.close(data=d)

                # 均线死叉
                elif crossover < 0:
                    self.close(data=d)

            else:
                if crossover > 0 and rsi < self.p.rsi_limit:
                    self.buy(data=d, size=100)
                    self.buyprices[d._name] = d.close[0]

def run_backtest(fast, slow, rsi_limit, tp, sl):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(
        GoldenCrossWithRSI,
        fast=fast,
        slow=slow,
        rsi_limit=rsi_limit,
        takeprofit=tp,
        stoploss=sl
    )
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
    cerebro.run()
    final_value = cerebro.broker.getvalue()
    pnl = final_value - 100000
    return pnl

if __name__ == "__main__":
    grid = list(itertools.product(
        config.TUNER_PARAMS["fast_ma"],
        config.TUNER_PARAMS["slow_ma"],
        config.TUNER_PARAMS["rsi_limit"],
        config.TUNER_PARAMS["takeprofit"],
        config.TUNER_PARAMS["stoploss"]
    ))

    best_pnl = -999999
    best_params = None

    for fast, slow, rsi_limit, tp, sl in grid:
        if fast >= slow:
            continue  # 均线快线必须小于慢线
        pnl = run_backtest(fast, slow, rsi_limit, tp, sl)
        print(f"✅ fast={fast}, slow={slow}, rsi={rsi_limit}, tp={tp}, sl={sl} → PnL={pnl:.2f}")
        if pnl > best_pnl:
            best_pnl = pnl
            best_params = (fast, slow, rsi_limit, tp, sl)

    print(f"\n🏆 最佳参数: fast={best_params[0]}, slow={best_params[1]}, rsi={best_params[2]}, tp={best_params[3]}, sl={best_params[4]} → PnL={best_pnl:.2f}")
