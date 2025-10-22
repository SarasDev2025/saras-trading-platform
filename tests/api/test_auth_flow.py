import json

import requests

from tests.api.utils import BASE_URL, auth_headers, login_user, get_profile


def test_register_login_profile(registered_user, run_log):
    """Register a user, log in, and fetch profile data."""
    login_resp = login_user(registered_user)
    run_log["steps"].append({
        "action": "login",
        "email": registered_user.email,
        "response": login_resp,
    })

    profile_resp = get_profile(registered_user)
    run_log["steps"].append({
        "action": "profile",
        "profile": profile_resp,
    })

    assert profile_resp.get("success") is True
    registered_user.user_id = profile_resp.get("data", {}).get("id")


def test_login_invalid_password(registered_user, run_log):
    """Login with wrong password should return 401."""
    payload = {"email": registered_user.email, "password": "WrongPassword!"}
    resp = requests.post(
        f"{BASE_URL}/auth/login", json=payload, timeout=10
    )
    run_log["steps"].append({
        "action": "login_invalid",
        "status_code": resp.status_code,
        "body": resp.text,
    })
    assert resp.status_code == 401
