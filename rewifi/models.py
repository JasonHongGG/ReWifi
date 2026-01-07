from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WifiStatus:
    state: str  # e.g. connected/disconnected
    ssid: str | None
    bssid: str | None
    interface: str | None
