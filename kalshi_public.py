import requests


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
            text = " ".join([
                str(m.get("ticker", "")),
                str(m.get("title", "")),
                str(m.get("subtitle", "")),
                str(m.get("event_ticker", "")),
            ]).lower()

            if "sol" in text and ("15" in text or "15-min" in text or "15 min" in text):
                matches.append(m)

        # Prefer the market closing soonest.
        matches.sort(key=lambda x: x.get("close_time", "9999"))
        return matches
