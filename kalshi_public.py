import requests
import re

PROD_BASE = "https://external-api.kalshi.com/trade-api/v2"


class KalshiPublic:
    def __init__(self, base_url: str = PROD_BASE, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_open_markets(self, limit: int = 1000):
        url = f"{self.base_url}/markets"
        params = {"limit": limit, "status": "open"}
        r = requests.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json().get("markets", [])

    def find_sol_15m(self):
        markets = self.get_open_markets()
        matches = []

        for m in markets:
            ticker = str(m.get("ticker", "")).lower()
            title = str(m.get("title", "")).lower()
            subtitle = str(m.get("subtitle", "")).lower()
            event_ticker = str(m.get("event_ticker", "")).lower()

            # Combined string for text matching
            text = f"{ticker} {title} {subtitle} {event_ticker}"

            # Regex ensures 'sol' is treated as an isolated word or a specific ticker prefix,
            # avoiding accidental matches on names like 'Axel Sola'.
            has_sol = re.search(r'\bsol\b|^sol-', text) is not None
            has_15m = any(x in text for x in ["15", "15-min", "15 min"])

            if has_sol and has_15m:
                matches.append(m)

        # Prefer the market closing soonest.
        matches.sort(key=lambda x: x.get("close_time", "9999"))
        return matches

