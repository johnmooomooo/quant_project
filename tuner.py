import yfinance as yf

symbol = "AAPL"
start_date = "2023-01-01"
end_date = "2023-12-31"

df = yf.download(symbol, start=start_date, end=end_date, interval="1d")
df.to_csv(f"{symbol}.csv")
print(f"✅ 已保存 {symbol}.csv 文件，行数: {len(df)}")
