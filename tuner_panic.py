# tuner_panic.py

import backtrader as bt
import pandas as pd
import itertools
import json
from concurrent.futures import ProcessPoolExecutor
import os

# 配置
INITIAL_CAPITAL = 100_000
SYMBOLS = ["AAPL", "TSLA", "0700.HK"]

# 参数范围
PARAM_GRID = {
    "drop_pct": [0.05, 0.07, 0.1],
    "volume_mult": [1.2, 1.5],
    "takeprofit": [0.03, 0.05],
    "stoploss": [0.02, 0.03],
}

# 策略
class PanicRebound(bt.Strategy):
    params = dict(
        drop_pct=0.05,
        volume_mult=1.5,
        takeprofit=0.05,
        stoploss=0.02,
        hold_days=5
    )

    def __init__(self):
        self.order = None
        self.buyprice = None
        self.hold_bars = 0

    def next(self):
        if self.position:
            self.hold_bars += 1
            # 止盈
            if self.data.close[0] >= self.buyprice * (1 + self.p.takeprofit):
                self.close()
                self.hold_bars = 0
            # 止损
            elif self.data.close[0] <= self.buyprice * (1 - self.p.stoploss):
                self.close()
                self.hold_bars = 0
            # 超过最大持仓天数
            elif self.hold_bars >= self.p.hold_days:
                self.close()
                self.hold_bars = 0
        else:
            if len(self.data) < 2:
                return
            drop = (self.data.close[-1] - self.data.close[0]) / self.data.close[-1]
            avg_vol = pd.Series(self.data.volume.get(size=20)).mean()
            if (
                drop <= -self.p.drop_pct
                and self.data.volume[0] >= avg_vol * self.p.volume_mult
            ):
                self.buyprice = self.data.close[0]
                self.buy()
                self.hold_bars = 0

# 并行回测
def run_backtest(symbol, drop_pct, volume_mult, takeprofit, stoploss):
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(INITIAL_CAPITAL)

    # CSV 读取
    def safe_date_parser(x):
        try:
            return pd.to_datetime(x, format="%Y-%m-%d")
        except:
            return pd.NaT

    df = pd.read_csv(
        f"{symbol}.csv",
        index_col=0,
        skiprows=[1],
        parse_dates=True,
        date_parser=safe_date_parser,
    )
    df.dropna(inplace=True)

    data = bt.feeds.PandasData(dataname=df)

    cerebro.adddata(data)
    cerebro.addstrategy(
        PanicRebound,
        drop_pct=drop_pct,
        volume_mult=volume_mult,
        takeprofit=takeprofit,
        stoploss=stoploss,
    )

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    result = cerebro.run()
    strat = result[0]

    pnl = cerebro.broker.getvalue() - INITIAL_CAPITAL
    trades = strat.analyzers.ta.get_analysis()
    total_trades = trades.total.closed if trades.total else 0

    summary = dict(
        symbol=symbol,
        drop_pct=drop_pct,
        volume_mult=volume_mult,
        takeprofit=takeprofit,
        stoploss=stoploss,
        pnl=round(pnl, 2),
        total_trades=total_trades
    )
    return summary

# 并行执行
if __name__ == "__main__":
    tasks = list(itertools.product(
        SYMBOLS,
        PARAM_GRID["drop_pct"],
        PARAM_GRID["volume_mult"],
        PARAM_GRID["takeprofit"],
        PARAM_GRID["stoploss"],
    ))

    print(f"⚙️ 并行回测 {len(tasks)} 组参数...")

    results = []
    with ProcessPoolExecutor() as executor:
        for res in executor.map(
            lambda x: run_backtest(*x), tasks
        ):
            print(
                f"✅ {res['symbol']} drop={res['drop_pct']}, vol_mult={res['volume_mult']}, "
                f"tp={res['takeprofit']}, sl={res['stoploss']} → PnL={res['pnl']}"
            )
            results.append(res)

    # 保存为 JSON
    with open("tuner_panic_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # 也打印最优
    best = max(results, key=lambda x: x["pnl"])
    print(
        f"\n🏆 最佳参数: {best['symbol']} drop={best['drop_pct']}, "
        f"vol_mult={best['volume_mult']}, tp={best['takeprofit']}, "
        f"sl={best['stoploss']} → PnL={best['pnl']}"
    )
