import json
from pathlib import Path

from core.debug_log import debug_log
from core.paths import RESOURCES_DIR

_CONFIG_PATH = RESOURCES_DIR / "config.json"

_DEFAULTS: dict = {
    "version": "0.1.0",
    "hotkey": "Alt+Space",
    "startup_video_enabled": False,
    "startup_video_duration": 5,
    "startup_video_path": "assets/startup/startup.png",
}


class ConfigManager:
    def __init__(self, path: Path = _CONFIG_PATH):
        self._path = path
        self._data = self._load()
        debug_log(f"legacy resources config path: {self._path.resolve()} exists={self._path.exists()}")

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> dict:
        if self._path.exists():
            with open(self._path, encoding="utf-8") as f:
                return json.load(f)
        return dict(_DEFAULTS)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self._save()

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
