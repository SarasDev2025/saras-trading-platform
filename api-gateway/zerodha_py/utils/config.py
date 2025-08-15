from pathlib import Path
import json
from typing import Optional

CONFIG_PATH = Path.home() / ".zerodha_py"


def save_config(data: dict, path: Optional[Path] = None) -> None:
    path = path or CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def load_config(path: Optional[Path] = None) -> dict:
    path = path or CONFIG_PATH
    if not path.exists():
        return {}
    return json.loads(path.read_text())