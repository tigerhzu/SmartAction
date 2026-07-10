"""Clipboard + synthetic keypress helper shared by paste-type actions."""


def send_paste() -> None:
    """Copy text to clipboard then simulate Ctrl+V in the foreground window."""
    try:
        import keyboard
        keyboard.send("ctrl+v")
    except Exception as exc:
        print(f"[Clipboard] Failed to send Ctrl+V: {exc}")
