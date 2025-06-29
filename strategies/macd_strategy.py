# quant_project/strategies/macd_strategy.py

class MACDStrategy:
    def __init__(self):
        pass

    def generate_signal(self, df):
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['dif'] = ema12 - ema26
        df['dea'] = df['dif'].ewm(span=9, adjust=False).mean()
        signal = []
        for i in range(len(df)):
            if i < 26:
                signal.append(0)
            elif (
                df['dif'].iloc[i-1] < df['dea'].iloc[i-1]
                and df['dif'].iloc[i] > df['dea'].iloc[i]
            ):
                signal.append(1)  # buy
            elif (
                df['dif'].iloc[i-1] > df['dea'].iloc[i-1]
                and df['dif'].iloc[i] < df['dea'].iloc[i]
            ):
                signal.append(-1)  # sell
            else:
                signal.append(0)
        df['macd_signal'] = signal
        return df
