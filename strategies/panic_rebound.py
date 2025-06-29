import backtrader as bt

class PanicRebound(bt.Strategy):
    params = dict(
        panic_drop_pct = 0.02,     # 当日下跌超5%
        panic_vol_ratio = 1.0,     # 当日成交量大于过去5日均量的1.5倍
        hold_days = 5,             # 最长持有5天
        takeprofit = 0.03,         # 止盈3%
        stoploss = 0.03,           # 止损3%
    )

    def __init__(self):
        self.bbands = dict()
        self.buy_signal = dict()
        self.hold_counter = dict()
        self.entry_prices = dict()
        
        for d in self.datas:
            self.bbands[d._name] = bt.indicators.BollingerBands(d.close, period=20)
            self.buy_signal[d._name] = False
            self.hold_counter[d._name] = 0
            self.entry_prices[d._name] = 0

    def next(self):
        for d in self.datas:
            pos = self.getposition(d)
            name = d._name
            
            if not pos:
                # 过去5日平均量
                if len(d) < 5:
                    continue
                avg_vol = sum(d.volume.get(size=5)) / 5
                
                # 当天跌幅
                drop_pct = (d.close[-1] - d.close[0]) / d.close[-1]
                
                # 是否恐慌
                panic = (
                    drop_pct < -self.p.panic_drop_pct and
                    d.volume[0] > avg_vol * self.p.panic_vol_ratio and
                    d.close[0] < self.bbands[name].bot[0]
                )
                
                if panic:
                    self.buy(data=d, size=100)
                    self.entry_prices[name] = d.close[0]
                    self.hold_counter[name] = 0
                    print(f"[DEBUG] {name} drop_pct={drop_pct:.2%}, vol={d.volume[0]:.0f}, avg_vol={avg_vol:.0f}, bb_bot={self.bbands[name].bot[0]:.2f}, close={d.close[0]:.2f}")
                    print(f"✅ [{name}] 触发恐慌买入 {d.datetime.date(0)} @ {d.close[0]:.2f}")
                    
            else:
                self.hold_counter[name] += 1
                price_now = d.close[0]
                entry = self.entry_prices[name]
                
                if price_now >= entry * (1 + self.p.takeprofit):
                    print(f"🎯 [{name}] 止盈卖出 {d.datetime.date(0)} @ {price_now:.2f}")
                    self.close(data=d)
                elif price_now <= entry * (1 - self.p.stoploss):
                    print(f"⚠️ [{name}] 止损卖出 {d.datetime.date(0)} @ {price_now:.2f}")
                    self.close(data=d)
                elif self.hold_counter[name] >= self.p.hold_days:
                    print(f"⏰ [{name}] 超时平仓 {d.datetime.date(0)} @ {price_now:.2f}")
                    self.close(data=d)
