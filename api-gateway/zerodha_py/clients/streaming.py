from kiteconnect import KiteTicker
from threading import Thread
from typing import Callable, List


class StreamingClient:
    def __init__(self, api_key: str, access_token: str):
        self.kws = KiteTicker(api_key, access_token)
        self._thread = None

    def _start_loop(self):
        self.kws.connect()

    def subscribe(self, tokens: List[int], on_ticks: Callable[[list], None]):
        """Subscribe to instrument tokens (list of ints). on_ticks is called with list of ticks."""

        def _on_ticks(ws, ticks):
            on_ticks(ticks)

        self.kws.on_ticks = _on_ticks
        self.kws.on_connect = lambda ws, response: ws.subscribe(tokens)

        # run the websocket in a background thread so it doesn't block
        self._thread = Thread(target=self._start_loop, daemon=True)
        self._thread.start()

    def close(self):
        try:
            self.kws.close()
        except Exception:
            pass