# quant_project/tuner.py

import yfinance as yf
import pandas as pd
from strategies.ma_strategy import MAStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from backtest.backtester import Backtester
import config

# 只下载一次
df = yf.download("0700.HK", interval="1d", period="1y")

def run_single_backtest(df, ma_fast, ma_slow, rsi_buy, rsi_sell):
    data = df.copy()

    ma = MAStrategy(fast=ma_fast, slow=ma_slow)
    macd = MACDStrategy()
    rsi = RSIStrategy(buy_th=rsi_buy, sell_th=rsi_sell)

    data = ma.generate_signal(data)
    data = macd.generate_signal(data)
    data = rsi.generate_signal(data)

    capital = config.INITIAL_CAPITAL
    positions = []
    bt = Backtester(initial_capital=capital)

    for i in range(len(data)):
        row = data.iloc[i]

        try:
            ma_sig = float(row['ma_signal']) if not pd.isna(row['ma_signal']) else 0
        except:
            ma_sig = 0
        try:
            macd_sig = float(row['macd_signal']) if not pd.isna(row['macd_signal']) else 0
        except:
            macd_sig = 0
        try:
            rsi_sig = float(row['rsi_signal']) if not pd.isna(row['rsi_signal']) else 0
        except:
            rsi_sig = 0

        buy_signal = (ma_sig == 1) or (macd_sig == 1) or (rsi_sig == 1)
        sell_signal = (ma_sig == -1) or (macd_sig == -1) or (rsi_sig == -1)

        if buy_signal:
            buy_budget = min(capital * config.ALLOCATE_PERCENTAGE, config.MAX_PER_TRADE)
            buy_qty = int(buy_budget // (row['Close'] * (1 + config.SLIPPAGE_RATE)))
            if buy_qty > 0:
                deal_price = row['Close'] * (1 + config.SLIPPAGE_RATE)
                cost = deal_price * buy_qty
                commission = cost * config.COMMISSION_RATE
                total_cost = cost + commission
                positions.append({
                    "price": deal_price,
                    "qty": buy_qty,
                    "entry_time": row.name
                })
                capital -= total_cost

        if sell_signal:
            i_pos = 0
            while i_pos < len(positions):
                pos = positions[i_pos]
                deal_price = row['Close'] * (1 - config.SLIPPAGE_RATE)
                sell_value = deal_price * pos['qty']
                commission = sell_value * config.COMMISSION_RATE
                net_income = sell_value - commission
                pnl = net_income - pos['price'] * pos['qty']
                capital += net_income
                bt.record_trade(
                    entry=pos['price'],
                    exit_=deal_price,
                    qty=pos['qty'],
                    entry_time=pos['entry_time'],
                    exit_time=row.name
                )
                positions.pop(i_pos)

    return bt.summary()

def main():
    results = []

    for ma_fast in range(3, 8):
        for ma_slow in range(ma_fast + 5, ma_fast + 20):
            for rsi_buy in range(20, 40, 5):
                for rsi_sell in range(60, 85, 5):
                    summary = run_single_backtest(df, ma_fast, ma_slow, rsi_buy, rsi_sell)
                    results.append({
                        "ma_fast": ma_fast,
                        "ma_slow": ma_slow,
                        "rsi_buy": rsi_buy,
                        "rsi_sell": rsi_sell,
                        "total_pnl": summary['total_pnl'],
                        "max_dd": summary['max_drawdown'],
                        "sharpe": summary['sharpe'],
                        "trades": summary['total_trades']
                    })
                    print(f"✅ tested ma{ma_fast}/{ma_slow} rsi{rsi_buy}/{rsi_sell} PnL:{summary['total_pnl']:.2f}")

    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values("total_pnl", ascending=False)
    df_results.to_csv("tuning_results.csv", index=False)
    print(df_results.head(10))

if __name__ == "__main__":
    main()
