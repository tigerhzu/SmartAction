from __future__ import annotations

import ctypes
import getpass
import json
import os
import platform
import socket
import subprocess
import time
from datetime import datetime
from typing import Any, Callable


CheckItem = dict[str, str]
CheckResult = dict[str, Any]


def run_environment_check() -> CheckResult:
    """Collect read-only environment information for support handoff."""
    started = datetime.now()
    perf_start = time.perf_counter()
    domain_info = _safe_call(_domain_info, {"domain": "Unknown", "joined": "Unknown"})
    gateway = _safe_call(_default_gateway, "Gateway not found")

    system_items = [
        _item("Windows Version", _windows_version),
        _item("Current User", _current_user),
        _item("Run as Admin", lambda: "Yes" if _is_admin() else "No"),
        _item("Computer Name", _computer_name),
        _static_item("Domain Joined", str(domain_info.get("joined", "Unknown"))),
        _static_item("Domain", str(domain_info.get("domain", "Unknown"))),
    ]

    network_items = [
        _item("IP Address", _ip_addresses),
        _static_item("Gateway", gateway or "Gateway not found"),
        _item("DNS Servers", _dns_servers),
        _item("Ping Gateway", lambda: _ping_gateway(gateway)),
        _item("DNS Resolution", _dns_resolution),
    ]

    powershell_items = [
        _item("Execution Policy", lambda: _powershell_value("Get-ExecutionPolicy")),
    ]

    firewall_items = [
        _item("Firewall Status", _firewall_status),
    ]

    return {
        "title": "SmartAction Environment Check",
        "time": started.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": round(time.perf_counter() - perf_start, 3),
        "sections": [
            {"title": "System", "items": system_items},
            {"title": "Network", "items": network_items},
            {"title": "PowerShell", "items": powershell_items},
            {"title": "Firewall", "items": firewall_items},
        ],
    }


def format_environment_check(result: CheckResult) -> str:
    lines = [
        str(result.get("title", "SmartAction Environment Check")),
        f"Time: {result.get('time', 'Unknown')}",
        "",
    ]
    for section in result.get("sections", []):
        lines.append(f"[{section.get('title', 'Unknown')}]")
        for item in section.get("items", []):
            label = item.get("label", "Unknown")
            value = item.get("value") or item.get("status") or "Unknown"
            detail = item.get("detail", "")
            if detail:
                lines.append(f"{label}: {value} ({detail})")
            else:
                lines.append(f"{label}: {value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _item(label: str, func: Callable[[], str]) -> CheckItem:
    try:
        value = func()
        return {"label": label, "value": value or "Unknown", "status": "ok", "detail": ""}
    except Exception as exc:
        return {"label": label, "value": "Unknown", "status": "failed", "detail": _brief_error(exc)}


def _static_item(label: str, value: str) -> CheckItem:
    return {"label": label, "value": value or "Unknown", "status": "ok", "detail": ""}


def _safe_call(func: Callable[[], Any], fallback: Any) -> Any:
    try:
        value = func()
        return value if value not in (None, "") else fallback
    except Exception:
        return fallback


def _brief_error(exc: Exception) -> str:
    text = str(exc).strip().replace("\r", " ").replace("\n", " ")
    return text[:160] if text else exc.__class__.__name__


def _windows_version() -> str:
    version = platform.win32_ver()
    parts = [p for p in (version[0], version[1], version[2]) if p]
    return " ".join(parts) or platform.platform()


def _current_user() -> str:
    domain = os.environ.get("USERDOMAIN", "").strip()
    user = getpass.getuser()
    return f"{domain}\\{user}" if domain else user


def _is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _computer_name() -> str:
    return os.environ.get("COMPUTERNAME") or socket.gethostname()


def _domain_info() -> dict[str, str]:
    output = _powershell_value(
        "Get-CimInstance Win32_ComputerSystem | "
        "Select-Object Domain,PartOfDomain | ConvertTo-Json -Compress"
    )
    data = json.loads(output)
    joined = "Yes" if bool(data.get("PartOfDomain")) else "No"
    return {"domain": str(data.get("Domain") or "Unknown"), "joined": joined}


def _ip_addresses() -> str:
    output = _powershell_value(
        "Get-NetIPAddress -AddressFamily IPv4 | "
        "Where-Object {$_.IPAddress -ne '127.0.0.1' -and $_.IPAddress -notlike '169.254*'} | "
        "Select-Object -ExpandProperty IPAddress"
    )
    return _join_lines(output)


def _default_gateway() -> str:
    return _powershell_value(
        "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | "
        "Sort-Object RouteMetric | Select-Object -First 1 -ExpandProperty NextHop"
    )


def _dns_servers() -> str:
    output = _powershell_value(
        "Get-DnsClientServerAddress -AddressFamily IPv4 | "
        "ForEach-Object {$_.ServerAddresses} | Where-Object {$_}"
    )
    return _join_lines(output)


def _ping_gateway(gateway: str) -> str:
    if not gateway or gateway == "Gateway not found":
        return "Gateway not found"
    proc = _run_process(["ping", "-n", "1", "-w", "1500", gateway], timeout=4)
    if proc.returncode == 0:
        return "Success"
    return "Failed"


def _dns_resolution() -> str:
    try:
        ip = socket.gethostbyname("google.com")
        return f"Success ({ip})"
    except OSError as exc:
        return f"Failed ({_brief_error(exc)})"


def _firewall_status() -> str:
    output = _powershell_value(
        "Get-NetFirewallProfile | ForEach-Object { \"$($_.Name): $($_.Enabled)\" }"
    )
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return "Unknown"
    enabled_values = []
    readable = []
    for line in lines:
        name, _, raw = line.partition(":")
        enabled = raw.strip().lower() == "true"
        enabled_values.append(enabled)
        readable.append(f"{name.strip()}: {'Enabled' if enabled else 'Disabled'}")
    if all(enabled_values):
        summary = "Enabled"
    elif not any(enabled_values):
        summary = "Disabled"
    else:
        summary = "Mixed"
    return f"{summary} ({'; '.join(readable)})"


def _powershell_value(command: str) -> str:
    proc = _run_process(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        timeout=10,
    )
    if proc.returncode != 0:
        error = (proc.stderr or proc.stdout or "PowerShell command failed").strip()
        raise RuntimeError(error)
    return (proc.stdout or "").strip()


def _run_process(args: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=flags,
    )


def _join_lines(text: str) -> str:
    values = [line.strip() for line in text.splitlines() if line.strip()]
    return ", ".join(dict.fromkeys(values)) if values else "Unknown"
