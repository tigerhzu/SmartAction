from __future__ import annotations

import json
import re
import shutil
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from core.actions_config import ActionsConfig
from core.client_workspace import ClientWorkspaceStore, WORKSPACE_PATH, validate_workspace_data
from core.config_manager import ConfigManager
from core.constellation import (
    DEFAULT_CONSTELLATION,
    DEFAULT_CONSTELLATION_COLOR,
    normalise_constellation_color,
)
from core.paths import BACKUPS_DIR
from core.powershell_library import LIBRARY_PATH, PowerShellLibrary, normalise_script
from core.theme import DEFAULT_THEME


PROFILE_VERSION = 1
APP_NAME = "SmartAction"

_SENSITIVE_KEY_RE = re.compile(r"(password|passwd|token|api[_-]?key|secret|credential)", re.IGNORECASE)
_LOCAL_PATH_RE = re.compile(r"(?i)([a-z]:\\|\\\\|\.exe\b|\.bat\b|\.cmd\b|\.ps1\b)")


@dataclass
class ImportResult:
    backup_path: Path
    local_path_warning: bool = False


class ProfileError(Exception):
    pass


def default_export_filename() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"smartaction-profile-{stamp}.json"


def build_profile(
    actions_config: ActionsConfig,
    actions_override: list[dict] | None = None,
    hotkey_override: str | None = None,
    theme_override: str | None = None,
    constellation_override: str | None = None,
    constellation_color_override: str | None = None,
    ui_theme_override: str | None = None,
    ui_background_override: str | None = None,
    ui_background_opacity_override: int | None = None,
    ui_background_zoom_override: int | None = None,
    ui_background_focus_x_override: float | None = None,
    ui_background_focus_y_override: float | None = None,
) -> dict[str, Any]:
    settings = _read_json(ConfigManager().path, {})
    library = PowerShellLibrary()
    workspaces = ClientWorkspaceStore()
    actions = deepcopy(actions_override if actions_override is not None else actions_config.get_raw_actions())
    hotkey = hotkey_override if hotkey_override is not None else actions_config.get_hotkey()
    theme = theme_override if theme_override is not None else actions_config.get_theme()
    constellation = (
        constellation_override
        if constellation_override is not None
        else actions_config.get_constellation()
    )
    constellation_color = normalise_constellation_color(
        constellation_color_override
        if constellation_color_override is not None
        else actions_config.get_constellation_color()
    )
    ui_theme = (
        ui_theme_override
        if ui_theme_override is not None
        else actions_config.get_ui_theme()
    )
    ui_background = (
        ui_background_override
        if ui_background_override is not None
        else actions_config.get_ui_background()
    )
    ui_background_opacity = (
        ui_background_opacity_override
        if ui_background_opacity_override is not None
        else actions_config.get_ui_background_opacity()
    )
    ui_background_zoom = (
        ui_background_zoom_override
        if ui_background_zoom_override is not None
        else actions_config.get_ui_background_zoom()
    )
    current_focus_x, current_focus_y = actions_config.get_ui_background_focus()
    ui_background_focus_x = (
        ui_background_focus_x_override
        if ui_background_focus_x_override is not None
        else current_focus_x
    )
    ui_background_focus_y = (
        ui_background_focus_y_override
        if ui_background_focus_y_override is not None
        else current_focus_y
    )

    return {
        "profile_version": PROFILE_VERSION,
        "app": APP_NAME,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "settings": _sanitize(settings),
        "actions_config": {
            "version": "1.3",
            "hotkey": hotkey,
            "theme": theme,
            "constellation": constellation,
            "constellation_color": constellation_color,
            "ui_theme": ui_theme,
            "ui_background": ui_background,
            "ui_background_opacity": ui_background_opacity,
            "ui_background_zoom": ui_background_zoom,
            "ui_background_focus_x": ui_background_focus_x,
            "ui_background_focus_y": ui_background_focus_y,
        },
        "actions": _sanitize(actions),
        "powershell_library": _sanitize(library.scripts()),
        "client_workspaces": _sanitize(workspaces.clients()),
        "ui": _sanitize(
            {
                "theme": theme,
                "constellation": constellation,
                "constellation_color": constellation_color,
                "global_theme": ui_theme,
                "background": ui_background,
                "background_opacity": ui_background_opacity,
                "background_zoom": ui_background_zoom,
                "background_focus_x": ui_background_focus_x,
                "background_focus_y": ui_background_focus_y,
                "startup_video_enabled": settings.get("startup_video_enabled", False),
                "startup_video_duration": settings.get("startup_video_duration", 5),
                "startup_video_path": settings.get("startup_video_path", "assets/startup/startup.png"),
            }
        ),
    }


def export_profile(
    path: Path,
    actions_config: ActionsConfig,
    actions_override: list[dict] | None = None,
    hotkey_override: str | None = None,
    theme_override: str | None = None,
    constellation_override: str | None = None,
    constellation_color_override: str | None = None,
    ui_theme_override: str | None = None,
    ui_background_override: str | None = None,
    ui_background_opacity_override: int | None = None,
    ui_background_zoom_override: int | None = None,
    ui_background_focus_x_override: float | None = None,
    ui_background_focus_y_override: float | None = None,
) -> None:
    profile = build_profile(
        actions_config,
        actions_override,
        hotkey_override,
        theme_override,
        constellation_override,
        constellation_color_override,
        ui_theme_override,
        ui_background_override,
        ui_background_opacity_override,
        ui_background_zoom_override,
        ui_background_focus_x_override,
        ui_background_focus_y_override,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, profile)


