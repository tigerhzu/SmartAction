from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import uuid
import configparser
import sys
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from core.debug_log import debug_log
from core.paths import DATA_DIR


WORKSPACE_PATH = DATA_DIR / "client_workspaces.json"
SMARTACTION_LOCAL_DIR = Path(os.environ.get("LOCALAPPDATA", str(DATA_DIR))) / "SmartAction"
FIREFOX_HELPER_DIR = SMARTACTION_LOCAL_DIR / "firefox_helper"
PENDING_LAUNCH_PATH = FIREFOX_HELPER_DIR / "pending_launch.json"
LAST_RESULT_PATH = FIREFOX_HELPER_DIR / "last_result.json"
FIREFOX_HELPER_XPI_PATH = SMARTACTION_LOCAL_DIR / "firefox-helper.xpi"
HELPER_TIMEOUT_SECONDS = 10
SMARTACTION_FIREFOX_PROFILE = "SmartAction-ClientWorkspace"
FIREFOX_HELPER_EXTENSION_ID = "smartaction-container-helper@naughtytiger06.local"
MULTI_ACCOUNT_CONTAINERS_EXTENSION_ID = "@testpilot-containers"
FIREFOX_PROFILES_INI = (
    Path(os.environ.get("APPDATA", str(Path.home())))
    / "Mozilla"
    / "Firefox"
    / "profiles.ini"
)

DEFAULT_WORKSPACES: dict[str, Any] = {
    "version": "1.0",
    "clients": [],
}


class ClientWorkspaceError(Exception):
    pass


@dataclass
class LaunchResult:
    opened_count: int
    skipped_empty_count: int
    invalid_scheme_urls: list[str]
    used_container_helper: bool = False
    container_name: str = ""


@dataclass(frozen=True)
class FirefoxProfile:
    name: str
    path: Path
    is_default: bool = False
    is_relative: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "isDefault": self.is_default,
            "isRelative": self.is_relative,
        }


def _new_id(name: str = "") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or f"client-{uuid.uuid4().hex[:8]}"


def list_firefox_profiles() -> list[FirefoxProfile]:
    if not FIREFOX_PROFILES_INI.exists():
        debug_log(f"firefox profiles.ini not found: {FIREFOX_PROFILES_INI}")
        return []

    parser = configparser.ConfigParser()
    parser.read(FIREFOX_PROFILES_INI, encoding="utf-8")
    base_dir = FIREFOX_PROFILES_INI.parent
    profiles: list[FirefoxProfile] = []
    for section in parser.sections():
        if not section.lower().startswith("profile"):
            continue
        name = parser.get(section, "Name", fallback="").strip()
        raw_path = parser.get(section, "Path", fallback="").strip()
        if not name or not raw_path:
            continue
        is_relative = parser.getint(section, "IsRelative", fallback=1) == 1
        profile_path = (base_dir / raw_path) if is_relative else Path(raw_path)
        profiles.append(
            FirefoxProfile(
                name=name,
                path=profile_path,
                is_default=parser.getint(section, "Default", fallback=0) == 1,
                is_relative=is_relative,
            )
        )
    debug_log(
        "firefox profiles loaded: "
        f"profiles_ini={FIREFOX_PROFILES_INI} "
        f"count={len(profiles)} "
        f"profiles={[p.to_dict() for p in profiles]}"
    )
    return profiles


def find_firefox_profile(name: str) -> FirefoxProfile | None:
    folded = str(name or "").strip().casefold()
    if not folded:
        return None
    for profile in list_firefox_profiles():
        if profile.name.casefold() == folded:
            return profile
    return None


