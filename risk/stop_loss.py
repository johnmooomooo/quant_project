# quant_project/risk/stop_loss.py

import config

def check_stop_loss(entry_price, current_price):
    loss_pct = (current_price - entry_price) / entry_price
    return loss_pct <= -config.STOP_LOSS_PCT
