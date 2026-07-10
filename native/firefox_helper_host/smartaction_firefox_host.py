from __future__ import annotations

import json
import os
import struct
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


HELPER_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "SmartAction" / "firefox_helper"
PENDING_LAUNCH_PATH = HELPER_DIR / "pending_launch.json"
LAST_RESULT_PATH = HELPER_DIR / "last_result.json"
LOG_PATH = HELPER_DIR / "helper.log"


def log(message: str) -> None:
    HELPER_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')} {message}\n")


def read_message() -> dict[str, Any] | None:
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        return None
    if len(raw_length) != 4:
        raise RuntimeError("Invalid native message length prefix.")
    message_length = struct.unpack("@I", raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode("utf-8")
    return json.loads(message)


def write_message(message: dict[str, Any]) -> None:
    encoded = json.dumps(message, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("@I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def load_pending_launch() -> dict[str, Any] | None:
    if not PENDING_LAUNCH_PATH.exists():
        return None
    with open(PENDING_LAUNCH_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or data.get("type") not in ("launch_workspace", "helper_check"):
        raise RuntimeError("pending_launch.json is not a supported helper request.")
    return data


def save_result(result: dict[str, Any]) -> None:
    HELPER_DIR.mkdir(parents=True, exist_ok=True)
    result["receivedAt"] = datetime.now().isoformat(timespec="seconds")
    with open(LAST_RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    try:
        PENDING_LAUNCH_PATH.unlink()
    except OSError:
        pass


def main() -> int:
    try:
        pending = load_pending_launch()
        if not pending:
            return 0
        log(f"sending launch request requestId={pending.get('requestId')}")
        write_message(pending)
        result = read_message()
        if result is None:
            log("no result from extension")
            return 1
        save_result(result)
        log(f"saved result success={result.get('success')} requestId={result.get('requestId')}")
        return 0
    except Exception as exc:
        log(f"error: {exc}")
        save_result(
            {
                "type": "helper_error_result",
                "success": False,
                "error": str(exc),
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
