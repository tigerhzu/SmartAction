from __future__ import annotations

import json
import shutil
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from core.paths import DATA_DIR

LIBRARY_PATH = DATA_DIR / "powershell_library.json"

CATEGORIES = [
    "System",
    "Network",
    "User Management",
    "Domain / AD",
    "Repair Tools",
    "Custom",
]

RISK_LEVELS = ["safe", "dangerous"]

DEFAULT_SCRIPTS: list[dict[str, Any]] = [
        {
            "id": "ipconfig_all",
            "name": "IP Configuration",
            "description": "Show full network adapter configuration.",
            "category": "Network",
            "script_content": "ipconfig /all",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "ping_google_dns",
            "name": "Ping Google DNS",
            "description": "Test network connectivity by pinging 8.8.8.8.",
            "category": "Network",
            "script_content": "ping 8.8.8.8",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "whoami",
            "name": "Current User",
            "description": "Show the current Windows user identity.",
            "category": "System",
            "script_content": "whoami",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "hostname",
            "name": "Hostname",
            "description": "Show the computer hostname.",
            "category": "System",
            "script_content": "hostname",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "task_manager",
            "name": "Open Task Manager",
            "description": "Open Windows Task Manager.",
            "category": "System",
            "script_content": "Start-Process taskmgr",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "ping_target",
            "name": "Ping Target",
            "description": "Ping a host supplied at run time.",
            "category": "Network",
            "script_content": "ping {{Target}}",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [
                {"name": "Target", "type": "text", "required": True}
            ],
        },
        {
            "id": "restart_computer",
            "name": "Restart Computer",
            "description": "Force restart this computer.",
            "category": "System",
            "script_content": "Restart-Computer -Force",
            "need_admin": True,
            "risk_level": "dangerous",
            "parameters": [],
        },
        {
            "id": "shutdown_computer",
            "name": "Shutdown Computer",
            "description": "Force shut down this computer.",
            "category": "System",
            "script_content": "Stop-Computer -Force",
            "need_admin": True,
            "risk_level": "dangerous",
            "parameters": [],
        },
        {
            "id": "open_services",
            "name": "Open Services",
            "description": "Open the Windows Services management console.",
            "category": "System",
            "script_content": "Start-Process services.msc",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "open_event_viewer",
            "name": "Open Event Viewer",
            "description": "Open Windows Event Viewer.",
            "category": "System",
            "script_content": "Start-Process eventvwr.msc",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "open_device_manager",
            "name": "Open Device Manager",
            "description": "Open Windows Device Manager.",
            "category": "System",
            "script_content": "Start-Process devmgmt.msc",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "create_local_user",
            "name": "Create Local User",
            "description": "Create a local Windows user with a password.",
            "category": "User Management",
            "script_content": "$Password = ConvertTo-SecureString \"{{Password}}\" -AsPlainText -Force\nNew-LocalUser -Name \"{{Username}}\" -Password $Password -FullName \"{{Username}}\" -Description \"Created by SmartAction\"",
            "need_admin": True,
            "risk_level": "dangerous",
            "parameters": [
                {"name": "Username", "type": "text", "required": True},
                {"name": "Password", "type": "password", "required": True},
            ],
        },
        {
            "id": "add_local_user_to_administrators",
            "name": "Add Local User to Administrators",
            "description": "Add a local user to the local Administrators group.",
            "category": "User Management",
            "script_content": "Add-LocalGroupMember -Group \"Administrators\" -Member \"{{Username}}\"",
            "need_admin": True,
            "risk_level": "dangerous",
            "parameters": [
                {"name": "Username", "type": "text", "required": True}
            ],
        },
        {
            "id": "disable_local_user",
            "name": "Disable Local User",
            "description": "Disable a local Windows user account.",
            "category": "User Management",
            "script_content": "Disable-LocalUser -Name \"{{Username}}\"",
            "need_admin": True,
            "risk_level": "dangerous",
            "parameters": [
                {"name": "Username", "type": "text", "required": True}
            ],
        },
        {
            "id": "list_local_users",
            "name": "List Local Users",
            "description": "List local Windows users with enabled state and last logon.",
            "category": "User Management",
            "script_content": "Get-LocalUser | Select-Object Name, Enabled, LastLogon",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "list_local_administrators",
            "name": "List Local Administrators",
            "description": "List members of the local Administrators group.",
            "category": "User Management",
            "script_content": "Get-LocalGroupMember -Group \"Administrators\"",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "check_domain_status",
            "name": "Check Domain Status",
            "description": "Show whether this computer is joined to a domain.",
            "category": "Domain / AD",
            "script_content": "Get-CimInstance Win32_ComputerSystem | Select-Object Name, Domain, PartOfDomain",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "join_domain",
            "name": "Join Domain",
            "description": "Join this computer to an Active Directory domain.",
            "category": "Domain / AD",
            "script_content": "$SecurePassword = ConvertTo-SecureString \"{{DomainPassword}}\" -AsPlainText -Force\n$Credential = New-Object System.Management.Automation.PSCredential (\"{{DomainUser}}\", $SecurePassword)\nAdd-Computer -DomainName \"{{DomainName}}\" -Credential $Credential",
            "need_admin": True,
            "risk_level": "dangerous",
            "parameters": [
                {"name": "DomainName", "type": "text", "required": True},
                {"name": "DomainUser", "type": "text", "required": True},
                {"name": "DomainPassword", "type": "password", "required": True},
            ],
        },
        {
            "id": "join_domain_and_restart",
            "name": "Join Domain and Restart",
            "description": "Join this computer to a domain and restart after success.",
            "category": "Domain / AD",
            "script_content": "$SecurePassword = ConvertTo-SecureString \"{{DomainPassword}}\" -AsPlainText -Force\n$Credential = New-Object System.Management.Automation.PSCredential (\"{{DomainUser}}\", $SecurePassword)\nAdd-Computer -DomainName \"{{DomainName}}\" -Credential $Credential -Restart",
            "need_admin": True,
            "risk_level": "dangerous",
            "parameters": [
                {"name": "DomainName", "type": "text", "required": True},
                {"name": "DomainUser", "type": "text", "required": True},
                {"name": "DomainPassword", "type": "password", "required": True},
            ],
        },
        {
            "id": "rename_computer",
            "name": "Rename Computer",
            "description": "Rename this computer without restarting automatically.",
            "category": "Domain / AD",
            "script_content": "Rename-Computer -NewName \"{{NewComputerName}}\"",
            "need_admin": True,
            "risk_level": "dangerous",
            "parameters": [
                {"name": "NewComputerName", "type": "text", "required": True}
            ],
        },
        {
            "id": "rename_computer_and_restart",
            "name": "Rename Computer and Restart",
            "description": "Rename this computer and restart after success.",
            "category": "Domain / AD",
            "script_content": "Rename-Computer -NewName \"{{NewComputerName}}\" -Restart",
            "need_admin": True,
            "risk_level": "dangerous",
            "parameters": [
                {"name": "NewComputerName", "type": "text", "required": True}
            ],
        },
        {
            "id": "flush_dns",
            "name": "Flush DNS",
            "description": "Clear the Windows DNS resolver cache.",
            "category": "Network",
            "script_content": "ipconfig /flushdns",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "renew_ip",
            "name": "Renew IP",
            "description": "Release and renew DHCP leases.",
            "category": "Network",
            "script_content": "ipconfig /release\nipconfig /renew",
            "need_admin": True,
            "risk_level": "dangerous",
            "parameters": [],
        },
        {
            "id": "show_dns_servers",
            "name": "Show DNS Servers",
            "description": "Show DNS servers configured on each network interface.",
            "category": "Network",
            "script_content": "Get-DnsClientServerAddress | Select-Object InterfaceAlias, ServerAddresses",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "ping_gateway",
            "name": "Ping Gateway",
            "description": "Find the default gateway and ping it.",
            "category": "Network",
            "script_content": "$gateway = Get-NetRoute -DestinationPrefix \"0.0.0.0/0\" | Sort-Object RouteMetric | Select-Object -First 1 -ExpandProperty NextHop\nping $gateway",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [],
        },
        {
            "id": "test_dns_resolution",
            "name": "Test DNS Resolution",
            "description": "Resolve a domain name using Windows DNS tools.",
            "category": "Network",
            "script_content": "Resolve-DnsName \"{{Domain}}\"",
            "need_admin": False,
            "risk_level": "safe",
            "parameters": [
                {"name": "Domain", "type": "text", "required": True}
            ],
        },
        {
            "id": "system_file_checker",
            "name": "System File Checker",
            "description": "Run sfc /scannow to check and repair system files.",
            "category": "Repair Tools",
            "script_content": "sfc /scannow",
            "need_admin": True,
            "risk_level": "dangerous",
            "parameters": [],
        },
        {
            "id": "dism_restore_health",
            "name": "DISM Restore Health",
            "description": "Run DISM RestoreHealth against the online Windows image.",
            "category": "Repair Tools",
            "script_content": "DISM /Online /Cleanup-Image /RestoreHealth",
            "need_admin": True,
            "risk_level": "dangerous",
            "parameters": [],
        },
        {
            "id": "restart_explorer",
            "name": "Restart Explorer",
            "description": "Restart Windows Explorer.",
            "category": "Repair Tools",
            "script_content": "Stop-Process -Name explorer -Force\nStart-Process explorer.exe",
            "need_admin": False,
            "risk_level": "dangerous",
            "parameters": [],
        },
        {
            "id": "clear_temp_files",
            "name": "Clear Temp Files",
            "description": "Remove files from the current user's temporary folder.",
            "category": "Repair Tools",
            "script_content": "Remove-Item \"$env:TEMP\\*\" -Recurse -Force -ErrorAction SilentlyContinue",
            "need_admin": False,
            "risk_level": "dangerous",
            "parameters": [],
        },
]

