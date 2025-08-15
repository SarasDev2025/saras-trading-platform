from kiteconnect import KiteConnect
from typing import Dict, Any


class MarketDataClient:
    def __init__(self, api_key: str, access_token: str):
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)

    def get_historical(self, symbol: str, from_date: str, to_date: str, interval: str = "5minute") -> Dict[str, Any]:
        """Wrapper for historical_data.

        interval examples: 'minute', '3minute', '5minute', '10minute', 'day'
        from_date/to_date are ISO strings (YYYY-MM-DD or datetimes)
        """
        return self.kite.historical_data(instrument_token=self._token_for_symbol(symbol), from_date=from_date, to_date=to_date, interval=interval)

    def _token_for_symbol(self, symbol: str) -> int:
        # Placeholder. To use historical_data you need instrument token. Users may map symbol->token via instruments() list
        raise NotImplementedError("Map symbol to instrument_token first (use /instruments/ endpoint or CSV mapping)")

    def ltp(self, instruments: list):
        return self.kite.ltp(instruments)

    def instruments(self, exchange: str = "NSE"):
        return self.kite.instruments(exchange)