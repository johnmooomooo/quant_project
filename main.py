# quant_project/main.py

import yfinance as yf
import asyncio
import config
from strategies.ma_strategy import MAStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.rsi_strategy import RSIStrategy
from utils.notifier import Notifier
from risk.stop_loss import check_stop_loss
from backtest.backtester import Backtester

notifier = Notifier()

async def main():
    # 下载历史数据
    df = yf.download("0700.HK", interval="5m", period="5d")

    # 初始化策略
    ma = MAStrategy()
    macd = MACDStrategy()
    rsi = RSIStrategy()

    # 生成各自信号
    df = ma.generate_signal(df)
    df = macd.generate_signal(df)
    df = rsi.generate_signal(df)

    capital = config.INITIAL_CAPITAL
    positions = []
    bt = Backtester(initial_capital=config.INITIAL_CAPITAL)

    for i in range(len(df)):
        row = df.iloc[i]

        buy_signal = (
            row['ma_signal'] == 1
            or row['macd_signal'] == 1
            or row['rsi_signal'] == 1
        )
        sell_signal = (
            row['ma_signal'] == -1
            or row['macd_signal'] == -1
            or row['rsi_signal'] == -1
        )

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

                # 记录回测
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
            # 不用i_pos+=1，因为pop后下移

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

    # 结束回测
    summary = bt.summary()
    await notifier.send(
        f"""
🏁 回测完毕
总收益: {summary['total_pnl']:.2f}
最大回撤: {summary['max_drawdown']*100:.2f}%
夏普比率: {summary['sharpe']:.2f}
总交易次数: {summary['total_trades']}
"""
    )

if __name__ == "__main__":
    asyncio.run(main())
