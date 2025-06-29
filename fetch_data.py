import yfinance as yf

# 以腾讯0700.HK为例
symbol = "0700.HK"
start_date = "2020-01-01"
end_date = "2025-12-31"

df = yf.download(symbol, start=start_date, end=end_date, interval="1d")

# 重置并清理索引
df = df.reset_index()

# 保存为标准 CSV
df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_csv(f"{symbol}.csv", index=False)

print(f"{symbol}.csv 已经保存，包含 {len(df)} 行。")
