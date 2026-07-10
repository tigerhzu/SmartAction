from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


HOST_NAME = "smartaction_firefox_helper"
REG_PATH = rf"Software\Mozilla\NativeMessagingHosts\{HOST_NAME}"
SMARTACTION_LOCAL_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "SmartAction"
HOST_INSTALL_DIR = SMARTACTION_LOCAL_DIR / "firefox_helper_host"


def main() -> int:
    if sys.platform != "win32":
        print("This installer is for Windows only.")
        return 1

    import winreg

    source_dir = Path(__file__).resolve().parent
    source_host_py = source_dir / "smartaction_firefox_host.py"
    source_template = source_dir / "host_manifest.json.template"

    HOST_INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    host_py = HOST_INSTALL_DIR / "smartaction_firefox_host.py"
    wrapper = HOST_INSTALL_DIR / "smartaction_firefox_host.cmd"
    manifest = HOST_INSTALL_DIR / "host_manifest.json"
    template = HOST_INSTALL_DIR / "host_manifest.json.template"

    shutil.copy2(source_host_py, host_py)
    shutil.copy2(source_template, template)

    wrapper.write_text(
        f'@echo off\r\n"{sys.executable}" "{host_py}"\r\n',
        encoding="utf-8",
    )

    data = json.loads(template.read_text(encoding="utf-8").replace("__HOST_COMMAND__", str(wrapper).replace("\\", "\\\\")))
    manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest))

    print("SmartAction Container Helper Native Messaging Host installed.")
    print(f"Install dir: {HOST_INSTALL_DIR}")
    print(f"Manifest: {manifest}")
    print(f"Registry: HKCU\\{REG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
