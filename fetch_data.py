import yfinance as yf
import config
import os

def download_data():
    for symbol in config.SYMBOLS:
        print(f"⏬ 下载 {symbol} ...")
        df = yf.download(symbol, start="2020-01-01", end="2025-12-31", interval="1d")
        if not df.empty:
            # 统一存放在一个“data”文件夹
            os.makedirs("data", exist_ok=True)
            df.to_csv(f"data/{symbol}.csv")
            print(f"✅ 已保存 data/{symbol}.csv, 共 {len(df)} 行")
        else:
            print(f"⚠️ {symbol} 下载失败或无数据")

if __name__ == "__main__":
    download_data()
