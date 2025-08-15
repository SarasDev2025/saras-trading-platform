"""Example: place a market order using TradingClient

Before running:
- Set API_KEY and ACCESS_TOKEN environment variables or replace in code.
- Obtain access_token using the login flow and exchange_request_token helper.
"""
from zerodha_py.clients.trading import TradingClient
from zerodha_py.model.orders import MarketOrderRequest
import os



from dotenv import load_dotenv

# Load the .env file
load_dotenv("SetUp.env")  # file name or full path

# Read values
API_KEY = os.getenv("ZERODHA_API_KEY")
ACCESS_TOKEN = os.getenv("ZERODHA_ACCESS_TOKEN")

print("API_KEY:", API_KEY)
print("ACCESS_TOKEN:", ACCESS_TOKEN)



if not API_KEY or not ACCESS_TOKEN:
    raise SystemExit("Set ZERODHA_API_KEY and ZERODHA_ACCESS_TOKEN environment variables")

client = TradingClient(api_key=API_KEY, access_token=ACCESS_TOKEN)

req = MarketOrderRequest(symbol="VIKASECO", side="BUY", qty=1, product="CNC")
res = client.place_market_order(req)
print("Placed:", res)