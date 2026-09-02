from dataclasses import dataclass
from typing import Optional


@dataclass
class Signal:
    action: str                 # "BUY" or "HOLD"
    side: str                   # "yes" or "no"
    confidence: float
    reason: str


class PaperStrategy:
    """
    DEVELOPMENT-ONLY strategy.

    This is deliberately conservative and simple:
    - It does NOT claim to predict SOL.
    - It uses short-term movement in the Kalshi market price only.
    - It exists so the plumbing can be tested before a real predictive model
      is introduced.

    A real strategy should compare an independent SOL price/forecast to the
    Kalshi contract's strike and time remaining, then estimate fair probability.
    """

    def __init__(self, max_entry_price: float = 0.66):
        self.max_entry_price = max_entry_price

    def evaluate(self, market: dict, previous_price: Optional[float]) -> Signal:
        price = float(market.get("yes_ask_dollars") or 0)

        if not price:
            return Signal("HOLD", "yes", 0.0, "No usable YES ask price")

        if previous_price is None:
            return Signal("HOLD", "yes", 0.0, "Waiting for another price sample")

        change = price - previous_price

        # Placeholder signal only: a small downward move is NOT a validated edge.
        if price <= self.max_entry_price and change <= -0.01:
            confidence = min(0.60, 0.50 + abs(change))
            return Signal(
                "BUY",
                "yes",
                confidence,
                f"Placeholder: YES ask fell {abs(change):.3f}"
            )

        return Signal("HOLD", "yes", 0.0, "No paper-trade condition met")
