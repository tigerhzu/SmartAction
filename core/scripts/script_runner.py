from __future__ import annotations

import subprocess
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.paths import SCRIPTS_DIR


class ScriptWorker(QThread):
    """Runs a .ps1 file in a background thread; emits (success, output) when done."""

    finished: Signal = Signal(bool, str)

    def __init__(self, script_name: str, params: dict, parent=None) -> None:
        super().__init__(parent)
        self._script_path = SCRIPTS_DIR / f"{script_name}.ps1"
        self._params = params

    def run(self) -> None:
        if not self._script_path.exists():
            self.finished.emit(False, f"Script not found: {self._script_path}")
            return

        args: list[str] = []
        for k, v in self._params.items():
            args.extend([f"-{k}", str(v)])

        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", str(self._script_path),
        ] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            out = result.stdout.strip()
            err = result.stderr.strip()
            # Remove PS error prefix noise
            err = err.replace("Write-Error: ", "").strip()
            combined = "\n".join(filter(None, [out, err]))
            self.finished.emit(result.returncode == 0, combined)
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Timeout：Script 執行超過 60 秒。")
        except Exception as exc:
            self.finished.emit(False, str(exc))
