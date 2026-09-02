import csv
from datetime import datetime, timezone
from pathlib import Path


class PaperTrader:
    def __init__(self, max_contracts=10, take_profit=0.10, stop_loss=0.08,
                 daily_loss_limit=25, data_dir="data"):
        self.max_contracts = max_contracts
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.daily_loss_limit = daily_loss_limit
        self.position = None

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.trade_file = self.data_dir / "paper_trades.csv"

        if not self.trade_file.exists():
            with self.trade_file.open("w", newline="") as f:
                csv.writer(f).writerow([
                    "timestamp", "market", "action", "side", "contracts",
                    "price", "pnl", "reason"
                ])

    def _log(self, market, action, side, contracts, price, pnl, reason):
        with self.trade_file.open("a", newline="") as f:
            csv.writer(f).writerow([
                datetime.now(timezone.utc).isoformat(),
                market, action, side, contracts, f"{price:.4f}",
                f"{pnl:.4f}", reason
            ])

    def enter(self, market, side, price, reason):
        if self.position is not None:
            return False

        cost = price * self.max_contracts
        self.position = {
            "market": market,
            "side": side,
            "contracts": self.max_contracts,
            "entry": price,
            "cost": cost,
        }

        self._log(
            market, "BUY", side, self.max_contracts, price, 0.0, reason
        )
        return True

    def update(self, market, current_price):
        p = self.position
        if not p or p["market"] != market:
            return None

        pnl_per_contract = current_price - p["entry"]
        pnl = pnl_per_contract * p["contracts"]

        if pnl_per_contract >= self.take_profit:
            self._close(current_price, pnl, "take-profit")
            return "TAKE_PROFIT"

        if pnl_per_contract <= -self.stop_loss:
            self._close(current_price, pnl, "stop-loss")
            return "STOP_LOSS"

        return None

    def _close(self, price, pnl, reason):
        p = self.position
        self._log(
            p["market"], "SELL", p["side"], p["contracts"],
            price, pnl, reason
        )
        self.position = None
