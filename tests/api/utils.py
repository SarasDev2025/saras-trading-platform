import os
import uuid
from dataclasses import dataclass
from typing import Dict, Any, Optional

import requests


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@dataclass
class TestUser:
    email: str
    username: str
    password: str
    access_token: Optional[str] = None
    user_id: Optional[str] = None


def unique_user() -> TestUser:
    suffix = uuid.uuid4().hex[:8]
    return TestUser(
        email=f"cli_user_{suffix}@example.com",
        username=f"cli_user_{suffix}",
        password="TestPassword123!"
    )


def register_user(user: TestUser) -> Dict[str, Any]:
    payload = {
        "email": user.email,
        "username": user.username,
        "password": user.password,
        "first_name": "CLI",
        "last_name": "Tester",
    }
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def login_user(user: TestUser) -> Dict[str, Any]:
    payload = {"email": user.email, "password": user.password}
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    body = response.json()
    token = body.get("data", {}).get("access_token")
    if token:
        user.access_token = token
    return body


def auth_headers(user: TestUser) -> Dict[str, str]:
    if not user.access_token:
        raise RuntimeError("User not authenticated yet")
    return {"Authorization": f"Bearer {user.access_token}"}


def get_profile(user: TestUser) -> Dict[str, Any]:
    response = requests.get(
        f"{BASE_URL}/users/profile",
        headers=auth_headers(user),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
