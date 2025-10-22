from decimal import Decimal

import requests

from tests.api.utils import BASE_URL, auth_headers, login_user, get_profile


def test_add_funds_and_check_balance(registered_user, run_log):
    login_user(registered_user)
    profile = get_profile(registered_user)
    run_log["steps"].append({
        "action": "profile",
        "profile": profile,
    })

    portfolio_id = profile["data"].get("default_portfolio_id")

    payload = {"portfolio_id": portfolio_id, "amount": 5000}
    add_resp = requests.post(
        f"{BASE_URL}/portfolios/add-funds",
        json=payload,
        headers=auth_headers(registered_user),
        timeout=10,
    )
    run_log["steps"].append({
        "action": "add_funds",
        "payload": payload,
        "status": add_resp.status_code,
        "response": add_resp.json() if add_resp.status_code < 500 else add_resp.text,
    })
    add_resp.raise_for_status()

    balance_resp = requests.get(
        f"{BASE_URL}/portfolios/cash-balance",
        headers=auth_headers(registered_user),
        timeout=10,
    )
    balance_resp.raise_for_status()
    balance_body = balance_resp.json()
    run_log["steps"].append({
        "action": "cash_balance",
        "response": balance_body,
    })

    assert balance_body["success"] is True
    assert Decimal(str(balance_body["data"]["cash_balance"])) >= Decimal("5000")
