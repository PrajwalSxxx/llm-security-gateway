import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
SANDBOX = ROOT / "sandbox"
POLICY_PATH = ROOT / "config" / "policies.yaml"
load_dotenv(ROOT / ".env")


def load_policies() -> dict:
    try:
        with POLICY_PATH.open(encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"Unable to load policy configuration: {exc}") from exc


def setting(name: str, default: str = "") -> str:
    return os.getenv(name, default)
