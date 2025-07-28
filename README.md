# Algo1 Trading Bot

This project provides a simple algorithmic trading bot that interacts with the Alpaca paper trading API. The bot fetches real-time market data and executes trades based on a strategy generated at runtime. A small Tkinter GUI displays the current price, recent strategy decision and your portfolio while the bot runs.

## Setup
1. Copy `.env.example` to `.env` and fill in your Alpaca credentials (and optional OpenAI key).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot to launch the GUI:
   ```bash
   python main.py
   ```

The default starting funds are $10,000 of paper money. When the application
starts a small GUI window displays the live price, the last trading decision,
your current portfolio and a slider to control how often data is refreshed.

## Notes
- This bot is for paper trading only; no real money is involved.
- The API rate limit (200 requests per minute) is observed.
- The trading strategy can be generated using OpenAI if an API key is supplied; otherwise a basic random strategy is used.