def ensure_smartaction_firefox_profile() -> FirefoxProfile:
    existing = find_firefox_profile(SMARTACTION_FIREFOX_PROFILE)
    if existing:
        return existing

    firefox = _find_firefox()
    if firefox is None:
        raise ClientWorkspaceError(
            "Firefox was not found. Please install Firefox before creating the SmartAction profile."
        )

    cmd = [str(firefox), "-CreateProfile", SMARTACTION_FIREFOX_PROFILE]
    _debug_firefox_launch(
        "create_profile",
        firefox,
        SMARTACTION_FIREFOX_PROFILE,
        None,
        cmd,
        temporary_profile=False,
        no_remote=False,
    )
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    if proc.returncode != 0:
        raise ClientWorkspaceError(
            f"Firefox could not create profile {SMARTACTION_FIREFOX_PROFILE}.\n"
            f"Exit code: {proc.returncode}\n"
            f"{(proc.stderr or proc.stdout or '').strip()}"
        )
    time.sleep(0.5)

    created = find_firefox_profile(SMARTACTION_FIREFOX_PROFILE)
    if not created:
        raise ClientWorkspaceError(
            f"Could not create Firefox profile: {SMARTACTION_FIREFOX_PROFILE}. "
            "Please close Firefox and try again."
        )
    return created


def normalise_url(data: dict[str, Any]) -> dict[str, str]:
    return {
        "name": str(data.get("name", "")).strip() or "Untitled URL",
        "url": str(data.get("url", "")).strip(),
    }


def normalise_client(data: dict[str, Any]) -> dict[str, Any]:
    name = str(data.get("name", "")).strip() or "Untitled Client"
    urls = data.get("urls", [])
    if not isinstance(urls, list):
        urls = []
    return {
        "id": str(data.get("id", "")).strip() or _new_id(name),
        "name": name,
        "containerName": str(data.get("containerName", "")).strip(),
        "firefoxProfile": str(data.get("firefoxProfile", "")).strip(),
        "urls": [normalise_url(u) for u in urls if isinstance(u, dict)],
    }


def validate_workspace_data(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ClientWorkspaceError("Workspace JSON must be an object.")
    if str(data.get("version", "")) != "1.0":
        raise ClientWorkspaceError("Unsupported Client Workspace version.")
    clients = data.get("clients")
    if not isinstance(clients, list):
        raise ClientWorkspaceError("Workspace JSON must contain a clients array.")
    for idx, client in enumerate(clients, start=1):
        if not isinstance(client, dict):
            raise ClientWorkspaceError(f"Client #{idx} must be an object.")
        if not str(client.get("name", "")).strip():
            raise ClientWorkspaceError(f"Client #{idx} name is required.")
        urls = client.get("urls", [])
        if not isinstance(urls, list):
            raise ClientWorkspaceError(f"Client #{idx} urls must be an array.")
        for url_idx, url_data in enumerate(urls, start=1):
            if not isinstance(url_data, dict):
                raise ClientWorkspaceError(f"Client #{idx} URL #{url_idx} must be an object.")
            if not str(url_data.get("name", "")).strip():
                raise ClientWorkspaceError(f"Client #{idx} URL #{url_idx} name is required.")
            if not str(url_data.get("url", "")).strip():
                raise ClientWorkspaceError(f"Client #{idx} URL #{url_idx} url is required.")
    return {
        "version": "1.0",
        "clients": [normalise_client(c) for c in clients if isinstance(c, dict)],
    }


class ClientWorkspaceStore:
    def __init__(self, path: Path = WORKSPACE_PATH) -> None:
        self.path = path
        self._data = self._load_or_create()

    def _load_or_create(self) -> dict[str, Any]:
        if not self.path.exists():
            self.save_data(deepcopy(DEFAULT_WORKSPACES))
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            clean = validate_workspace_data(data)
        except (OSError, json.JSONDecodeError, ClientWorkspaceError):
            clean = deepcopy(DEFAULT_WORKSPACES)
            self.save_data(clean)
        return clean

    def save_data(self, data: dict[str, Any]) -> None:
        clean = validate_workspace_data(data)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2, ensure_ascii=False)
        self._data = clean

    def clients(self) -> list[dict[str, Any]]:
        return deepcopy(self._data.get("clients", []))

    def get(self, client_id: str) -> dict[str, Any] | None:
        for client in self.clients():
            if client.get("id") == client_id:
                return client
        return None

    def add_client(self, client: dict[str, Any]) -> dict[str, Any]:
        if not str(client.get("name", "")).strip():
            raise ClientWorkspaceError("Client name is required.")
        clean = normalise_client(client)
        self._ensure_unique_name(clean["name"])
        existing = {c.get("id") for c in self._data.setdefault("clients", [])}
        if clean["id"] in existing:
            clean["id"] = _new_id(clean["name"])
        self._data["clients"].append(clean)
        self.save_data(self._data)
        return clean

    def update_client(self, client_id: str, client: dict[str, Any]) -> dict[str, Any]:
        if not str(client.get("name", "")).strip():
            raise ClientWorkspaceError("Client name is required.")
        clean = normalise_client({**client, "id": client_id})
        self._ensure_unique_name(clean["name"], ignore_id=client_id)
        clients = self._data.setdefault("clients", [])
        for idx, existing in enumerate(clients):
            if existing.get("id") == client_id:
                clients[idx] = clean
                self.save_data(self._data)
                return clean
        clients.append(clean)
        self.save_data(self._data)
        return clean

    def delete_client(self, client_id: str) -> None:
        clients = self._data.setdefault("clients", [])
        self._data["clients"] = [c for c in clients if c.get("id") != client_id]
        self.save_data(self._data)

    def export_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def import_json(self, path: Path) -> Path:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        clean = validate_workspace_data(data)
        backup_path = self.backup()
        self.save_data(clean)
        return backup_path

    def backup(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = self.path.parent / f"client_workspaces.backup.{stamp}.json"
        if self.path.exists():
            shutil.copy2(self.path, backup_path)
        else:
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_WORKSPACES, f, indent=2, ensure_ascii=False)
        return backup_path

    def _ensure_unique_name(self, name: str, ignore_id: str | None = None) -> None:
        folded = name.strip().casefold()
        for client in self._data.get("clients", []):
            if ignore_id and client.get("id") == ignore_id:
                continue
            if str(client.get("name", "")).strip().casefold() == folded:
                raise ClientWorkspaceError(f'Client name "{name}" already exists.')


