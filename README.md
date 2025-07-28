# Algo1 Trading Bot

This project provides a simple algorithmic trading bot that interacts with the Alpaca paper trading API. The bot fetches real-time market data and executes trades based on a strategy generated at runtime.

## Setup
1. Copy `.env.example` to `.env` and fill in your Alpaca credentials (and optional OpenAI key).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   This project requires `openai>=1.0` and uses the new `OpenAI` client
   interface. Older code relying on `openai.ChatCompletion` will not work.
3. Run the bot:
   ```bash
   python main.py
   ```

The default starting funds are $10,000 of paper money.

## Notes
- This bot is for paper trading only; no real money is involved.
- The API rate limit (200 requests per minute) is observed.
- The trading strategy can be generated using OpenAI if an API key is supplied; otherwise a basic random strategy is used.
