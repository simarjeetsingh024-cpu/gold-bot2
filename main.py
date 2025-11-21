from flask import Flask, request, jsonify
from datetime import datetime
import json
import pathlib

from oanda_client import OandaClient
from risk import RiskManager
from news import is_news_blocked
from ai_filter import ai_approve

CONFIG = json.loads(pathlib.Path("config.json").read_text())
INSTRUMENT = CONFIG["oanda"]["instrument"]
RISK_PCT = CONFIG["risk"]["risk_per_trade_pct"]

app = Flask(__name__)
oanda = OandaClient()
risk = RiskManager()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/signal", methods=["POST"])
def signal():
    try:
        data = request.get_json(force=True)
        side = data["side"].upper()
        entry = float(data["entry"])
        sl = float(data["sl"])
        tp = float(data["tp"])

        now = datetime.utcnow()

        if is_news_blocked(now):
            return jsonify({"status": "blocked_news"}), 200

        ok, reason = risk.can_trade()
        if not ok:
            return jsonify({"status": "blocked_risk", "reason": reason}), 200

        ctx = {
            "side": side,
            "rr": CONFIG["risk"]["default_rr"],
            "news_block": False,
        }

        if not ai_approve(ctx):
            return jsonify({"status": "blocked_ai"}), 200

        balance = oanda.get_balance()
        is_buy = side == "BUY"
        units = RiskManager.calc_units(balance, entry, sl, RISK_PCT, is_buy=is_buy)

        if units == 0:
            return jsonify({"status": "error", "reason": "units_zero"}), 400

        code, resp = oanda.place_market_order(units, sl, tp, INSTRUMENT)
        risk.register_trade_open()

        return jsonify({
            "status": "ok",
            "http": code,
            "oanda": resp
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
