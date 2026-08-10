"""
ActionsConfig — primary configuration for the ring's action tree.

File location : <project_root>/config/actions.json
Auto-created  : yes, from _DEFAULTS on first run.

Schema summary
--------------
{
  "version": "1.0",
  "hotkey":  "ctrl+space",          # global trigger combo
  "actions": [                       # root-level ring slots
    {
      "id":          "ai",
      "label":       "AI",           # full label shown in floating card
      "short_label": "AI",           # 1-3 chars shown inside the slot circle
      "icon":        "",             # emoji overrides short_label if set
      "type":        "folder",       # includes "settings" for opening Settings from the ring
      "target":      "",             # URL, command string, or form id
      "script_id":   "",             # legacy only; powershell_library now opens the library window
      "enabled":     true,           # false → hidden from ring
      "sub_actions": [ ... ]         # nested items (makes type="folder" implicit)
    }
  ]
}

Relationship to legacy core/config_manager.py
----------------------------------------------
ConfigManager (resources/config.json) still backs the Settings GUI.
ActionsConfig (config/actions.json) is the new authoritative source for
the ring and will be the only config once the Settings GUI is updated.
"""
from __future__ import annotations

import copy
import json
import shutil
import uuid
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from core.action_contracts import ActionValidationError, normalise_actions
from core.action_service import ActionConfigService, ActionMutationResult
from core.atomic_json import AtomicJsonStore, JsonStoreError
from core.debug_log import debug_log
from core.menu_model import MenuItem
from core.paths import CONFIG_DIR as _CONFIG_DIR

# ── Paths ─────────────────────────────────────────────────────────────────────

_CONFIG_PATH = _CONFIG_DIR / "actions.json"
_CONFIG_VERSION = "1.3"

UI_THEME_CLASSIC = "classic"
UI_THEME_CUTE = "cute"
UI_THEME_WOVEN = "woven_light"
UI_THEME_IDS = {UI_THEME_CLASSIC, UI_THEME_CUTE, UI_THEME_WOVEN}
DEFAULT_UI_BACKGROUND_OPACITY = 82
DEFAULT_UI_BACKGROUND_ZOOM = 100
DEFAULT_UI_BACKGROUND_FOCUS = 0.5

_SETTINGS_ACTION: dict = {
    "id":          "settings",
    "label":       "Settings",
    "short_label": "SET",
    "icon":        "",
    "type":        "settings",
    "target":      "",
    "enabled":     True,
    "sub_actions": [],
}

# ── Default config (written on first run) ────────────────────────────────────

_DEFAULTS: dict = {
    "version": _CONFIG_VERSION,
    "hotkey": "ctrl+space",
    "theme": "tiger",
    "constellation": "scorpio",
    "constellation_color": "#F2760B",
    "ui_theme": UI_THEME_CLASSIC,
    "ui_background": "",
    "ui_background_opacity": DEFAULT_UI_BACKGROUND_OPACITY,
    "ui_background_zoom": DEFAULT_UI_BACKGROUND_ZOOM,
    "ui_background_focus_x": DEFAULT_UI_BACKGROUND_FOCUS,
    "ui_background_focus_y": DEFAULT_UI_BACKGROUND_FOCUS,
    "actions": [
        {
            "id":          "ai",
            "label":       "AI",
            "short_label": "AI",
            "icon":        "",
            "type":        "folder",
            "target":      "",
            "enabled":     True,
            "sub_actions": [
                {
                    "id":          "chatgpt",
                    "label":       "ChatGPT",
                    "short_label": "",
                    "icon":        "",
                    "type":        "url",
                    "target":      "https://chatgpt.com",
                    "enabled":     True,
                },
                {
                    "id":          "claude",
                    "label":       "Claude",
                    "short_label": "",
                    "icon":        "",
                    "type":        "url",
                    "target":      "https://claude.ai",
                    "enabled":     True,
                },
            ],
        },
        {
            "id":          "powershell",
            "label":       "PowerShell",
            "short_label": "PS",
            "icon":        "",
            "type":        "folder",
            "target":      "",
            "enabled":     True,
            "sub_actions": [
                {
                    "id":          "join_domain",
                    "label":       "Join Domain",
                    "short_label": "",
                    "icon":        "",
                    "type":        "ps_form",
                    "target":      "join_domain",
                    "enabled":     True,
                },
                {
                    "id":          "add_local_user",
                    "label":       "Add Local User",
                    "short_label": "",
                    "icon":        "",
                    "type":        "ps_form",
                    "target":      "add_local_user",
                    "enabled":     True,
                },
            ],
        },
        _SETTINGS_ACTION,
    ],
}


