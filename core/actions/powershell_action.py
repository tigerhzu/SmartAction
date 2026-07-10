"""
PowerShellAction — run a PowerShell command or script block.

payload : a PowerShell command string
          e.g. "Get-Process | Out-GridView"
               "Add-LocalUser -Name 'newuser' -Password (ConvertTo-SecureString ...)"

The process runs in a new PowerShell window (CREATE_NEW_CONSOLE) so the user
can see output and interact with prompts.
"""
import subprocess
import sys

from core.actions.base import BaseAction
from core.actions.registry import register_action


@register_action
class PowerShellAction(BaseAction):
    action_type = "powershell"

    def execute(self, payload: str, context: dict) -> None:
        if not payload:
            print("[PowerShellAction] Empty payload — nothing to run.")
            return
        try:
            cmd = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command", payload,
            ]
            kwargs: dict = {}
            if sys.platform == "win32":
                # Open a visible console so the user can interact with the script.
                kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
            subprocess.Popen(cmd, **kwargs)
        except Exception as exc:
            print(f"[PowerShellAction] Failed: {exc}")
