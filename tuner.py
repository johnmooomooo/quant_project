import yfinance as yf
import pandas as pd
import config
from strategies.ma_strategy import MAStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from backtest.backtester import Backtester


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

        # 策略开关
        buy_signal = False
        sell_signal = False

        if config.USE_MA:
            buy_signal = (ma_sig == 1)
            sell_signal = (ma_sig == -1)

        if config.USE_MACD:
            buy_signal = buy_signal or (macd_sig == 1)
            sell_signal = sell_signal or (macd_sig == -1)

        if config.USE_RSI:
            buy_signal = buy_signal or (rsi_sig == 1)
            sell_signal = sell_signal or (rsi_sig == -1)

        # 买
        if buy_signal and not positions:
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
                print(f"✅ BUY {buy_qty} @ {deal_price:.2f} on {row.name}")

        # 卖
        if sell_signal and positions:
            pos = positions.pop(0)
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
            print(f"❌ SELL {pos['qty']} @ {deal_price:.2f} on {row.name}")

    return bt.summary()


def main():
    results = []
    tuner_cfg = config.TUNER_PARAMS

    for symbol in config.SYMBOLS:
        print(f"\n📊 正在下载数据: {symbol}")
        df = yf.download(symbol, interval=config.INTERVAL, period=config.PERIOD)

        for ma_fast in tuner_cfg["ma_fast_range"]:
            for ma_slow in tuner_cfg["ma_slow_range"]:
                for rsi_buy in tuner_cfg["rsi_buy_range"]:
                    for rsi_sell in tuner_cfg["rsi_sell_range"]:
                        summary = run_single_backtest(df, ma_fast, ma_slow, rsi_buy, rsi_sell)
                        results.append({
                            "symbol": symbol,
                            "ma_fast": ma_fast,
                            "ma_slow": ma_slow,
                            "rsi_buy": rsi_buy,
                            "rsi_sell": rsi_sell,
                            "total_pnl": summary['total_pnl'],
                            "max_dd": summary['max_drawdown'],
                            "sharpe": summary['sharpe'],
                            "trades": summary['total_trades']
                        })
                        print(
                            f"✅ {symbol} | ma{ma_fast}/{ma_slow} rsi{rsi_buy}/{rsi_sell} "
                            f"PnL:{summary['total_pnl']:.2f} Trades:{summary['total_trades']}"
                        )

    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values("total_pnl", ascending=False)
    df_results.to_csv("tuning_results.csv", index=False)
    print("\n🏆 Top 10 overall:")
    print(df_results.head(10))


if __name__ == "__main__":
    main()
