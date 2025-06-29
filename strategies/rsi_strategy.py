# quant_project/strategies/rsi_strategy.py

class RSIStrategy:
    def __init__(self, buy_th=30, sell_th=70):
        self.buy_th = buy_th
        self.sell_th = sell_th

    def generate_signal(self, df):
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - 100/(1 + rs)
        signal = []
        for i in range(len(df)):
            if pd.isna(df['rsi'].iloc[i]):
                signal.append(0)
            elif df['rsi'].iloc[i] < self.buy_th:
                signal.append(1)
            elif df['rsi'].iloc[i] > self.sell_th:
                signal.append(-1)
            else:
                signal.append(0)
        df['rsi_signal'] = signal
        return df
