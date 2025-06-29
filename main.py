import pandas as pd

df = pd.read_csv("AAPL.csv", index_col=0, parse_dates=True)

for i in range(5, len(df)):
    drop_pct = (df['Close'].iloc[i-1] - df['Close'].iloc[i]) / df['Close'].iloc[i-1]
    avg_vol = df['Volume'].iloc[i-5:i].mean()
    if (
        drop_pct >= 0.05
    ):
        print(f"{df.index[i]}: drop={drop_pct:.2%}, vol={df['Volume'].iloc[i]:.0f}, avg_vol={avg_vol:.0f}")
