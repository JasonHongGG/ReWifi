from __future__ import annotations

import argparse
from pathlib import Path

from .logging_utils import log
from .probes import HttpProbe, PingProbe
from .state import JsonStateStore
from .wifi import NetshWifiClient, is_windows
from .watchdog import ReWifiWatchdog


DEFAULT_STATE_FILE = Path(__file__).resolve().parent.parent / "rewifi_state.json"


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="ReWifi - auto reconnect Wi-Fi when connectivity is lost")
    ap.add_argument("--interval", type=int, default=10, help="Check interval (seconds)")
    ap.add_argument(
        "--probe-mode",
        choices=["ping", "http"],
        default="ping",
        help="Connectivity probe method: ping (default) or http (HTTP/HTTPS)",
    )
    ap.add_argument("--ping-timeout-ms", type=int, default=1500, help="Ping timeout per probe (ms)")
    ap.add_argument(
        "--probes",
        default="1.1.1.1,8.8.8.8",
        help="Comma-separated probe IPs/domains (ping)",
    )
    ap.add_argument(
        "--urls",
        default="https://www.msftconnecttest.com/connecttest.txt,https://www.google.com/generate_204",
        help="Comma-separated URLs to probe when --probe-mode=http",
    )
    ap.add_argument(
        "--http-timeout-s",
        type=float,
        default=3.0,
        help="HTTP(S) timeout per URL (seconds) when --probe-mode=http",
    )
    ap.add_argument(
        "--required-successes",
        type=int,
        default=1,
        help="How many probes must succeed to treat Internet as OK",
    )
    ap.add_argument(
        "--reconnect-cooldown",
        type=int,
        default=20,
        help="Minimum seconds between reconnect attempts",
    )
    ap.add_argument(
        "--disconnect-first",
        action="store_true",
        help="Disconnect before reconnecting (sometimes helps for stuck state)",
    )
    ap.add_argument(
        "--state-file",
        default=str(DEFAULT_STATE_FILE),
        help="Path to JSON state file (stores last known-good SSID)",
    )
    return ap


def main(argv: list[str]) -> int:
    if not is_windows():
        log("This script currently targets Windows (netsh).")
        return 2

    ap = build_arg_parser()
    args = ap.parse_args(argv)

    probes = [p.strip() for p in args.probes.split(",") if p.strip()]
    urls = [u.strip() for u in args.urls.split(",") if u.strip()]

    if args.probe_mode == "ping" and not probes:
        log("ERROR: no ping probes provided")
        return 2
    if args.probe_mode == "http" and not urls:
        log("ERROR: no http urls provided")
        return 2

    if args.probe_mode == "ping":
        probe = PingProbe(targets=probes, timeout_ms=args.ping_timeout_ms, required_successes=args.required_successes)
        log(f"Probe mode: ping; probes: {probes} (required successes: {args.required_successes})")
    else:
        probe = HttpProbe(urls=urls, timeout_s=args.http_timeout_s, required_successes=args.required_successes)
        log(f"Probe mode: http; urls: {urls} (required successes: {args.required_successes})")

    wifi = NetshWifiClient()
    state = JsonStateStore(path=Path(args.state_file))

    watchdog = ReWifiWatchdog(
        wifi=wifi,
        probe=probe,
        state=state,
        interval_s=args.interval,
        reconnect_cooldown_s=args.reconnect_cooldown,
        disconnect_first=args.disconnect_first,
    )
    return watchdog.run_forever()
