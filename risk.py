import json
import pathlib
from datetime import date

CONFIG = json.loads(pathlib.Path("config.json").read_text())
R = CONFIG["risk"]

class RiskManager:
    def __init__(self):
        self.max_trades = int(R["max_trades_per_day"])
        self.max_daily_loss_r = float(R["max_daily_loss_r"])
        self.risk_pct = float(R["risk_per_trade_pct"])
        self._reset_day()

    def _reset_day(self):
        self.day = date.today()
        self.trades = 0
        self.realized_r = 0.0

    def can_trade(self):
        # Reset day if date changed
        if date.today() != self.day:
            self._reset_day()

        # Max trades reached?
        if self.trades >= self.max_trades:
            return False, "max_trades_reached"

        # Daily loss limit reached?
        if self.realized_r <= -self.max_daily_loss_r:
            return False, "max_daily_loss_reached"

        return True, "ok"

    def register_trade_open(self):
        if date.today() != self.day:
            self._reset_day()
        self.trades += 1

    def register_trade_close(self, r_multiple):
        if date.today() != self.day:
            self._reset_day()
        self.realized_r += r_multiple

    @staticmethod
    def calc_units(balance, entry_price, sl_price, risk_pct, is_buy=True):
        risk_amount = balance * (risk_pct / 100.0)
        sl_distance = abs(entry_price - sl_price)

        if sl_distance <= 0:
            return 0

        # XAU position sizing: units = risk / SL-distance
        units = risk_amount / sl_distance

        # Negative units for sell trades
        return int(units if is_buy else -units)