def launch_client_workspace(client: dict[str, Any]) -> LaunchResult:
    raw_urls = [u.get("url", "") for u in client.get("urls", [])]
    skipped_empty = sum(1 for url in raw_urls if not str(url).strip())
    urls = [str(url).strip() for url in raw_urls if str(url).strip()]
    if not urls:
        raise ClientWorkspaceError("This client has no URLs configured.")

    invalid_scheme_urls = [
        url for url in urls
        if not (url.lower().startswith("http://") or url.lower().startswith("https://"))
    ]
    container_name = str(client.get("containerName", "")).strip()
    if container_name:
        return _launch_with_firefox_helper(client, urls, skipped_empty, invalid_scheme_urls, container_name)

    return _launch_v1_firefox_tabs(client, urls, skipped_empty, invalid_scheme_urls)


def format_firefox_helper_error(error: str, container_name: str = "") -> str:
    raw_error = str(error or "").strip()
    lower_error = raw_error.lower()

    if "no permission for cookiestoreid" in lower_error:
        return (
            "Container Helper Extension permission is not sufficient to open the requested Container.\n"
            "Please confirm the extension manifest includes the cookies permission, "
            "then reload or reinstall the signed XPI.\n\n"
            "Original error:\n"
            f"{raw_error}"
        )

    if "container not found" in lower_error:
        return f"Firefox Container not found: {container_name}"

    return raw_error or "Container Helper Extension returned an error."


