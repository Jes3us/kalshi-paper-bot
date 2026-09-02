import os
import threading
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify

from kalshi_public import KalshiPublic
from paper import PaperTrader
from strategy import PaperStrategy

load_dotenv()

MODE = os.getenv("MODE", "paper").lower()
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "5"))
MAX_CONTRACTS = int(os.getenv("MAX_CONTRACTS", "10"))
MAX_ENTRY_PRICE = float(os.getenv("MAX_ENTRY_PRICE", "0.66"))
TAKE_PROFIT = float(os.getenv("TAKE_PROFIT", "0.10"))
STOP_LOSS = float(os.getenv("STOP_LOSS", "0.08"))
DAILY_LOSS_LIMIT = float(os.getenv("DAILY_LOSS_LIMIT", "25"))
PORT = int(os.getenv("PORT", "8080"))

app = Flask(__name__)

state = {
    "mode": MODE,
    "started": datetime.now(timezone.utc).isoformat(),
    "last_market": None,
    "last_price": None,
    "last_signal": None,
    "position": None,
    "error": None,
}

api = KalshiPublic()
strategy = PaperStrategy(MAX_ENTRY_PRICE)
trader = PaperTrader(
    max_contracts=MAX_CONTRACTS,
    take_profit=TAKE_PROFIT,
    stop_loss=STOP_LOSS,
    daily_loss_limit=DAILY_LOSS_LIMIT,
)


def trading_loop():
    previous_prices = {}

    while True:
        try:
            matches = api.find_sol_15m()

            if not matches:
                state["error"] = "No SOL/15-minute market found right now."
                time.sleep(POLL_SECONDS)
                continue

            market = matches[0]
            ticker = market["ticker"]
            
            # Kalshi returns price as a float string or 0. Parse safely.
            raw_price = market.get("yes_ask_dollars")
            price = float(raw_price) if raw_price is not None else 0.0

            # LIQUIDITY SAFEGUARD: Skip market evaluation if order book is empty
            if price <= 0.0:
                state["error"] = f"Market {ticker} found, but there is currently zero liquidity (YES ask is $0.00)."
                time.sleep(POLL_SECONDS)
                continue

            previous = previous_prices.get(ticker)
            signal = strategy.evaluate(market, previous)

            previous_prices[ticker] = price

            state["last_market"] = {
                "ticker": ticker,
                "title": market.get("title"),
                "close_time": market.get("close_time"),
            }
            state["last_price"] = price
            state["last_signal"] = {
                "action": signal.action,
                "side": signal.side,
                "confidence": signal.confidence,
                "reason": signal.reason,
            }
            state["error"] = None

            if trader.position:
                trader.update(ticker, price)

            if MODE == "paper" and signal.action == "BUY":
                trader.enter(ticker, signal.side, price, signal.reason)

            state["position"] = trader.position

            print(
                f"[{datetime.now().isoformat(timespec='seconds')}] "
                f"{ticker} YES ask={price:.4f} "
                f"signal={signal.action} {signal.reason}"
            )

        except Exception as exc:
            state["error"] = str(exc)
            print("ERROR:", exc)

        time.sleep(POLL_SECONDS)


@app.get("/")
def home():
    position = state["position"]
    return f"""
    <html>
      <head>
        <title>Kalshi Paper Bot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {{ font-family: Arial; max-width: 760px; margin: 40px auto; padding: 20px; }}
          .card {{ border: 1px solid #ddd; border-radius: 14px; padding: 18px; margin: 12px 0; }}
          .green {{ color: #087f23; }}
        </style>
      </head>
      <body>
        <h1>Kalshi Bot</h1>
        <div class="card"><b>Mode:</b> <span class="green">{MODE.upper()}</span></div>
        <div class="card"><b>Market:</b> {state["last_market"]}</div>
        <div class="card"><b>YES ask:</b> {state["last_price"]}</div>
        <div class="card"><b>Signal:</b> {state["last_signal"]}</div>
        <div class="card"><b>Position:</b> {position}</div>
        <div class="card"><b>Error:</b> {state["error"]}</div>
        <p>Paper-only development build. No real orders are sent.</p>
      </body>
    </html>
    """


@app.get("/api/status")
def status():
    return jsonify(state)


if __name__ == "__main__":
    t = threading.Thread(target=trading_loop, daemon=True)
    t.start()

    # 0.0.0.0 is required for most cloud hosting platforms.
    app.run(host="0.0.0.0", port=PORT)
