from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass

from .models import WifiStatus
from .logging_utils import log


def is_windows() -> bool:
    return os.name == "nt"


def _run(cmd: list[str], timeout: int = 10) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        encoding="utf-8",
        errors="replace",
    )


def parse_netsh_interfaces(text: str) -> WifiStatus:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    def find_value(patterns: list[str]) -> str | None:
        for ln in lines:
            for p in patterns:
                m = re.match(p, ln, flags=re.IGNORECASE)
                if m:
                    val = m.group(1).strip()
                    return val if val else None
        return None

    state = find_value([
        r"^State\s*:\s*(.+)$",
        r"^狀態\s*:\s*(.+)$",
        r"^状态\s*:\s*(.+)$",
    ])

    ssid = find_value([
        r"^SSID\s*:\s*(.+)$",
        r"^SSID\s+\d+\s*:\s*(.+)$",
        r"^SSID\s*：\s*(.+)$",
    ])

    bssid = find_value([
        r"^BSSID\s*:\s*(.+)$",
        r"^BSSID\s*：\s*(.+)$",
    ])

    interface = find_value([
        r"^Name\s*:\s*(.+)$",
        r"^名稱\s*:\s*(.+)$",
        r"^名称\s*:\s*(.+)$",
    ])

    if not state:
        state = "connected" if ssid and ssid.lower() not in {"", "<none>", "none"} else "disconnected"

    if ssid and ssid.strip().lower() in {"<none>", "none"}:
        ssid = None

    log(f"Parsed Wi-Fi status: state={state}, ssid={ssid}, bssid={bssid}, interface={interface}")
    return WifiStatus(state=state.lower(), ssid=ssid, bssid=bssid, interface=interface)


@dataclass
class NetshWifiClient:
    def get_status(self) -> WifiStatus:
        cp = _run(["netsh", "wlan", "show", "interfaces"], timeout=10)
        text = (cp.stdout or "") + "\n" + (cp.stderr or "")
        return parse_netsh_interfaces(text)

    def connect(self, ssid_or_profile: str) -> tuple[bool, str]:
        cp = _run(["netsh", "wlan", "connect", f"name={ssid_or_profile}"])
        out = (cp.stdout or "") + (cp.stderr or "")
        if cp.returncode == 0:
            return True, out

        success_markers = ["successfully", "已成功", "成功"]
        if any(m.lower() in out.lower() for m in success_markers):
            return True, out

        return False, out

    def disconnect(self) -> None:
        _run(["netsh", "wlan", "disconnect"], timeout=10)