def _launch_v1_firefox_tabs(
    client: dict[str, Any],
    urls: list[str],
    skipped_empty: int,
    invalid_scheme_urls: list[str],
) -> LaunchResult:

    firefox = _find_firefox()
    if firefox is None:
        raise ClientWorkspaceError(
            "Firefox was not found. Please check that Firefox is installed, "
            "or manually add firefox.exe to PATH. Manual firefox path support is planned."
        )

    args = [str(firefox)]
    profile = _resolve_client_firefox_profile(client)
    if profile:
        args.extend(["-P", profile.name])
    for url in urls:
        args.extend(["-new-tab", url])

    _debug_firefox_launch(
        "v1_tabs",
        firefox,
        profile.name if profile else "",
        profile.path if profile else None,
        args,
        temporary_profile=False,
        no_remote="-no-remote" in args,
    )
    subprocess.Popen(args)
    return LaunchResult(
        opened_count=len(urls),
        skipped_empty_count=skipped_empty,
        invalid_scheme_urls=invalid_scheme_urls,
    )


def _launch_with_firefox_helper(
    client: dict[str, Any],
    urls: list[str],
    skipped_empty: int,
    invalid_scheme_urls: list[str],
    container_name: str,
) -> LaunchResult:
    firefox = _find_firefox()
    if firefox is None:
        raise ClientWorkspaceError(
            "Firefox was not found. Please check that Firefox is installed, "
            "or manually add firefox.exe to PATH. Manual firefox path support is planned."
        )

    profile = _resolve_client_firefox_profile(client, create_smartaction_if_missing=True)
    check_firefox_helper(client, start_firefox=True)

    request_id = uuid.uuid4().hex
    launch_payload = {
        "requestId": request_id,
        "type": "launch_workspace",
        "clientId": client.get("id", ""),
        "clientName": client.get("name", ""),
        "containerName": container_name,
        "urls": [
            {"name": url_data.get("name", ""), "url": url_data.get("url", "")}
            for url_data in client.get("urls", [])
            if str(url_data.get("url", "")).strip()
        ],
    }

    debug_log(
        "client workspace helper launch request: "
        f"profile_name={(profile.name if profile else '')!r} "
        f"profile_path={(str(profile.path) if profile else '')!r} "
        f"temporary_profile=False no_remote=False "
        f"pending_launch={PENDING_LAUNCH_PATH}"
    )
    result = _send_helper_request(launch_payload)
    if result is None:
        raise ClientWorkspaceError(
            _helper_not_connected_message(profile)
        )
    if not result.get("success"):
        error = str(result.get("error") or "Container Helper Extension returned an error.")
        raise ClientWorkspaceError(format_firefox_helper_error(error, container_name))

    return LaunchResult(
        opened_count=int(result.get("openedCount", len(urls)) or 0),
        skipped_empty_count=skipped_empty,
        invalid_scheme_urls=invalid_scheme_urls,
        used_container_helper=True,
        container_name=container_name,
    )


def check_firefox_helper(client: dict[str, Any], start_firefox: bool = True) -> dict[str, Any]:
    firefox = _find_firefox()
    if firefox is None:
        raise ClientWorkspaceError(
            "Firefox was not found. Please check that Firefox is installed."
        )

    profile = _resolve_client_firefox_profile(client, create_smartaction_if_missing=True)
    firefox_running = _is_firefox_running()
    debug_log(
        "client workspace helper check: "
        f"firefox_running={firefox_running} "
        f"profile_name={(profile.name if profile else '')!r} "
        f"profile_path={(str(profile.path) if profile else '')!r} "
        f"extension_id={FIREFOX_HELPER_EXTENSION_ID!r}"
    )
    if start_firefox and not firefox_running:
        _start_firefox_for_helper(firefox, profile)
    elif firefox_running:
        _debug_firefox_launch(
            "helper_check_existing_firefox",
            firefox,
            profile.name if profile else "",
            profile.path if profile else None,
            [],
            temporary_profile=False,
            no_remote=False,
        )

    payload = {
        "requestId": uuid.uuid4().hex,
        "type": "helper_check",
        "expectedAddonId": FIREFOX_HELPER_EXTENSION_ID,
        "profileName": profile.name if profile else "",
    }
    result = _send_helper_request(payload)
    if result is None or not result.get("success"):
        raise ClientWorkspaceError(_helper_not_connected_message(profile))

    addon_id = str(result.get("addonId", ""))
    if addon_id and addon_id != FIREFOX_HELPER_EXTENSION_ID:
        raise ClientWorkspaceError(
            "Container Helper Extension responded with an unexpected add-on id.\n\n"
            f"Expected: {FIREFOX_HELPER_EXTENSION_ID}\n"
            f"Actual: {addon_id}\n\n"
            "Please reinstall the current signed XPI."
        )
    return result


