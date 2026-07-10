"""
CommandAction — run a shell command in the background.

payload : any command string accepted by cmd.exe (Windows) or /bin/sh (Unix)
          The process is detached — its output is NOT captured.

Example payloads:
  "notepad.exe"
  "explorer C:\\Users"
  "ping -n 4 8.8.8.8"
"""
import subprocess
import sys

from core.actions.base import BaseAction
from core.actions.registry import register_action


@register_action
class CommandAction(BaseAction):
    action_type = "command"

    def execute(self, payload: str, context: dict) -> None:
        if not payload:
            print("[CommandAction] Empty payload — nothing to run.")
            return
        try:
            kwargs: dict = {"shell": True}
            if sys.platform == "win32":
                # Detach from the parent console so the child survives after
                # the ring process exits; suppress any popup console window.
                kwargs["creationflags"] = (
                    subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
                )
            subprocess.Popen(payload, **kwargs)
        except Exception as exc:
            print(f"[CommandAction] Failed: {exc}")
