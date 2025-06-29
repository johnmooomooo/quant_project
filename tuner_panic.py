import backtrader as bt
import pandas as pd
import yfinance as yf
import os
from itertools import product
import config


class TuningStrategy(bt.Strategy):
    params = (
        ("fast", 10),
        ("slow", 30),
    )

    def __init__(self):
        self.ma_fast = bt.indicators.SMA(self.data.close, period=self.p.fast)
        self.ma_slow = bt.indicators.SMA(self.data.close, period=self.p.slow)

    def next(self):
        if not self.position:
            if self.ma_fast[0] > self.ma_slow[0]:
                self.buy()
        else:
            if self.ma_fast[0] < self.ma_slow[0]:
                self.sell()


def download_data():
    os.makedirs("data", exist_ok=True)
    for symbol in config.SYMBOLS:
        print(f"⏬ Downloading {symbol}...")
        df = yf.download(symbol, start=config.START_DATE, end=config.END_DATE, interval="1d")
        if not df.empty:
            df.to_csv(f"data/{symbol}.csv")
            print(f"✅ Saved data/{symbol}.csv with {len(df)} rows")
        else:
            print(f"⚠️ {symbol} no data.")


def run_backtest(symbol, fast, slow):
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(100000)

    df = pd.read_csv(f"data/{symbol}.csv", parse_dates=True, index_col=0)

    # 强制转换index为Timestamp
    df.index = pd.to_datetime(df.index, errors="coerce")

    # 转 float 并过滤
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna()

    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data, name=symbol)

    cerebro.addstrategy(TuningStrategy, fast=fast, slow=slow)
    result = cerebro.run()
    final_value = cerebro.broker.getvalue()
    return {
        "symbol": symbol,
        "fast": fast,
        "slow": slow,
        "final_value": final_value
    }



if __name__ == "__main__":
    # 下载数据
    download_data()

    # 参数组合
    fast_list = [5, 10, 15]
    slow_list = [20, 30, 50]

    results = []

    for symbol in config.SYMBOLS:
        for fast, slow in product(fast_list, slow_list):
            if fast >= slow:
                continue
            res = run_backtest(symbol, fast, slow)
            results.append(res)
            print(f"🔍 {symbol} fast={fast} slow={slow} → final: {res['final_value']:.2f}")

    # 按收益排序
    results.sort(key=lambda x: x["final_value"], reverse=True)
    print("\n=== Top Results ===")
    for r in results[:5]:
        print(f"{r['symbol']} | fast={r['fast']} slow={r['slow']} → final: {r['final_value']:.2f}")