def install_firefox_helper_extension(client: dict[str, Any]) -> Path:
    firefox = _find_firefox()
    if firefox is None:
        raise ClientWorkspaceError("Firefox was not found. Please install Firefox first.")

    profile = _resolve_client_firefox_profile(client, create_smartaction_if_missing=True)
    xpi_path = _find_firefox_helper_xpi()
    if xpi_path is None:
        raise ClientWorkspaceError(
            "Container Helper XPI was not found.\n\n"
            "Please run build_extension.bat first, then sign the XPI for production install."
        )

    args = [str(firefox)]
    if profile:
        args.extend(["-P", profile.name])
    args.append(str(xpi_path))
    _debug_firefox_launch(
        "install_helper_extension",
        firefox,
        profile.name if profile else "",
        profile.path if profile else None,
        args,
        temporary_profile=False,
        no_remote="-no-remote" in args,
    )
    subprocess.Popen(args)
    return xpi_path


def open_firefox_addons(client: dict[str, Any]) -> None:
    firefox = _find_firefox()
    if firefox is None:
        raise ClientWorkspaceError("Firefox was not found. Please install Firefox first.")
    profile = _resolve_client_firefox_profile(client, create_smartaction_if_missing=True)
    args = [str(firefox)]
    if profile:
        args.extend(["-P", profile.name])
    args.append("about:addons")
    _debug_firefox_launch(
        "open_addons",
        firefox,
        profile.name if profile else "",
        profile.path if profile else None,
        args,
        temporary_profile=False,
        no_remote="-no-remote" in args,
    )
    subprocess.Popen(args)


def repair_native_host_setup() -> Path:
    if os.name != "nt":
        raise ClientWorkspaceError("Native Messaging Host repair is available on Windows only.")

    import winreg

    install_dir = SMARTACTION_LOCAL_DIR / "firefox_helper_host"
    install_dir.mkdir(parents=True, exist_ok=True)

    host_source = _find_native_host_source()
    if host_source is None:
        raise ClientWorkspaceError(
            "Could not find native host files.\n\n"
            "Please run setup.bat from the SmartAction release folder."
        )

    host_target: Path
    if host_source.suffix.casefold() == ".exe":
        host_target = install_dir / "smartaction_firefox_host.exe"
        shutil.copy2(host_source, host_target)
    else:
        host_py = install_dir / "smartaction_firefox_host.py"
        shutil.copy2(host_source, host_py)
        host_target = install_dir / "smartaction_firefox_host.cmd"
        host_target.write_text(
            f'@echo off\r\n"{sys.executable}" "{host_py}"\r\n',
            encoding="utf-8",
        )

    xpi = _find_firefox_helper_xpi()
    if xpi:
        FIREFOX_HELPER_XPI_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(xpi, FIREFOX_HELPER_XPI_PATH)

    manifest = install_dir / "host_manifest.json"
    manifest_data = {
        "name": "smartaction_firefox_helper",
        "description": "SmartAction Container Helper Native Messaging Host",
        "path": str(host_target),
        "type": "stdio",
        "allowed_extensions": [FIREFOX_HELPER_EXTENSION_ID],
    }
    manifest.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    reg_path = r"Software\Mozilla\NativeMessagingHosts\smartaction_firefox_helper"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest))

    debug_log(
        "native host repaired: "
        f"host_source={host_source} host_target={host_target} "
        f"manifest={manifest} xpi_copied={bool(xpi)}"
    )
    return manifest