DEFAULT_LIBRARY: dict[str, Any] = {
    "version": "1.1",
    "scripts": DEFAULT_SCRIPTS,
}


def _new_id() -> str:
    return f"ps_{uuid.uuid4().hex[:10]}"


def normalise_script(data: dict[str, Any]) -> dict[str, Any]:
    script = {
        "id": data.get("id") or _new_id(),
        "name": str(data.get("name", "Untitled Script")).strip() or "Untitled Script",
        "description": str(data.get("description", "")).strip(),
        "category": data.get("category") if data.get("category") in CATEGORIES else "Custom",
        "script_content": str(data.get("script_content", "")).strip(),
        "need_admin": bool(data.get("need_admin", False)),
        "risk_level": data.get("risk_level") if data.get("risk_level") in RISK_LEVELS else "safe",
        "parameters": data.get("parameters") if isinstance(data.get("parameters"), list) else [],
    }
    clean_params: list[dict[str, Any]] = []
    for param in script["parameters"]:
        if not isinstance(param, dict):
            continue
        name = str(param.get("name", "")).strip()
        if not name:
            continue
        ptype = str(param.get("type", "text")).strip().lower()
        clean_params.append(
            {
                "name": name,
                "type": "password" if ptype == "password" else "text",
                "required": bool(param.get("required", False)),
            }
        )
    script["parameters"] = clean_params
    return script


