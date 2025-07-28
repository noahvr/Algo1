import os
import time
import logging
from dotenv import load_dotenv
from ratelimit import limits, sleep_and_retry

try:
    import alpaca_trade_api as tradeapi
except Exception as e:
    raise SystemExit("alpaca-trade-api is required: pip install -r requirements.txt")

try:
    import openai
except Exception:
    openai = None

# Alpaca free tier allows 200 requests per minute
CALLS_PER_MINUTE = 180
ONE_MINUTE = 60

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.StreamHandler(),
                              logging.FileHandler('trades.log')])

def env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable '{name}' not set")
    return value

@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=ONE_MINUTE)
def safe_api_call(func, *args, **kwargs):
    return func(*args, **kwargs)

class AIAgent:
    def __init__(self):
        self.use_openai = openai is not None and os.getenv('OPENAI_API_KEY')
        if self.use_openai:
            openai.api_key = os.getenv('OPENAI_API_KEY')

    def generate_trade(self, last_price: float) -> str:
        if self.use_openai:
            prompt = (
                f"The current price of the asset is {last_price}. "
                "Should we 'buy', 'sell', or 'hold'?"
            )
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1,
                )
                decision = response.choices[0].message["content"].strip().lower()
                if decision not in {"buy", "sell", "hold"}:
                    decision = "hold"
            except Exception as exc:
                logging.error(f"OpenAI error: {exc}")
                decision = "hold"
        else:
            import random
            decision = random.choice(["buy", "sell", "hold"])
        return decision

class Trader:
    def __init__(self, symbol: str):
        api_key = env('APCA_API_KEY_ID')
        api_secret = env('APCA_API_SECRET_KEY')
        base_url = env('APCA_API_BASE_URL')
        self.api = tradeapi.REST(api_key, api_secret, base_url)
        self.symbol = symbol
        self.ai = AIAgent()

    def get_price(self) -> float:
        trade = safe_api_call(self.api.get_latest_trade, self.symbol)
        return float(trade.price)

    def submit_order(self, side: str, qty: int):
        logging.info(f"Submitting {side} order for {qty} {self.symbol}")
        safe_api_call(
            self.api.submit_order,
            symbol=self.symbol,
            qty=qty,
            side=side,
            type='market',
            time_in_force='gtc',
        )

    def run(self):
        logging.info("Starting trading loop")
        while True:
            try:
                price = self.get_price()
                decision = self.ai.generate_trade(price)
                logging.info(f"Price: {price:.2f} Decision: {decision}")
                if decision in {'buy', 'sell'}:
                    self.submit_order(decision, qty=1)
            except Exception as e:
                logging.error(f"Error during trading loop: {e}")
            time.sleep(60)

def main():
    symbol = os.getenv('TRADE_SYMBOL', 'AAPL')
    trader = Trader(symbol)
    trader.run()

if __name__ == '__main__':
    main()
