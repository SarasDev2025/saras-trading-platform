from kiteconnect import KiteConnect
from .config import save_config, load_config
from typing import Dict


def get_kite_client(api_key: str, api_secret: str = None, access_token: str = None) -> KiteConnect:
    """Return a configured KiteConnect instance. If access_token is given it will be set.

    Note: to obtain access_token, follow the normal Kite flow: build login url, user logs in,
    you receive request_token, then exchange with generate_session.
    """
    kite = KiteConnect(api_key=api_key)
    if access_token:
        kite.set_access_token(access_token)
    return kite


def exchange_request_token(api_key: str, api_secret: str, request_token: str) -> Dict:
    """Exchange request_token for access_token and refreshable credentials.

    Returns the dict returned by generate_session: {"access_token":..., "public_token":...}
    """
    kite = KiteConnect(api_key=api_key)
    data = kite.generate_session(request_token, api_secret)
    # optionally save data
    cfg = load_config()
    cfg.update({"api_key": api_key, "api_secret": api_secret})
    cfg.update(data)
    save_config(cfg)
    return data