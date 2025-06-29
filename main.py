import yfinance as yf
import asyncio
import pandas as pd
import config
from strategies.ma_strategy import MAStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.rsi_strategy import RSIStrategy
from utils.notifier import Notifier
from risk.stop_loss import check_stop_loss
from backtest.backtester import Backtester

notifier = Notifier()

async def main():
    # 下载5天5分钟K线
    df = yf.download("0700.HK", interval="5m", period="5d")

    # 初始化策略
    ma = MAStrategy()
    macd = MACDStrategy()
    rsi = RSIStrategy()

    # 计算指标
    df = ma.generate_signal(df)
    df = macd.generate_signal(df)
    df = rsi.generate_signal(df)

    # 账户
    capital = config.INITIAL_CAPITAL
    positions = []
    bt = Backtester(initial_capital=config.INITIAL_CAPITAL)

    for i in range(len(df)):
        row = df.iloc[i]

        # 避免 Series 比较歧义
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

        # 买入
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
                await notifier.send(
                    f"📈 买入 {buy_qty}股 @ {deal_price:.2f}, 手续费:{commission:.2f}, 剩余:{capital:.2f}"
                )

        # 卖出
        if sell_signal:
            i_pos = 0
            while i_pos < len(positions):
                pos = positions[i_pos]
                deal_price = row['Close'] * (1 - config.SLIPPAGE_RATE)
                sell_value = deal_price * pos['qty']
                commission = sell_value * config.COMMISSION_RATE
                net_income = sell_value - commission
                pnl = net_income - pos['price'] * pos['qty']
                pnl_pct = pnl / (pos['price'] * pos['qty']) * 100
                capital += net_income

                bt.record_trade(
                    entry=pos['price'],
                    exit_=deal_price,
                    qty=pos['qty'],
                    entry_time=pos['entry_time'],
                    exit_time=row.name
                )

                await notifier.send(
                    f"📉 卖出 {pos['qty']}股 @ {deal_price:.2f}, 盈亏:{pnl:.2f} ({pnl_pct:.2f}%), 剩余:{capital:.2f}"
                )
                positions.pop(i_pos)
            # pop后元素下移，不用i_pos+=1

        # 止损
        i_pos = 0
        while i_pos < len(positions):
            pos = positions[i_pos]
            if check_stop_loss(pos['price'], row['Close']):
                deal_price = row['Close'] * (1 - config.SLIPPAGE_RATE)
                sell_value = deal_price * pos['qty']
                commission = sell_value * config.COMMISSION_RATE
                net_income = sell_value - commission
                pnl = net_income - pos['price'] * pos['qty']
                pnl_pct = pnl / (pos['price'] * pos['qty']) * 100
                capital += net_income

                bt.record_trade(
                    entry=pos['price'],
                    exit_=deal_price,
                    qty=pos['qty'],
                    entry_time=pos['entry_time'],
                    exit_time=row.name
                )

                await notifier.send(
                    f"⚠️ 止损卖出 {pos['qty']}股 @ {deal_price:.2f}, 亏损:{pnl:.2f} ({pnl_pct:.2f}%), 剩余:{capital:.2f}"
                )
                positions.pop(i_pos)
            else:
                i_pos += 1

    # 回测总结
    summary = bt.summary()
    await notifier.send(
        f"""
🏁 回测结束
总收益: {summary['total_pnl']:.2f}
最大回撤: {summary['max_drawdown']*100:.2f}%
夏普比率: {summary['sharpe']:.2f}
总交易次数: {summary['total_trades']}
"""
    )

if __name__ == "__main__":
    asyncio.run(main())
