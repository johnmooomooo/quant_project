import backtrader as bt

class PanicRebound(bt.Strategy):
    params = dict(
        panic_drop_pct=0.05,     # 恐慌跌幅阈值 5%
        panic_vol_ratio=1.5,     # 恐慌放量阈值
        hold_days=5,             # 最多持仓天数
        takeprofit=0.03,         # 3%止盈
        stoploss=0.03,           # 3%止损
    )

    def __init__(self):
        self.bbands = dict()
        for d in self.datas:
            self.bbands[d._name] = bt.indicators.BollingerBands(d.close, period=20)

    def next(self):
        for d in self.datas:
            name = d._name
            pos = self.getposition(d)
            
            if not pos:
                if len(d) < 21:
                    continue  # 因为布林带20期需要足够数据

                avg_vol = sum(d.volume.get(size=5)) / 5
                drop_pct = (d.close[-1] - d.close[0]) / d.close[-1]
                bb_bot = self.bbands[name].bot[0]
                

                panic = (
                    drop_pct < -self.p.panic_drop_pct
                    and d.volume[0] > avg_vol * self.p.panic_vol_ratio
                    #and d.close[0] < bb_bot
                )

                if panic:
                    self.buy(data=d, size=100)
                    self.entry_price = d.close[0]
                    self.entry_bar = len(d)
                    print(f"✅ [{name}] 恐慌买入: {d.datetime.date(0)} @ {d.close[0]:.2f}")
            
            else:
                # 持仓逻辑
                bars_held = len(d) - self.entry_bar
                pnl = (d.close[0] - self.entry_price) / self.entry_price

                if pnl > self.p.takeprofit:
                    self.close(data=d)
                    print(f"🎯 [{name}] 止盈卖出: {d.datetime.date(0)} @ {d.close[0]:.2f}")
                elif pnl < -self.p.stoploss:
                    self.close(data=d)
                    print(f"🛑 [{name}] 止损卖出: {d.datetime.date(0)} @ {d.close[0]:.2f}")
                elif bars_held >= self.p.hold_days:
                    self.close(data=d)
                    print(f"⏰ [{name}] 超时卖出: {d.datetime.date(0)} @ {d.close[0]:.2f}")