class PowerShellLibrary:
    def __init__(self, path: Path = LIBRARY_PATH) -> None:
        self.path = path
        self.recovery_message: str | None = None
        self._data = self._load_or_create()

    def _load_or_create(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._write_defaults()
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            self._backup_corrupt_file()
            self.recovery_message = (
                f"PowerShell Library was corrupt and has been reset. Details: {exc}"
            )
            return self._write_defaults()
        scripts = data.get("scripts")
        if not isinstance(scripts, list):
            self._backup_corrupt_file()
            self.recovery_message = "PowerShell Library format was invalid and has been reset."
            return self._write_defaults()
        clean_scripts = [normalise_script(s) for s in scripts if isinstance(s, dict)]
        changed = len(clean_scripts) != len(scripts)
        changed = changed or any(
            not isinstance(raw, dict)
            or raw.get("id") != clean.get("id")
            or raw.get("parameters") != clean.get("parameters")
            for raw, clean in zip(scripts, clean_scripts)
        )
        data["scripts"] = clean_scripts
        if self._merge_missing_defaults(data) or changed:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        return data

    def _backup_corrupt_file(self) -> None:
        if not self.path.exists():
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = self.path.with_suffix(f".corrupt_{timestamp}.bak")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.path, backup)

    def _write_defaults(self) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = deepcopy(DEFAULT_LIBRARY)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return data

    def _merge_missing_defaults(self, data: dict[str, Any]) -> bool:
        scripts = data.setdefault("scripts", [])
        existing_ids = {s.get("id") for s in scripts if isinstance(s, dict)}
        missing = [
            deepcopy(script)
            for script in DEFAULT_SCRIPTS
            if script.get("id") not in existing_ids
        ]
        if not missing:
            return False
        scripts.extend(missing)
        data["version"] = DEFAULT_LIBRARY["version"]
        return True

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def scripts(self, category: str | None = None) -> list[dict[str, Any]]:
        scripts = [normalise_script(s) for s in self._data.get("scripts", [])]
        if category and category != "All":
            scripts = [s for s in scripts if s.get("category") == category]
        return scripts

    def get(self, script_id: str) -> dict[str, Any] | None:
        for script in self.scripts():
            if script.get("id") == script_id:
                return script
        return None

    def add(self, script: dict[str, Any]) -> dict[str, Any]:
        clean = normalise_script({**script, "id": script.get("id") or _new_id()})
        self._data.setdefault("scripts", []).append(clean)
        self.save()
        return clean

    def update(self, script_id: str, script: dict[str, Any]) -> dict[str, Any]:
        scripts = self._data.setdefault("scripts", [])
        clean = normalise_script({**script, "id": script_id})
        for idx, existing in enumerate(scripts):
            if existing.get("id") == script_id:
                scripts[idx] = clean
                self.save()
                return clean
        scripts.append(clean)
        self.save()
        return clean

    def delete(self, script_id: str) -> None:
        scripts = self._data.setdefault("scripts", [])
        self._data["scripts"] = [s for s in scripts if s.get("id") != script_id]
        self.save()
