import textwrap

import requests

from tests.api.utils import BASE_URL, auth_headers, login_user

MINIMAL_STRATEGY = textwrap.dedent(
    """
    for symbol, data in market_data.items():
        generate_signal(symbol, 'buy', 1, 'smoke test signal')
    """
)


def create_algorithm_payload(name: str):
    return {
        "name": name,
        "strategy_code": MINIMAL_STRATEGY,
        "parameters": {},
        "auto_run": False,
        "execution_interval": "manual",
        "max_positions": 5,
        "risk_per_trade": 1.0,
        "allowed_regions": ["US"],
        "allowed_trading_modes": ["paper"],
        "stock_universe": {"type": "specific", "symbols": ["AAPL"]},
    }


def test_algorithm_lifecycle(registered_user, run_log):
    login_user(registered_user)

    name = f"Smoke Algo {registered_user.username}"
    payload = create_algorithm_payload(name)
    create_resp = requests.post(
        f"{BASE_URL}/api/v1/algorithms",
        json=payload,
        headers=auth_headers(registered_user),
        timeout=10,
    )
    run_log["steps"].append({
        "action": "create_algorithm",
        "payload": payload,
        "status": create_resp.status_code,
        "response": create_resp.json() if create_resp.status_code < 500 else create_resp.text,
    })
    create_resp.raise_for_status()
    algo_id = create_resp.json()["data"]["id"]

    detail_resp = requests.get(
        f"{BASE_URL}/api/v1/algorithms/{algo_id}",
        headers=auth_headers(registered_user),
        timeout=10,
    )
    detail_resp.raise_for_status()
    run_log["steps"].append({
        "action": "algorithm_detail",
        "response": detail_resp.json(),
    })

    execute_resp = requests.post(
        f"{BASE_URL}/api/v1/algorithms/{algo_id}/execute?dry_run=true",
        headers=auth_headers(registered_user),
        timeout=10,
    )
    run_log["steps"].append({
        "action": "execute_algorithm",
        "status": execute_resp.status_code,
        "response": execute_resp.json() if execute_resp.status_code < 500 else execute_resp.text,
    })
    execute_resp.raise_for_status()

    delete_resp = requests.delete(
        f"{BASE_URL}/api/v1/algorithms/{algo_id}",
        headers=auth_headers(registered_user),
        timeout=10,
    )
    run_log["steps"].append({
        "action": "delete_algorithm",
        "status": delete_resp.status_code,
        "response": delete_resp.json() if delete_resp.status_code < 500 else delete_resp.text,
    })
    delete_resp.raise_for_status()
