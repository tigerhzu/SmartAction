from __future__ import annotations

import ctypes
import re
import subprocess
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class PowerShellRunResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int | None
    duration_seconds: float
    friendly_error: str = ""


def is_user_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def render_script(script_content: str, values: dict[str, str]) -> str:
    rendered = script_content
    for name, value in values.items():
        rendered = rendered.replace("{{" + name + "}}", value)
    return rendered


def mask_secret_values(text: str, values: dict[str, str], parameters: list[dict[str, Any]]) -> str:
    masked = text
    for param in parameters:
        if param.get("type") != "password":
            continue
        value = values.get(str(param.get("name", "")), "")
        if value:
            masked = masked.replace(value, "******")
    return masked


def mask_script_preview(script_content: str, values: dict[str, str], parameters: list[dict[str, Any]]) -> str:
    masked_values = dict(values)
    for param in parameters:
        if param.get("type") == "password":
            masked_values[str(param.get("name", ""))] = "******"
    return render_script(script_content, masked_values)


def parameter_summary(values: dict[str, str], parameters: list[dict[str, Any]]) -> str:
    if not parameters:
        return "(none)"
    secret_names = {str(p.get("name", "")) for p in parameters if p.get("type") == "password"}
    lines = []
    for param in parameters:
        name = str(param.get("name", ""))
        value = "******" if name in secret_names and values.get(name) else values.get(name, "")
        lines.append(f"{name}: {value}")
    return "\n".join(lines)


def run_powershell_script(script_content: str, values: dict[str, str], parameters: list[dict[str, Any]]) -> PowerShellRunResult:
    command = render_script(script_content, values)
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            capture_output=True,
            text=True,
            timeout=300,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        duration = time.perf_counter() - start
        stdout = mask_secret_values(proc.stdout or "", values, parameters)
        stderr = mask_secret_values(proc.stderr or "", values, parameters)
        friendly = ""
        combined = f"{stdout}\n{stderr}".lower()
        if proc.returncode != 0 and re.search(r"access is denied|administrator|elevat|permission", combined):
            friendly = (
                "這個動作可能需要系統管理員權限。\n"
                "請嘗試用系統管理員身分重新啟動 SmartAction。"
            )
        return PowerShellRunResult(
            success=proc.returncode == 0,
            stdout=stdout,
            stderr=stderr,
            exit_code=proc.returncode,
            duration_seconds=duration,
            friendly_error=friendly,
        )
    except FileNotFoundError:
        return PowerShellRunResult(
            success=False,
            stdout="",
            stderr="PowerShell executable was not found.",
            exit_code=None,
            duration_seconds=time.perf_counter() - start,
            friendly_error="PowerShell could not be found on this system.",
        )
    except subprocess.TimeoutExpired as exc:
        stdout = mask_secret_values(exc.stdout or "", values, parameters)
        stderr = mask_secret_values(exc.stderr or "", values, parameters)
        return PowerShellRunResult(
            success=False,
            stdout=stdout,
            stderr=stderr,
            exit_code=None,
            duration_seconds=time.perf_counter() - start,
            friendly_error="The script timed out after 300 seconds.",
        )
    except Exception as exc:
        return PowerShellRunResult(
            success=False,
            stdout="",
            stderr=str(exc),
            exit_code=None,
            duration_seconds=time.perf_counter() - start,
            friendly_error="The script could not be executed. Check the script content and try again.",
        )
