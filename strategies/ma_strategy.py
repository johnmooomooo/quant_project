class MAStrategy:
    def __init__(self, fast=3, slow=10):
        self.fast = fast
        self.slow = slow

    def generate_signal(self, df):
        df['ma_fast'] = df['Close'].rolling(self.fast).mean()
        df['ma_slow'] = df['Close'].rolling(self.slow).mean()
        signal = []
        for i in range(len(df)):
            if i < self.slow:
                signal.append(0)
            elif df['ma_fast'].iloc[i-1] <= df['ma_slow'].iloc[i-1] and df['ma_fast'].iloc[i] > df['ma_slow'].iloc[i]:
                signal.append(1)   # 金叉
            elif df['ma_fast'].iloc[i-1] >= df['ma_slow'].iloc[i-1] and df['ma_fast'].iloc[i] < df['ma_slow'].iloc[i]:
                signal.append(-1)  # 死叉
            else:
                signal.append(0)
        df['ma_signal'] = signal

        # 验证
        print(df[['Close','ma_fast','ma_slow','ma_signal']].tail(20))

        return df
