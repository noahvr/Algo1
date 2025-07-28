import os
import logging
import tkinter as tk

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

    def get_portfolio_str(self) -> str:
        account = safe_api_call(self.api.get_account)
        positions = safe_api_call(self.api.list_positions)
        lines = [f"Cash: {account.cash}", "Positions:"]
        for p in positions:
            lines.append(f"{p.symbol} {p.qty} @ {p.current_price}")
        return "\n".join(lines)

    def step(self) -> tuple[str, float]:
        price = self.get_price()
        decision = self.ai.generate_trade(price)
        logging.info(f"Price: {price:.2f} Decision: {decision}")
        if decision in {'buy', 'sell'}:
            self.submit_order(decision, qty=1)
        return decision, price


class TradingApp:
    def __init__(self, trader: Trader):
        self.trader = trader
        self.root = tk.Tk()
        self.root.title("Algo1 Trading Bot")

        self.price_var = tk.StringVar(value="Price: --")
        tk.Label(self.root, textvariable=self.price_var, font=("Arial", 16)).pack()

        self.strategy_var = tk.StringVar(value="Decision: --")
        tk.Label(self.root, textvariable=self.strategy_var, font=("Arial", 14)).pack()

        tk.Label(self.root, text="Update Interval (seconds)").pack()
        self.interval_var = tk.IntVar(value=60)
        tk.Scale(
            self.root,
            from_=5,
            to=300,
            orient=tk.HORIZONTAL,
            variable=self.interval_var,
        ).pack(fill="x")

        tk.Label(self.root, text="Portfolio").pack()
        self.portfolio_text = tk.Text(self.root, height=10, width=50)
        self.portfolio_text.pack()

        self.update_data()

    def update_data(self):
        try:
            decision, price = self.trader.step()
            self.price_var.set(f"Price: {price:.2f}")
            self.strategy_var.set(f"Decision: {decision}")
            portfolio = self.trader.get_portfolio_str()
            self.portfolio_text.delete(1.0, tk.END)
            self.portfolio_text.insert(tk.END, portfolio)
        except Exception as exc:
            logging.error(f"GUI update error: {exc}")

        interval = self.interval_var.get()
        self.root.after(interval * 1000, self.update_data)

    def run(self):
        self.root.mainloop()

def main():
    symbol = os.getenv('TRADE_SYMBOL', 'AAPL')
    trader = Trader(symbol)
    app = TradingApp(trader)
    app.run()

if __name__ == '__main__':
    main()