# ── Config class ──────────────────────────────────────────────────────────────

class ActionsConfig:
    """Read / write ``config/actions.json``.

    Automatically creates the file with default contents on first run.
    All mutations are persisted immediately (same approach as ConfigManager).
    """

    def __init__(self, path: Path = _CONFIG_PATH) -> None:
        self._path = Path(path)
        self._store = AtomicJsonStore(self._path)
        self._data = self._load_or_create()
        self._action_service = ActionConfigService(self)
        raw_actions = self._data.get("actions", [])
        debug_log(
            f"actions config path: {self._path.resolve()} "
            f"exists={self._path.exists()} root_actions={len(raw_actions)} "
            f"enabled_actions={len([a for a in raw_actions if a.get('enabled', True)])} "
            f"theme={self.get_theme()!r}"
        )

    @property
    def path(self) -> Path:
        return self._path

    # ── I/O ───────────────────────────────────────────────────────────────────

    def _load_or_create(self) -> dict:
        if self._path.exists():
            try:
                data = self._store.read()
            except JsonStoreError as exc:
                if not isinstance(exc.__cause__, json.JSONDecodeError):
                    raise
                print(f"[ActionsConfig] Corrupt JSON ({exc.__cause__}); regenerating defaults.")
            else:
                if not isinstance(data, dict):
                    print("[ActionsConfig] Invalid root JSON; regenerating defaults.")
                else:
                    data, changed = self._migrate(data)
                    try:
                        clean_actions = normalise_actions(data.get("actions", []))
                    except ActionValidationError as exc:
                        # Preserve legacy hand-edited configs at startup. New
                        # mutations still pass through strict service validation.
                        debug_log(
                            "actions config schema warning: "
                            f"code={exc.code} path={exc.path} message={exc}"
                        )
                    else:
                        if clean_actions != data.get("actions", []):
                            data["actions"] = clean_actions
                            changed = True
                    if changed:
                        self._write_data(data)
                    debug_log(f"loaded existing actions config: {self._path.resolve()}")
                    return data

        # First run or corrupt file → write defaults
        data = copy.deepcopy(_DEFAULTS)
        data["actions"] = normalise_actions(data["actions"])
        self._write_data(data)
        print(f"[ActionsConfig] Created default config: {self._path}")
        debug_log("default actions config was auto-created")
        return data

    def _migrate(self, data: dict) -> tuple[dict, bool]:
        """Upgrade known legacy configs without replacing user actions."""
        version = str(data.get("version", ""))
        if version not in {"", "1.0", "1.1", "1.2"}:
            return data, False

        data.setdefault("constellation", _DEFAULTS["constellation"])
        data.setdefault("constellation_color", _DEFAULTS["constellation_color"])
        data.setdefault("ui_theme", _DEFAULTS["ui_theme"])
        data.setdefault("ui_background", _DEFAULTS["ui_background"])
        data.setdefault(
            "ui_background_opacity",
            _DEFAULTS["ui_background_opacity"],
        )
        data.setdefault("ui_background_zoom", _DEFAULTS["ui_background_zoom"])
        data.setdefault(
            "ui_background_focus_x",
            _DEFAULTS["ui_background_focus_x"],
        )
        data.setdefault(
            "ui_background_focus_y",
            _DEFAULTS["ui_background_focus_y"],
        )
        actions = data.setdefault("actions", [])
        if isinstance(actions, list) and not any(
            action.get("type") == "settings"
            for action in actions
            if isinstance(action, dict)
        ):
            # Keep Settings inside the eight visible root slots on legacy
            # configs, matching its position in the current defaults.
            actions.insert(min(2, len(actions)), copy.deepcopy(_SETTINGS_ACTION))
        data["version"] = _CONFIG_VERSION
        debug_log(
            f"migrated actions config from version {version or 'unversioned'} "
            f"to {_CONFIG_VERSION}"
        )
        return data, True

    def _write_data(self, data: dict) -> None:
        self._store.write(data)

    def _save(self) -> None:
        self._write_data(self._data)

    def _update(self, mutate: Callable[[dict[str, Any]], None]) -> None:
        """Commit a config mutation without exposing half-written state."""
        next_data = copy.deepcopy(self._data)
        mutate(next_data)
        self._write_data(next_data)
        self._data = next_data

    def snapshot(self) -> dict[str, Any]:
        """Return a detached snapshot of the complete actions document."""
        return copy.deepcopy(self._data)

    def update_settings(self, changes: Mapping[str, Any]) -> None:
        """Atomically update supported non-action settings in one commit."""
        from core.constellation import normalise_constellation_color

        allowed = {
            "hotkey",
            "theme",
            "constellation",
            "constellation_color",
            "ui_theme",
            "ui_background",
            "ui_background_opacity",
            "ui_background_zoom",
            "ui_background_focus_x",
            "ui_background_focus_y",
        }
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"Unsupported settings: {', '.join(sorted(unknown))}")

        clean = dict(changes)
        if "hotkey" in clean:
            clean["hotkey"] = str(clean["hotkey"]).strip()
        if "theme" in clean:
            clean["theme"] = str(clean["theme"]).strip()
        if "constellation" in clean:
            clean["constellation"] = str(clean["constellation"]).strip()
        if "constellation_color" in clean:
            clean["constellation_color"] = normalise_constellation_color(
                clean["constellation_color"]
            )
        if "ui_theme" in clean:
            value = str(clean["ui_theme"]).strip().lower()
            clean["ui_theme"] = value if value in UI_THEME_IDS else UI_THEME_CLASSIC
        if "ui_background" in clean:
            clean["ui_background"] = str(clean["ui_background"] or "").strip()
        if "ui_background_opacity" in clean:
            clean["ui_background_opacity"] = max(
                15, min(100, int(clean["ui_background_opacity"]))
            )
        if "ui_background_zoom" in clean:
            clean["ui_background_zoom"] = max(
                100, min(400, int(clean["ui_background_zoom"]))
            )
        for key in ("ui_background_focus_x", "ui_background_focus_y"):
            if key in clean:
                clean[key] = max(0.0, min(1.0, float(clean[key])))

        self._update(lambda data: data.update(clean))

    # ── Hotkey ────────────────────────────────────────────────────────────────

    def get_hotkey(self) -> str:
        return self._data.get("hotkey", "ctrl+space")

    def set_hotkey(self, combo: str) -> None:
        self._update(lambda data: data.__setitem__("hotkey", combo))

    # ── Theme ─────────────────────────────────────────────────────────────────

    def get_theme(self) -> str:
        return self._data.get("theme", "tiger")

    def set_theme(self, theme_id: str) -> None:
        self._update(lambda data: data.__setitem__("theme", theme_id))

    def get_constellation(self) -> str:
        from core.constellation import CONSTELLATIONS, DEFAULT_CONSTELLATION

        value = str(self._data.get("constellation", DEFAULT_CONSTELLATION))
        return value if value in CONSTELLATIONS else DEFAULT_CONSTELLATION

    def set_constellation(self, constellation_id: str) -> None:
        self._update(lambda data: data.__setitem__("constellation", constellation_id))

    def get_constellation_color(self) -> str:
        from core.constellation import normalise_constellation_color

        return normalise_constellation_color(self._data.get("constellation_color"))

    def set_constellation_color(self, color: str) -> None:
        from core.constellation import normalise_constellation_color

        value = normalise_constellation_color(color)
        self._update(lambda data: data.__setitem__("constellation_color", value))

    def get_ui_theme(self) -> str:
        value = str(self._data.get("ui_theme", UI_THEME_CLASSIC)).strip().lower()
        return value if value in UI_THEME_IDS else UI_THEME_CLASSIC

    def set_ui_theme(self, theme_id: str) -> None:
        value = str(theme_id).strip().lower()
        clean = value if value in UI_THEME_IDS else UI_THEME_CLASSIC
        self._update(lambda data: data.__setitem__("ui_theme", clean))

    def get_ui_background(self) -> str:
        return str(self._data.get("ui_background", "") or "").strip()

    def set_ui_background(self, path_value: str) -> None:
        value = str(path_value or "").strip()
        self._update(lambda data: data.__setitem__("ui_background", value))

    def resolve_ui_background(self, path_value: str | None = None) -> Path | None:
        raw = self.get_ui_background() if path_value is None else str(path_value or "").strip()
        if not raw:
            return None
        path = Path(raw).expanduser()
        return path if path.is_absolute() else (self._path.parent / path)

    def install_ui_background(self, source: Path) -> str:
        source = Path(source).expanduser().resolve()
        if not source.is_file():
            raise ValueError("The selected UI background image does not exist.")
        suffix = source.suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
            raise ValueError("UI background must be PNG, JPG, BMP, or WEBP.")
        background_dir = self._path.parent / "ui-backgrounds"
        background_dir.mkdir(parents=True, exist_ok=True)
        destination = background_dir / f"background-{uuid.uuid4().hex[:12]}{suffix}"
        shutil.copy2(source, destination)
        relative = destination.relative_to(self._path.parent).as_posix()
        self.set_ui_background(relative)
        return relative

    def install_ui_background_bytes(self, filename: str, content: bytes) -> str:
        """Install a browser-uploaded background through the same Core store."""
        suffix = Path(str(filename or "")).suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
            raise ValueError("UI background must be PNG, JPG, BMP, or WEBP.")
        if not content:
            raise ValueError("UI background image is empty.")
        if len(content) > 10 * 1024 * 1024:
            raise ValueError("UI background image must be no larger than 10 MB.")
        if not _looks_like_image(content, suffix):
            raise ValueError("UI background data does not match its image type.")
        background_dir = self._path.parent / "ui-backgrounds"
        background_dir.mkdir(parents=True, exist_ok=True)
        destination = background_dir / f"background-{uuid.uuid4().hex[:12]}{suffix}"
        destination.write_bytes(content)
        relative = destination.relative_to(self._path.parent).as_posix()
        self.set_ui_background(relative)
        return relative

    def get_ui_background_opacity(self) -> int:
        try:
            value = int(self._data.get("ui_background_opacity", DEFAULT_UI_BACKGROUND_OPACITY))
        except (TypeError, ValueError):
            value = DEFAULT_UI_BACKGROUND_OPACITY
        return max(15, min(100, value))

    def set_ui_background_opacity(self, value: int) -> None:
        clean = max(15, min(100, int(value)))
        self._update(lambda data: data.__setitem__("ui_background_opacity", clean))

    def get_ui_background_zoom(self) -> int:
        try:
            value = int(self._data.get("ui_background_zoom", DEFAULT_UI_BACKGROUND_ZOOM))
        except (TypeError, ValueError):
            value = DEFAULT_UI_BACKGROUND_ZOOM
        return max(100, min(400, value))

    def get_ui_background_focus(self) -> tuple[float, float]:
        def normalise(value: object) -> float:
            try:
                return max(0.0, min(1.0, float(value)))
            except (TypeError, ValueError):
                return DEFAULT_UI_BACKGROUND_FOCUS

        return (
            normalise(self._data.get("ui_background_focus_x")),
            normalise(self._data.get("ui_background_focus_y")),
        )

    def set_ui_background_crop(
        self,
        zoom: int,
        focus_x: float,
        focus_y: float,
    ) -> None:
        clean_zoom = max(100, min(400, int(zoom)))
        clean_x = max(0.0, min(1.0, float(focus_x)))
        clean_y = max(0.0, min(1.0, float(focus_y)))

        def mutate(data: dict[str, Any]) -> None:
            data["ui_background_zoom"] = clean_zoom
            data["ui_background_focus_x"] = clean_x
            data["ui_background_focus_y"] = clean_y

        self._update(mutate)

    # ── Actions → MenuItem tree ───────────────────────────────────────────────

    def load_actions(self) -> list[MenuItem]:
        """Return the enabled root actions as a ``MenuItem`` tree."""
        return [
            self._to_menu_item(a)
            for a in self._data.get("actions", [])
            if a.get("enabled", True)
        ]

    def _to_menu_item(self, action: dict) -> MenuItem:
        children = [
            self._to_menu_item(s)
            for s in action.get("sub_actions", [])
            if s.get("enabled", True)
        ]
        # Items with sub_actions are implicitly folders (action_type = "")
        action_type = "" if children else self._normalise_type(action.get("type", ""))
        action_payload = "" if action.get("type") == "powershell_library" else action.get("target", "")
        return MenuItem(
            id             = action.get("id", "") or _new_id(),
            label          = action.get("label", ""),
            icon           = action.get("icon", ""),
            short_label    = action.get("short_label", ""),
            action_type    = action_type,
            action_payload = action_payload,
            children       = children,
        )

    @staticmethod
    def _normalise_type(t: str) -> str:
        """Map schema type strings to MenuItem.action_type values."""
        return {
            "folder":     "",
            "url":        "url",
            "command":    "command",
            "powershell": "powershell",
            "powershell_library": "powershell_library",
            "environment_check": "environment_check",
            "client_workspace": "client_workspace",
            "settings":   "settings",
            "app":        "app",
            "paste":      "paste",
            "form":       "form",
            "ps_form":    "ps_form",
        }.get(t, t)   # unknown types pass through unchanged

    def reload(self) -> None:
        """Re-read actions.json from disk, replacing in-memory state."""
        self._data = self._load_or_create()

    # ── Raw access (for future Settings GUI) ──────────────────────────────────

    def get_raw_actions(self) -> list[dict]:
        """Return a detached raw action snapshot (for editing)."""
        return copy.deepcopy(self._data.get("actions", []))

    def save_raw_actions(self, actions: list[dict]) -> None:
        """Persist an edited action list back to disk."""
        self._action_service.replace_all(actions)

    @property
    def action_service(self) -> ActionConfigService:
        """Transport-neutral service used by Native UI and future adapters."""
        return self._action_service

    # ActionRepository implementation. These methods intentionally remain
    # narrower than the compatibility APIs above.
    def action_snapshot(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._data.get("actions", []))

    def replace_action_snapshot(self, actions: list[dict[str, Any]]) -> None:
        clean = normalise_actions(actions)

        def mutate(data: dict[str, Any]) -> None:
            data["actions"] = clean

        self._update(mutate)

    # Convenience facades preserve a simple Core API for non-UI callers.
    def create_action(
        self,
        action: Mapping[str, Any],
        *,
        parent_id: str | None = None,
        index: int | None = None,
    ) -> ActionMutationResult:
        return self._action_service.create(action, parent_id=parent_id, index=index)

    def update_action(
        self,
        action_id: str,
        changes: Mapping[str, Any],
    ) -> ActionMutationResult:
        return self._action_service.update(action_id, changes)

    def delete_action(self, action_id: str) -> ActionMutationResult:
        return self._action_service.delete(action_id)

    def reorder_actions(
        self,
        ordered_ids: Sequence[str],
        *,
        parent_id: str | None = None,
    ) -> ActionMutationResult:
        return self._action_service.reorder(ordered_ids, parent_id=parent_id)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _new_id() -> str:
    return f"act_{uuid.uuid4().hex[:8]}"


def _looks_like_image(content: bytes, suffix: str) -> bool:
    if suffix == ".png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if suffix in {".jpg", ".jpeg"}:
        return content.startswith(b"\xff\xd8\xff")
    if suffix == ".bmp":
        return content.startswith(b"BM")
    if suffix == ".webp":
        return content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    return False
