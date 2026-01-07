from __future__ import annotations

import re
import subprocess
import urllib.request
from dataclasses import dataclass


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


class ConnectivityProbe:
    """A connectivity probe returns True when Internet is considered OK."""

    def ok(self) -> bool:  # pragma: no cover
        raise NotImplementedError


@dataclass
class PingProbe(ConnectivityProbe):
    targets: list[str]
    timeout_ms: int = 1500
    required_successes: int = 1

    def _ping_ok(self, host: str) -> bool:
        cp = _run(["ping", "-n", "1", "-w", str(self.timeout_ms), host], timeout=max(3, self.timeout_ms // 1000 + 2))
        out = (cp.stdout or "") + (cp.stderr or "")
        if cp.returncode == 0:
            return True
        return bool(re.search(r"TTL=\d+", out, flags=re.IGNORECASE))

    def ok(self) -> bool:
        successes = 0
        for host in self.targets:
            if self._ping_ok(host):
                successes += 1
                if successes >= self.required_successes:
                    return True
        return False


@dataclass
class HttpProbe(ConnectivityProbe):
    urls: list[str]
    timeout_s: float = 3.0
    required_successes: int = 1

    def _http_ok(self, url: str) -> bool:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "ReWifi/1.0 (Windows; ConnectivityCheck)",
                "Cache-Control": "no-cache",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                status = getattr(resp, "status", None)
                if status is None:
                    status = resp.getcode()
                return 200 <= int(status) < 400
        except Exception:
            return False

    def ok(self) -> bool:
        successes = 0
        for url in self.urls:
            if self._http_ok(url):
                successes += 1
                if successes >= self.required_successes:
                    return True
        return False
