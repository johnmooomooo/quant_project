import yfinance as yf
import config

def download_data():
    for symbol in config.SYMBOLS:
        print(f"⏬ 下载 {symbol} ...")
        df = yf.download(
            symbol,
            start="2020-01-01",
            end="2025-12-31",
            interval="1d",
            progress=False,
            auto_adjust=False,
        )

        if not df.empty:
            # 只保留需要的列
            df = df[["Open", "High", "Low", "Close", "Volume"]]
            # 索引改名
            df.index.name = "Date"
            # 保存
            df.to_csv(f"{symbol}.csv")
            print(f"✅ {symbol}.csv 已保存，行数: {len(df)}")
        else:
            print(f"⚠️ {symbol} 下载失败或无数据")

if __name__ == "__main__":
    download_data()
