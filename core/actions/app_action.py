"""
AppAction — open an application or file with the OS default handler.

payload : path to an executable, document, or folder
          e.g.  "C:\\Windows\\notepad.exe"
                "C:\\Users\\user\\report.pdf"
                "C:\\Projects"

On Windows os.startfile() is used, which delegates to the shell
(same as double-clicking the file in Explorer).
On macOS / Linux a subprocess fallback is used instead.
"""
import os
import subprocess
import sys

from core.actions.base import BaseAction
from core.actions.registry import register_action


@register_action
class AppAction(BaseAction):
    action_type = "app"

    def execute(self, payload: str, context: dict) -> None:
        if not payload:
            print("[AppAction] Empty payload — nothing to open.")
            return
        try:
            if sys.platform == "win32":
                os.startfile(payload)          # open with default associated program
            elif sys.platform == "darwin":
                subprocess.Popen(["open", payload])
            else:
                subprocess.Popen(["xdg-open", payload])
        except Exception as exc:
            print(f"[AppAction] Failed to open {payload!r}: {exc}")
