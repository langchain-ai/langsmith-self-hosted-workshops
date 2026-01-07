from __future__ import annotations
import os
from datetime import date

def ok(msg: str) -> None:
    print(f"✅ {msg}")

def warn(msg: str) -> None:
    print(f"⚠️  {msg}")

def fail(msg: str) -> None:
    raise RuntimeError(f"❌ {msg}")

def require_env(*keys: str) -> dict:
    cfg = {}
    missing = []
    for k in keys:
        v = os.environ.get(k, "").strip()
        if not v:
            missing.append(k)
        cfg[k] = v
        if k == 'CLUSTER_NAME':
            # Add a hardcoded prefix to the cluster name
            cfg[k] = f"langsmith-workshop-{date.today().strftime('%Y%m%d')}-{v}"
    if missing:
        fail(f"Missing required environment variables: {', '.join(missing)}")
    return cfg

def redact(value: str, keep: int = 4) -> str:
    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return f"{value[:keep]}…({'*' * 8})"

def print_config(config: dict, redact_keys: set[str] | None = None) -> None:
    redact_keys = redact_keys or set()
    print("### Config (redacted)")
    for k, v in config.items():
        if k in redact_keys:
            print(f"- {k}: {redact(str(v))}")
        else:
            print(f"- {k}: {v}")
