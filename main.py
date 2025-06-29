import backtrader as bt
import pandas as pd
from strategies.panic_rebound import PanicRebound

# === 配置 ===
symbols = ["AAPL", "TSLA", "0700.HK"]
start_date = "2020-01-01"
end_date = "2025-06-30"
initial_cash = 100000

# === Cerebro ===
cerebro = bt.Cerebro()
cerebro.broker.setcash(initial_cash)

# === 数据源 ===
for symbol in symbols:
    csv_file = f"{symbol}.csv"
    try:
        df = pd.read_csv(csv_file, index_col=0, parse_dates=True, skiprows=[1,2])
        df = df[["Close","High","Low","Open","Volume"]].dropna()
        df = df.astype(float)
        data = bt.feeds.PandasData(dataname=df, name=symbol)
        cerebro.adddata(data)
    except Exception as e:
        print(f"⚠️ 无法加载 {symbol}: {e}")

# === 策略 ===
cerebro.addstrategy(PanicRebound)

# === 运行 ===
print(f"🚀 初始资金: {cerebro.broker.getvalue():.2f}")
cerebro.run()
print(f"🏁 结束资金: {cerebro.broker.getvalue():.2f}")
