"""Example: subscribe to ticks for tokens using StreamingClient

You need instrument tokens (integers). Use client.instruments() or a mapping CSV to map symbol->token.
"""
from zerodha_py.clients.streaming import StreamingClient
import os

API_KEY = os.getenv("ZERODHA_API_KEY")
ACCESS_TOKEN = os.getenv("ZERODHA_ACCESS_TOKEN")

client = StreamingClient(API_KEY, ACCESS_TOKEN)

# replace with real instrument tokens
TOKENS = [738561, 408065]  # example tokens


def on_ticks(ticks):
    print("Ticks:", ticks)

client.subscribe(TOKENS, on_ticks)

# keep alive in simple example
import time
try:
    while T