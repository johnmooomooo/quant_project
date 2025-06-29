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

# 策略参数范围
TUNER_PARAMS = {
    "fast_ma": [3, 5, 8],
    "slow_ma": [10, 20, 30],
    "rsi_limit": [45, 50, 55],
    "takeprofit": [0.05, 0.08],
    "stoploss": [0.02, 0.03]
}

# ===调试参数===
DEBUG = 0                    # 调试模式，True时打印更多日志
