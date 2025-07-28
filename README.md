# Algo1 Market Streamer

This project now focuses on streaming market data from the Alpaca API. The trading logic has been set aside so you can concentrate on monitoring real-time prices in your terminal using a small, attractive UI.

## Setup
1. Copy `.env.example` to `.env` and fill in your Alpaca credentials.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the streamer:
   ```bash
   python main.py
   ```

The UI updates once per second while staying under Alpaca's free tier limit of 200 requests per minute.

## Notes
- This project is for educational use with Alpaca's paper trading API.
- The API rate limit (200 requests per minute) is observed.
