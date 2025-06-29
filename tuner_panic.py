import backtrader as bt
import pandas as pd
import itertools

# === 策略 ===
class PanicRebound(bt.Strategy):
    params = dict(
        panic_drop_pct=0.05,
        volume_multiplier=1.5,
        takeprofit=0.05,
        stoploss=0.03,
        max_hold_days=5,
    )

    def __init__(self):
        self.order = None
        self.buy_price = None
        self.holding_days = 0

    def next(self):
        if self.position:
            self.holding_days += 1
            # 止盈
            if self.data.close[0] >= self.buy_price * (1 + self.p.takeprofit):
                self.sell()
            # 止损
            elif self.data.close[0] <= self.buy_price * (1 - self.p.stoploss):
                self.sell()
            # 超时
            elif self.holding_days >= self.p.max_hold_days:
                self.sell()
        else:
            if len(self.data) < 20:
                return  # 保障足够历史数据

            drop = (self.data.close[-1] - self.data.close[0]) / self.data.close[-1]
            avg_vol = pd.Series(self.data.volume.get(size=20)).mean()
            if drop < -self.p.panic_drop_pct and self.data.volume[0] > avg_vol * self.p.volume_multiplier:
                self.buy_price = self.data.close[0]
                self.holding_days = 0
                self.buy()


# === 参数网格 ===
param_grid = {
    'panic_drop_pct': [0.03, 0.05, 0.08],
    'volume_multiplier': [1.2, 1.5, 2.0],
    'takeprofit': [0.03, 0.05, 0.08],
    'stoploss': [0.02, 0.03, 0.05],
    'max_hold_days': [3, 5, 7],
}

param_combinations = list(itertools.product(
    param_grid['panic_drop_pct'],
    param_grid['volume_multiplier'],
    param_grid['takeprofit'],
    param_grid['stoploss'],
    param_grid['max_hold_days'],
))

best_pnl = -999999
best_params = None

for p in param_combinations:
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(100000)

    cerebro.addstrategy(
        PanicRebound,
        panic_drop_pct=p[0],
        volume_multiplier=p[1],
        takeprofit=p[2],
        stoploss=p[3],
        max_hold_days=p[4],
    )

    df = pd.read_csv("AAPL.csv", index_col=0, skiprows=[1,2], parse_dates=True)
    df.index = pd.to_datetime(df.index)
    df = df.astype(float)




    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    cerebro.run()
    pnl = cerebro.broker.getvalue() - 100000

    print(f"✅ panic={p[0]:.2%}, volx={p[1]}, tp={p[2]:.2%}, sl={p[3]:.2%}, hold={p[4]}d → PnL={pnl:.2f}")

    if pnl > best_pnl:
        best_pnl = pnl
        best_params = p

print(f"\n🏆 最优组合: panic={best_params[0]:.2%}, volx={best_params[1]}, tp={best_params[2]:.2%}, sl={best_params[3]:.2%}, hold={best_params[4]}d → PnL={best_pnl:.2f}")