def get_setup_status(client: dict[str, Any], helper_connected: bool | None = None) -> dict[str, Any]:
    firefox = _find_firefox()
    profile: FirefoxProfile | None = None
    profile_error = ""
    try:
        profile = _resolve_client_firefox_profile(client, create_smartaction_if_missing=False)
    except ClientWorkspaceError as exc:
        profile_error = str(exc)

    return {
        "firefox_installed": firefox is not None,
        "firefox_path": str(firefox or ""),
        "profile_name": profile.name if profile else str(client.get("firefoxProfile", "")),
        "profile_path": str(profile.path) if profile else "",
        "profile_error": profile_error,
        "multi_account_containers_installed": _profile_has_extension(
            profile, MULTI_ACCOUNT_CONTAINERS_EXTENSION_ID
        ),
        "container_helper_installed": _profile_has_extension(
            profile, FIREFOX_HELPER_EXTENSION_ID
        ),
        "native_host_registered": is_firefox_helper_host_installed(),
        "helper_connected": helper_connected,
        "xpi_path": str(_find_firefox_helper_xpi() or ""),
    }


def _find_firefox_helper_xpi() -> Path | None:
    candidates = [
        FIREFOX_HELPER_XPI_PATH,
        Path.cwd() / "dist" / "firefox-helper.xpi",
        Path(__file__).resolve().parents[1] / "dist" / "firefox-helper.xpi",
    ]
    for base in _runtime_base_dirs():
        candidates.extend(
            [
                base / "firefox-helper.xpi",
                base / "dist" / "firefox-helper.xpi",
            ]
        )
    for path in candidates:
        if path.exists():
            return path
    return None


def _find_native_host_source() -> Path | None:
    names = [
        Path("native_host") / "smartaction_firefox_host.exe",
        Path("native") / "firefox_helper_host" / "smartaction_firefox_host.exe",
        Path("native") / "firefox_helper_host" / "smartaction_firefox_host.py",
    ]
    bases = _runtime_base_dirs()
    for base in bases:
        for rel in names:
            candidate = base / rel
            if candidate.exists():
                return candidate
    fallback = Path(__file__).resolve().parents[1] / "native" / "firefox_helper_host" / "smartaction_firefox_host.py"
    return fallback if fallback.exists() else None


def _runtime_base_dirs() -> list[Path]:
    dirs: list[Path] = []
    if getattr(sys, "frozen", False):
        dirs.append(Path(sys.executable).resolve().parent)
    dirs.extend(
        [
            Path.cwd(),
            Path(__file__).resolve().parents[1],
            Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) > 2 else Path.cwd(),
        ]
    )
    unique: list[Path] = []
    for path in dirs:
        if path not in unique:
            unique.append(path)
    return unique


