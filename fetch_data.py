import yfinance as yf
import config

def download_data():
    for symbol in config.SYMBOLS:
        print(f"⏬ 下载 {symbol} ...")
        df = yf.download(symbol, start="2020-01-01", end="2025-12-31", interval="1d")
        if not df.empty:
            df.to_csv(f"{symbol}.csv")
            print(f"✅ {symbol}.csv 已保存，行数: {len(df)}")
        else:
            print(f"⚠️ {symbol} 下载失败或无数据")

if __name__ == "__main__":
    download_data()
