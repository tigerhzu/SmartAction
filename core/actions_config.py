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
import uuid
from pathlib import Path

from core.debug_log import debug_log
from core.menu_model import MenuItem
from core.paths import CONFIG_DIR as _CONFIG_DIR

# ── Paths ─────────────────────────────────────────────────────────────────────

_CONFIG_PATH = _CONFIG_DIR / "actions.json"
_CONFIG_VERSION = "1.1"

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
        self._path = path
        self._data = self._load_or_create()
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
            with open(self._path, encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    data, changed = self._migrate(data)
                    if changed:
                        self._write_data(data)
                    debug_log(f"loaded existing actions config: {self._path.resolve()}")
                    return data
                except json.JSONDecodeError as exc:
                    print(f"[ActionsConfig] Corrupt JSON ({exc}); regenerating defaults.")

        # First run or corrupt file → write defaults
        data = copy.deepcopy(_DEFAULTS)
        self._write_data(data)
        print(f"[ActionsConfig] Created default config: {self._path}")
        debug_log("default actions config was auto-created")
        return data

    def _migrate(self, data: dict) -> tuple[dict, bool]:
        """Upgrade known legacy configs without replacing user actions."""
        version = str(data.get("version", ""))
        if version not in {"", "1.0"}:
            return data, False

        data.setdefault("constellation", _DEFAULTS["constellation"])
        data.setdefault("constellation_color", _DEFAULTS["constellation_color"])
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
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _save(self) -> None:
        self._write_data(self._data)

    # ── Hotkey ────────────────────────────────────────────────────────────────

    def get_hotkey(self) -> str:
        return self._data.get("hotkey", "ctrl+space")

    def set_hotkey(self, combo: str) -> None:
        self._data["hotkey"] = combo
        self._save()

    # ── Theme ─────────────────────────────────────────────────────────────────

    def get_theme(self) -> str:
        return self._data.get("theme", "tiger")

    def set_theme(self, theme_id: str) -> None:
        self._data["theme"] = theme_id
        self._save()

    def get_constellation(self) -> str:
        from core.constellation import CONSTELLATIONS, DEFAULT_CONSTELLATION

        value = str(self._data.get("constellation", DEFAULT_CONSTELLATION))
        return value if value in CONSTELLATIONS else DEFAULT_CONSTELLATION

    def set_constellation(self, constellation_id: str) -> None:
        self._data["constellation"] = constellation_id
        self._save()

    def get_constellation_color(self) -> str:
        from core.constellation import normalise_constellation_color

        return normalise_constellation_color(self._data.get("constellation_color"))

    def set_constellation_color(self, color: str) -> None:
        from core.constellation import normalise_constellation_color

        self._data["constellation_color"] = normalise_constellation_color(color)
        self._save()

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
        """Return the raw action list from JSON (for editing)."""
        return self._data.get("actions", [])

    def save_raw_actions(self, actions: list[dict]) -> None:
        """Persist an edited action list back to disk."""
        self._data["actions"] = actions
        self._save()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _new_id() -> str:
    return f"act_{uuid.uuid4().hex[:8]}"
