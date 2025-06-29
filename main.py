import backtrader as bt
import pandas as pd
import config
import os
from strategies.panic_rebound import PanicRebound

if __name__ == "__main__":
    cerebro = bt.Cerebro()

    # 加载恐慌反弹策略
    cerebro.addstrategy(
        PanicRebound,
        panic_drop_pct=0.05,     # 单日下跌5%以上
        panic_vol_ratio=1.5,     # 成交量大于过去5日1.5倍
        hold_days=5,             # 最多持有5天
        takeprofit=0.03,         # 止盈3%
        stoploss=0.03            # 止损3%
    )

    for symbol in config.SYMBOLS:
        csv_file = f"{symbol}.csv"
        if not os.path.exists(csv_file):
            print(f"⚠️ 缺少 {csv_file}，请下载或准备好数据")
            continue
        df = pd.read_csv(csv_file, index_col=0, parse_dates=True, skiprows=[1, 2])
        df = df[["Close", "High", "Low", "Open", "Volume"]].dropna()
        df = df.astype(float)
        data = bt.feeds.PandasData(dataname=df)
        data._name = symbol
        cerebro.adddata(data)

    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.001)

    print(f"🚀 初始资金: {cerebro.broker.getvalue():.2f}")
    cerebro.run()
    print(f"🏁 结束资金: {cerebro.broker.getvalue():.2f}")

    # 如果你要画图可打开
    # cerebro.plot()