def import_profile(path: Path, actions_config: ActionsConfig, mode: str = "replace") -> ImportResult:
    if mode != "replace":
        raise ProfileError("Merge import is not available yet. Please use Replace mode.")

    profile = _load_and_validate_profile(path)
    backup_path = backup_current_profile(actions_config)
    local_path_warning = _contains_local_paths(profile.get("actions", []))

    try:
        _import_replace(profile, actions_config)
    except Exception:
        _restore_backup(backup_path, actions_config)
        raise

    return ImportResult(backup_path=backup_path, local_path_warning=local_path_warning)


def backup_current_profile(actions_config: ActionsConfig) -> Path:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUPS_DIR / f"backup_profile_{stamp}.json"
    profile = build_profile(actions_config)
    profile["backup_created_at"] = datetime.now().isoformat(timespec="seconds")
    _write_json(backup_path, profile)
    return backup_path


def _import_replace(profile: dict[str, Any], actions_config: ActionsConfig) -> None:
    actions = deepcopy(profile.get("actions", []))
    if not isinstance(actions, list):
        raise ProfileError("Profile actions must be a list.")

    config_meta = profile.get("actions_config", {})
    if not isinstance(config_meta, dict):
        config_meta = {}

    actions_data = {
        "version": str(config_meta.get("version", "1.0")),
        "hotkey": str(config_meta.get("hotkey", "ctrl+space")),
        "theme": str(config_meta.get("theme") or profile.get("ui", {}).get("theme", DEFAULT_THEME)),
        "constellation": str(
            config_meta.get("constellation")
            or profile.get("ui", {}).get("constellation", DEFAULT_CONSTELLATION)
        ),
        "constellation_color": normalise_constellation_color(
            config_meta.get("constellation_color")
            or profile.get("ui", {}).get(
                "constellation_color",
                DEFAULT_CONSTELLATION_COLOR,
            )
        ),
        "ui_theme": str(
            config_meta.get("ui_theme")
            or profile.get("ui", {}).get("global_theme", "classic")
        ),
        "ui_background": str(
            config_meta.get("ui_background")
            or profile.get("ui", {}).get("background", "")
        ),
        "ui_background_opacity": int(
            config_meta.get("ui_background_opacity")
            or profile.get("ui", {}).get("background_opacity", 82)
        ),
        "ui_background_zoom": max(
            100,
            min(
                400,
                int(
                    config_meta.get("ui_background_zoom")
                    or profile.get("ui", {}).get("background_zoom", 100)
                ),
            ),
        ),
        "ui_background_focus_x": max(
            0.0,
            min(
                1.0,
                float(
                    config_meta.get("ui_background_focus_x")
                    if config_meta.get("ui_background_focus_x") is not None
                    else profile.get("ui", {}).get("background_focus_x", 0.5)
                ),
            ),
        ),
        "ui_background_focus_y": max(
            0.0,
            min(
                1.0,
                float(
                    config_meta.get("ui_background_focus_y")
                    if config_meta.get("ui_background_focus_y") is not None
                    else profile.get("ui", {}).get("background_focus_y", 0.5)
                ),
            ),
        ),
        "actions": actions,
    }

    settings = deepcopy(profile.get("settings", {}))
    if settings and not isinstance(settings, dict):
        raise ProfileError("Profile settings must be an object.")

    scripts = deepcopy(profile.get("powershell_library", []))
    if not isinstance(scripts, list):
        raise ProfileError("Profile PowerShell Library must be a list.")

    client_workspaces = deepcopy(profile.get("client_workspaces", []))
    if not isinstance(client_workspaces, list):
        raise ProfileError("Profile Client Workspaces must be a list.")

    clean_scripts = [normalise_script(s) for s in scripts if isinstance(s, dict)]

    _write_json(actions_config.path, actions_data)
    if settings:
        _write_json(ConfigManager().path, settings)
    _write_json(LIBRARY_PATH, {"version": "1.1", "scripts": clean_scripts})
    _write_json(WORKSPACE_PATH, validate_workspace_data({"version": "1.0", "clients": client_workspaces}))

    actions_config.reload()


def _restore_backup(backup_path: Path, actions_config: ActionsConfig) -> None:
    try:
        profile = _read_json(backup_path, {})
        if not profile:
            return
        _import_replace(profile, actions_config)
    except Exception:
        return


def _load_and_validate_profile(path: Path) -> dict[str, Any]:
    try:
        profile = _read_json(path, None)
    except json.JSONDecodeError as exc:
        raise ProfileError(f"JSON format is invalid: {exc}") from exc
    except OSError as exc:
        raise ProfileError(f"Unable to read profile: {exc}") from exc

    if not isinstance(profile, dict):
        raise ProfileError("This file is not a SmartAction profile.")
    if profile.get("app") != APP_NAME:
        raise ProfileError("This file is not a SmartAction profile.")
    if profile.get("profile_version") != PROFILE_VERSION:
        raise ProfileError(f"Unsupported profile_version: {profile.get('profile_version')!r}")
    if "actions" not in profile or "powershell_library" not in profile:
        raise ProfileError("Profile is missing required fields.")
    return profile


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if _SENSITIVE_KEY_RE.search(str(key)):
                result[key] = "******"
            else:
                result[key] = _sanitize(child)
        return result
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def _contains_local_paths(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_local_paths(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_local_paths(v) for v in value)
    if isinstance(value, str):
        return bool(_LOCAL_PATH_RE.search(value))
    return False


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return deepcopy(fallback)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    shutil.move(str(tmp), str(path))
