import json
import time
from pathlib import Path
from typing import Dict, Any

import pytest

from tests.api.utils import BASE_URL, TestUser, unique_user, register_user, login_user


@pytest.fixture(scope="session")
def run_log_dir() -> Path:
    directory = Path("tests/api/output")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@pytest.fixture(scope="function")
def run_log(run_log_dir: Path, request) -> Dict[str, Any]:
    entry = {
        "test": request.node.name,
        "start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "steps": [],
    }
    yield entry
    entry["end"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    output_file = run_log_dir / f"{request.node.name}.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2)


@pytest.fixture(scope="function")
def registered_user(run_log: Dict[str, Any]) -> TestUser:
    user = unique_user()
    response = register_user(user)
    run_log["steps"].append({
        "action": "register",
        "email": user.email,
        "response": response,
        "base_url": BASE_URL,
    })
    return user
