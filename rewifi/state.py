from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class JsonStateStore:
    path: Path

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def save(self, state: dict) -> None:
        self.path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def set_last_good_ssid(self, ssid: str) -> None:
        st = self.load()
        st["last_good_ssid"] = ssid
        st["last_good_at"] = _dt.datetime.now().isoformat(timespec="seconds")
        self.save(st)

    def get_last_good_ssid(self) -> str | None:
        st = self.load()
        ssid = st.get("last_good_ssid")
        return ssid if isinstance(ssid, str) and ssid.strip() else None
