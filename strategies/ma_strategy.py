# quant_project/strategies/ma_strategy.py

class MAStrategy:
    def __init__(self, fast=5, slow=20):
        self.fast = fast
        self.slow = slow

    def generate_signal(self, df):
        df['ma_fast'] = df['Close'].rolling(self.fast).mean()
        df['ma_slow'] = df['Close'].rolling(self.slow).mean()
        signal = []
        for i in range(len(df)):
            if i < self.slow:
                signal.append(0)
            elif (
                df['ma_fast'].iloc[i-1] < df['ma_slow'].iloc[i-1]
                and df['ma_fast'].iloc[i] > df['ma_slow'].iloc[i]
            ):
                signal.append(1)  # buy
            elif (
                df['ma_fast'].iloc[i-1] > df['ma_slow'].iloc[i-1]
                and df['ma_fast'].iloc[i] < df['ma_slow'].iloc[i]
            ):
                signal.append(-1)  # sell
            else:
                signal.append(0)
        df['ma_signal'] = signal
        return df
