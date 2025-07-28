import os
import time
import logging
from dotenv import load_dotenv
from ratelimit import limits, sleep_and_retry
from rich.console import Console
from rich.table import Table
from rich.live import Live

try:
    import alpaca_trade_api as tradeapi
except Exception as e:
    raise SystemExit("alpaca-trade-api is required: pip install -r requirements.txt")

# Alpaca free tier allows 200 requests per minute
CALLS_PER_MINUTE = 180
ONE_MINUTE = 60

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.StreamHandler(),
                              logging.FileHandler('market.log')])

def env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable '{name}' not set")
    return value

@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=ONE_MINUTE)
def safe_api_call(func, *args, **kwargs):
    return func(*args, **kwargs)

class MarketStreamer:
    """Stream and display market data for a single symbol."""

    def __init__(self, symbol: str):
        api_key = env("APCA_API_KEY_ID")
        api_secret = env("APCA_API_SECRET_KEY")
        base_url = env("APCA_API_BASE_URL")
        self.api = tradeapi.REST(api_key, api_secret, base_url)
        self.symbol = symbol

    def get_trade(self):
        """Fetch the latest trade information."""
        return safe_api_call(self.api.get_latest_trade, self.symbol)

    def run(self):
        console = Console()
        table = Table(title=f"{self.symbol} Market Data")
        table.add_column("Time")
        table.add_column("Price", justify="right")
        table.add_column("Size", justify="right")

        with Live(table, console=console, refresh_per_second=1):
            while True:
                try:
                    trade = self.get_trade()
                    table.rows = []
                    ts = trade.timestamp.to_pydatetime() if hasattr(trade.timestamp, "to_pydatetime") else trade.timestamp
                    table.add_row(
                        ts.strftime("%H:%M:%S"),
                        f"{float(trade.price):.2f}",
                        str(trade.size),
                    )
                except Exception as exc:
                    logging.error(f"Error fetching trade data: {exc}")
                time.sleep(1)

def main():
    symbol = os.getenv("TRADE_SYMBOL", "AAPL")
    streamer = MarketStreamer(symbol)
    streamer.run()

if __name__ == '__main__':
    main()
