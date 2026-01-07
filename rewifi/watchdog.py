from __future__ import annotations

import time
from dataclasses import dataclass

from .logging_utils import log
from .models import WifiStatus
from .probes import ConnectivityProbe
from .state import JsonStateStore
from .wifi import NetshWifiClient


@dataclass
class ReWifiWatchdog:
    wifi: NetshWifiClient
    probe: ConnectivityProbe
    state: JsonStateStore
    interval_s: int = 10
    reconnect_cooldown_s: int = 20
    disconnect_first: bool = False

    def _should_reconnect(self, status: WifiStatus) -> tuple[bool, str]:
        if status.state != "connected" or not status.ssid:
            return True, "Wi-Fi is disconnected"

        if not self.probe.ok():
            return True, "Wi-Fi connected but connectivity probe failed"

        return False, "OK"

    def run_forever(self) -> int:
        last_reconnect_at: float = 0.0

        log("ReWifi started")
        log(f"State file: {self.state.path}")

        while True:
            try:
                status = self.wifi.get_status()
                needs, reason = self._should_reconnect(status)

                if not needs:
                    if status.ssid:
                        self.state.set_last_good_ssid(status.ssid)
                    time.sleep(self.interval_s)
                    continue

                now = time.time()
                if now - last_reconnect_at < self.reconnect_cooldown_s:
                    log(f"Connectivity issue ({reason}), but in cooldown")
                    time.sleep(self.interval_s)
                    continue

                target = status.ssid or self.state.get_last_good_ssid()
                if not target:
                    log(f"Connectivity issue ({reason}), but no SSID to reconnect")
                    time.sleep(self.interval_s)
                    continue

                log(f"Connectivity issue: {reason}. Reconnecting to: {target}")
                last_reconnect_at = now

                if self.disconnect_first:
                    self.wifi.disconnect()
                    time.sleep(2)

                ok, out = self.wifi.connect(target)
                if not ok:
                    log("Reconnect command failed (netsh). Will retry later.")
                    if out.strip():
                        log(out.strip())
                    time.sleep(self.interval_s)
                    continue

                time.sleep(3)

            except KeyboardInterrupt:
                log("Stopped")
                return 0
            except Exception as e:
                log(f"ERROR: {e}")
                time.sleep(self.interval_s)
