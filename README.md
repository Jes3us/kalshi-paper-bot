# Kalshi Paper Bot — v0.1

This is the first, SAFE version of the Kalshi bot project.

It does **not place real Kalshi orders**. It:
- discovers open Kalshi markets through the public API
- filters for SOL / 15-minute style markets
- records market prices
- runs a simple configurable paper-trading signal
- records simulated entries/exits in CSV
- exposes a small health/status web page for a cloud server

## Important
The strategy in `strategy.py` is a development placeholder, NOT a claim of profitability.
Do not enable real trading until the strategy has been backtested and tested in Kalshi Demo.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

Open:
http://localhost:8080

## Configuration

Copy `.env.example` to `.env`.

Useful settings:
- `MODE=paper`
- `POLL_SECONDS=5`
- `MAX_CONTRACTS=10`
- `MAX_ENTRY_PRICE=0.66`
- `TAKE_PROFIT=0.10`
- `STOP_LOSS=0.08`
- `DAILY_LOSS_LIMIT=25`

No Kalshi API key is needed for this paper-only version because public market data does not require authentication.

## Cloud deployment

This project includes a Dockerfile and can be deployed as a persistent worker/web service on a cloud provider such as Railway, Render, or a VPS.

For the first deployment, keep:
`MODE=paper`

Do NOT add a production Kalshi private key yet.
