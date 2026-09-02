import requests
import re

# Correct fixed production endpoint
PROD_BASE = "https://kalshi.com"


class KalshiPublic:
    def __init__(self, base_url: str = PROD_BASE, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_open_markets(self, limit: int = 1000):
        # Explicitly building the full URL path to avoid local context redirection overrides
        url = f"{PROD_BASE}/markets"
        params = {"limit": limit, "status": "open"}
        
        # Add basic headers so Kalshi recognizes the bot browser agent safely
        headers = {"Accept": "application/json"}
        
        r = requests.get(url, params=params, headers=headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json().get("markets", [])

    def find_sol_15m(self):
        try:
            markets = self.get_open_markets()
        except Exception as e:
            # If rate limited, bubble up the clean message
            raise RuntimeError(f"Kalshi API connection rate-limited or blocked: {e}")
            
        matches = []

        for m in markets:
            ticker = str(m.get("ticker", "")).lower()
            title = str(m.get("title", "")).lower()
            subtitle = str(m.get("subtitle", "")).lower()
            event_ticker = str(m.get("event_ticker", "")).lower()

            text = f"{ticker} {title} {subtitle} {event_ticker}"

            # Standalone word boundaries or explicit system asset code prefixes
            has_sol = re.search(r'\bsol\b|^sol-|^kxsol', text) is not None
            has_15m = any(x in text for x in ["15", "15-min", "15 min", "15m"])

            if has_sol and has_15m:
                matches.append(m)

        matches.sort(key=lambda x: x.get("close_time", "9999"))
        return matches
