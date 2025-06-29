# quant_project/config.py

# Telegram 配置
TELEGRAM_BOT_TOKEN = "7846355348:AAHrBeY2nuAYU1Edd5SipObRwC2M0swzcW8"
TELEGRAM_CHAT_ID = 8168231390

# ===账户参数===
INITIAL_CAPITAL = 100_000      # 初始账户本金
ALLOCATE_PERCENTAGE = 0.3      # 每次交易最多使用多少比例资金
MAX_PER_TRADE = 20_000         # 单次最大下单金额
TAKE_PROFIT_PCT = 0.05         # 止盈百分比（5%获利止盈）
STOP_LOSS_PCT = 0.02           # 止损百分比（2%止损）
SLIPPAGE_RATE = 0.001          # 滑点比例（千分之一）
COMMISSION_RATE = 0.001        # 佣金比例（千分之一）

# ===数据源配置===
SYMBOLS = ["0700.HK", "AAPL", "TSLA"]
INTERVAL = "5m"
PERIOD = "5d"


# ===策略启用开关===
USE_MA = True
USE_RSI = 0
USE_MACD = 0


# ===策略参数===
MA_FAST = 3                    # 均线快速线周期
MA_SLOW = 6                    # 均线慢速线周期

RSI_BUY_THRESHOLD = 50         # RSI买入阈值
RSI_SELL_THRESHOLD = 55        # RSI卖出阈值

# ===调优参数===
TUNER_PARAMS = {
    "ma_fast_range": [3, 4, 5],   # 均线快速期可调范围
    "ma_slow_range": [8, 12, 20], # 均线慢速期可调范围
    "rsi_buy_range": [40, 45, 50],# RSI买入阈值范围
    "rsi_sell_range": [55, 60, 65],# RSI卖出阈值范围
}

# ===调试参数===
DEBUG = True                    # 调试模式，True时打印更多日志

