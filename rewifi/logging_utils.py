from __future__ import annotations

import datetime as _dt


def log(msg: str) -> None:
    ts = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)