def _profile_has_extension(profile: FirefoxProfile | None, extension_id: str) -> bool:
    if profile is None:
        return False
    extensions_json = profile.path / "extensions.json"
    if not extensions_json.exists():
        return False
    try:
        data = json.loads(extensions_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    for addon in data.get("addons", []):
        if str(addon.get("id", "")).casefold() == extension_id.casefold():
            return not bool(addon.get("userDisabled", False)) and not bool(addon.get("appDisabled", False))
    return False


def _send_helper_request(payload: dict[str, Any]) -> dict[str, Any] | None:
    FIREFOX_HELPER_DIR.mkdir(parents=True, exist_ok=True)
    if LAST_RESULT_PATH.exists():
        try:
            LAST_RESULT_PATH.unlink()
        except OSError:
            pass
    with open(PENDING_LAUNCH_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    debug_log(
        "firefox helper request written: "
        f"type={payload.get('type')!r} request_id={payload.get('requestId')!r} "
        f"path={PENDING_LAUNCH_PATH}"
    )
    return _wait_for_helper_result(str(payload.get("requestId", "")))


def _helper_not_connected_message(profile: FirefoxProfile | None) -> str:
    profile_name = profile.name if profile else ""
    profile_path = str(profile.path) if profile else ""
    return (
        "請先安裝 Helper Extension。\n\n"
        "SmartAction could not confirm that the Container Helper Extension is connected.\n\n"
        "Please check:\n"
        f"- Install the signed XPI for add-on id: {FIREFOX_HELPER_EXTENSION_ID}\n"
        f"- Firefox profile: {profile_name}\n"
        f"- Profile path: {profile_path}\n"
        "- Native Messaging Host is registered under HKCU for smartaction_firefox_helper.\n"
        f"- Helper files are under: {FIREFOX_HELPER_DIR}"
    )


def _start_firefox_for_helper(firefox: Path, profile: FirefoxProfile | None) -> None:
    args = [str(firefox)]
    if profile:
        args.extend(["-P", profile.name])
    args.extend(["--new-window", "about:blank"])
    _debug_firefox_launch(
        "helper_start",
        firefox,
        profile.name if profile else "",
        profile.path if profile else None,
        args,
        temporary_profile=False,
        no_remote="-no-remote" in args,
    )
    subprocess.Popen(args)


def _wait_for_helper_result(request_id: str) -> dict[str, Any] | None:
    deadline = time.time() + HELPER_TIMEOUT_SECONDS
    while time.time() < deadline:
        if LAST_RESULT_PATH.exists():
            try:
                with open(LAST_RESULT_PATH, encoding="utf-8") as f:
                    result = json.load(f)
                if result.get("requestId") in (None, request_id):
                    try:
                        PENDING_LAUNCH_PATH.unlink()
                    except OSError:
                        pass
                    return result
            except (OSError, json.JSONDecodeError):
                pass
        time.sleep(0.25)
    return None


def _resolve_client_firefox_profile(
    client: dict[str, Any],
    create_smartaction_if_missing: bool = False,
) -> FirefoxProfile | None:
    requested = str(client.get("firefoxProfile", "")).strip()
    if requested:
        profile = find_firefox_profile(requested)
        if profile:
            return profile
        debug_log(
            "client workspace firefox profile not found: "
            f"requested={requested!r} profiles_ini={FIREFOX_PROFILES_INI}"
        )
        raise ClientWorkspaceError(
            f'Firefox profile "{requested}" was not found in profiles.ini.\n\n'
            f"Please select a fixed profile from Client Workspace settings."
        )

    if create_smartaction_if_missing:
        return ensure_smartaction_firefox_profile()

    profiles = list_firefox_profiles()
    default_profile = next((profile for profile in profiles if profile.is_default), None)
    return default_profile or (profiles[0] if profiles else None)


def _is_firefox_running() -> bool:
    if os.name != "nt":
        return False
    try:
        proc = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq firefox.exe", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        output = (proc.stdout or "").casefold()
        running = "firefox.exe" in output
        debug_log(f"firefox process check: running={running} output={output.strip()!r}")
        return running
    except Exception as exc:
        debug_log(f"firefox process check failed: {exc}")
        return False


def _debug_firefox_launch(
    reason: str,
    firefox: Path | None,
    profile_name: str,
    profile_path: Path | None,
    command_line: list[str],
    temporary_profile: bool,
    no_remote: bool,
) -> None:
    debug_log(
        "firefox launch debug: "
        f"reason={reason} "
        f"firefox_path={str(firefox) if firefox else ''!r} "
        f"profile_name={profile_name!r} "
        f"profile_path={str(profile_path) if profile_path else ''!r} "
        f"command_line={command_line!r} "
        f"temporary_profile={temporary_profile} "
        f"no_remote={no_remote}"
    )


def _find_firefox() -> Path | None:
    found = shutil.which("firefox")
    if found:
        return Path(found)
    candidates = [
        Path("C:/Program Files/Mozilla Firefox/firefox.exe"),
        Path("C:/Program Files (x86)/Mozilla Firefox/firefox.exe"),
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def is_firefox_helper_host_installed() -> bool:
    if os.name != "nt":
        return False
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Mozilla\NativeMessagingHosts\smartaction_firefox_helper",
        ) as key:
            manifest_path, _value_type = winreg.QueryValueEx(key, "")
        manifest = Path(str(manifest_path))
        if not manifest.exists():
            return False
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        host_path = Path(str(data.get("path", "")))
        return host_path.exists()
    except Exception:
        return False
