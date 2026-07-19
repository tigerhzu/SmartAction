from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path


UNICODE_EMOJI_TEST_URL = "https://www.unicode.org/Public/emoji/latest/emoji-test.txt"
OUTPUT_PATH = Path("data/icons/emoji_database.json")


KEYWORD_OVERRIDES: dict[str, list[str]] = {
    "tiger face": ["tiger", "cat", "animal", "brand", "smartaction"],
    "tiger": ["tiger", "cat", "animal", "wild"],
    "globe showing europe-africa": ["browser", "web", "internet", "network"],
    "globe showing americas": ["browser", "web", "internet", "network"],
    "globe with meridians": ["browser", "web", "internet", "network"],
    "compass": ["browser", "navigation", "portal"],
    "magnifying glass tilted left": ["search", "find", "browser"],
    "magnifying glass tilted right": ["search", "find", "browser"],
    "file folder": ["folder", "files", "directory"],
    "open file folder": ["folder", "files", "directory"],
    "card index dividers": ["folder", "tabs", "files"],
    "antenna bars": ["network", "wifi", "signal"],
    "wireless": ["network", "wifi", "signal"],
    "satellite antenna": ["network", "satellite", "signal"],
    "electric plug": ["network", "power", "connect"],
    "locked": ["security", "lock", "secure"],
    "locked with key": ["security", "lock", "key"],
    "locked with pen": ["security", "lock", "auth"],
    "shield": ["security", "firewall", "protect"],
    "key": ["security", "password", "auth"],
    "police car light": ["security", "alert", "incident"],
    "warning": ["security", "alert", "caution"],
    "cloud": ["cloud", "azure", "m365"],
    "cloud with lightning": ["cloud", "storm", "sync"],
    "sun behind cloud": ["cloud", "weather"],
    "outbox tray": ["cloud", "upload", "send"],
    "inbox tray": ["cloud", "download", "receive"],
    "laptop": ["terminal", "dev", "code"],
    "keyboard": ["terminal", "input", "keys"],
    "gear": ["terminal", "settings", "system", "config"],
    "envelope": ["mail", "email", "message"],
    "e-mail": ["mail", "email", "message"],
    "incoming envelope": ["mail", "email", "inbox"],
    "mobile phone": ["phone", "device", "mobile"],
    "telephone": ["phone", "call", "support"],
}


CUSTOM_ITEMS = [
    ("1F42F", "Tiger Face", "Tiger / Brand", ["tiger", "animal", "cat", "face", "brand", "smartaction"]),
    ("1F405", "Tiger", "Tiger / Brand", ["tiger", "animal", "cat", "wild"]),
    ("1F525", "Fire", "Tiger / Brand", ["brand", "energy", "hot", "fire"]),
    ("26A1", "High Voltage", "Tiger / Brand", ["brand", "power", "fast", "lightning"]),
    ("1F451", "Crown", "Tiger / Brand", ["brand", "premium", "king"]),
    ("1F916", "Robot", "AI", ["ai", "bot", "assistant", "automation"]),
    ("1F9E0", "Brain", "AI", ["ai", "smart", "thinking", "model"]),
    ("2728", "Sparkles", "AI", ["ai", "magic", "clean", "enhance"]),
    ("1F4A1", "Idea", "AI", ["idea", "tip", "insight"]),
    ("1F3AF", "Target", "AI", ["goal", "precision", "focus"]),
    ("1F680", "Rocket", "AI", ["launch", "deploy", "boost"]),
    ("1F52C", "Microscope", "AI", ["research", "analyze", "science"]),
    ("1F4BB", "Laptop", "Development", ["dev", "code", "programming", "terminal"]),
    ("1F9D1 200D 1F4BB", "Technologist", "Development", ["dev", "code", "programmer"]),
    ("1F6E0 FE0F", "Tools", "Development", ["build", "tools", "maintenance"]),
    ("2699 FE0F", "Gear", "Development", ["settings", "config", "terminal"]),
    ("1F9EA", "Test Tube", "Development", ["test", "qa", "experiment"]),
    ("1F41E", "Bug", "Development", ["bug", "debug", "fix"]),
    ("1F4E6", "Package", "Development", ["package", "deploy", "release"]),
    ("1F527", "Wrench", "Development", ["fix", "repair", "tool"]),
    ("2699 FE0F", "Gear", "System", ["settings", "config", "system"]),
    ("1F5A5 FE0F", "Desktop Computer", "System", ["monitor", "screen", "system"]),
    ("1FA9F", "Window", "System", ["windows", "app", "desktop"]),
    ("1F50B", "Battery", "System", ["power", "charge", "device"]),
    ("1F9F9", "Broom", "System", ["clean", "cleanup", "maintenance"]),
    ("1F9F0", "Toolbox", "System", ["repair", "maintenance", "it"]),
    ("1F6E1 FE0F", "Shield", "System", ["security", "protect", "defender"]),
    ("1F4C1", "File Folder", "Files & Storage", ["folder", "files", "directory"]),
    ("1F4C2", "Open File Folder", "Files & Storage", ["folder", "open", "files"]),
    ("1F5C2 FE0F", "Card Index Dividers", "Files & Storage", ["folder", "tabs", "index"]),
    ("1F4BE", "Floppy Disk", "Files & Storage", ["save", "storage", "backup"]),
    ("1F5C4 FE0F", "File Cabinet", "Files & Storage", ["database", "archive", "storage"]),
    ("1F4C4", "Page Facing Up", "Files & Storage", ["file", "document", "paper"]),
    ("1F4D1", "Bookmark Tabs", "Files & Storage", ["document", "tabs", "office"]),
    ("1F310", "Globe With Meridians", "Network", ["network", "web", "internet", "browser"]),
    ("1F4E1", "Satellite Antenna", "Network", ["network", "signal", "satellite"]),
    ("1F6DC", "Wireless", "Network", ["network", "wifi", "wireless"]),
    ("1F50C", "Electric Plug", "Network", ["network", "connect", "power"]),
    ("1F9ED", "Compass", "Network", ["network", "navigate", "browser"]),
    ("1F6F0 FE0F", "Satellite", "Network", ["network", "space", "signal"]),
    ("1F512", "Locked", "Security", ["security", "lock", "secure"]),
    ("1F510", "Locked With Key", "Security", ["security", "lock", "auth"]),
    ("1F6E1 FE0F", "Shield", "Security", ["security", "firewall", "protect"]),
    ("1F511", "Key", "Security", ["security", "password", "credential"]),
    ("1F6A8", "Police Car Light", "Security", ["security", "alert", "incident"]),
    ("26A0 FE0F", "Warning", "Security", ["security", "warning", "caution"]),
    ("2601 FE0F", "Cloud", "Cloud", ["cloud", "azure", "m365"]),
    ("1F329 FE0F", "Cloud With Lightning", "Cloud", ["cloud", "storm", "sync"]),
    ("26C5", "Sun Behind Cloud", "Cloud", ["cloud", "weather"]),
    ("1F4E4", "Outbox Tray", "Cloud", ["cloud", "upload", "send"]),
    ("1F4E5", "Inbox Tray", "Cloud", ["cloud", "download", "receive"]),
    ("1F5C4 FE0F", "File Cabinet", "Cloud", ["cloud", "storage", "database"]),
    ("1F4CA", "Bar Chart", "Work / Office", ["chart", "report", "excel"]),
    ("1F4C8", "Chart Increasing", "Work / Office", ["chart", "growth", "business"]),
    ("1F4C5", "Calendar", "Work / Office", ["calendar", "schedule", "meeting"]),
    ("1F4DD", "Memo", "Work / Office", ["note", "write", "task"]),
    ("1F4CC", "Pushpin", "Work / Office", ["pin", "important", "bookmark"]),
    ("1F4CE", "Paperclip", "Work / Office", ["attach", "clip", "office"]),
    ("1F4BC", "Briefcase", "Work / Office", ["work", "office", "client"]),
    ("1F310", "Globe", "Browser / Web", ["browser", "web", "internet", "url"]),
    ("1F9ED", "Compass", "Browser / Web", ["browser", "navigation", "portal"]),
    ("1F50E", "Magnifying Glass", "Browser / Web", ["browser", "search", "find"]),
    ("1FA9F", "Window", "Apps", ["app", "application", "window", "desktop"]),
    ("1F4F1", "Mobile App", "Apps", ["app", "mobile", "phone", "device"]),
    ("1F9E9", "Puzzle Piece", "Apps", ["plugin", "extension", "module", "app"]),
    ("1F6E0 FE0F", "Tools", "Apps", ["utility", "tool", "maintenance", "app"]),
    ("1F3B5", "Musical Note", "Media", ["music", "audio", "sound"]),
    ("1F3AC", "Clapper Board", "Media", ["video", "film", "movie"]),
    ("1F5BC FE0F", "Framed Picture", "Media", ["image", "picture", "photo"]),
    ("1F399 FE0F", "Studio Microphone", "Media", ["audio", "voice", "recording"]),
    ("2705", "Check Mark Button", "Productivity", ["done", "complete", "ok", "task"]),
    ("1F4CC", "Pushpin", "Productivity", ["pin", "important", "bookmark"]),
    ("1F4DD", "Memo", "Productivity", ["note", "write", "task"]),
    ("23F1 FE0F", "Stopwatch", "Productivity", ["timer", "time", "quick"]),
    ("1F5A8 FE0F", "Printer", "Devices", ["print", "device", "hardware"]),
    ("1F5B1 FE0F", "Computer Mouse", "Devices", ["mouse", "cursor", "click"]),
    ("1F50B", "Battery", "Devices", ["power", "charge", "device"]),
    ("1F4F7", "Camera", "Devices", ["camera", "photo", "webcam"]),
    ("2709 FE0F", "Envelope", "Communication", ["mail", "email", "message"]),
    ("1F4E7", "E-Mail", "Communication", ["mail", "email", "message"]),
    ("1F4EC", "Open Mailbox", "Communication", ["mail", "email", "inbox"]),
    ("1F4F1", "Mobile Phone", "Devices", ["phone", "mobile", "device"]),
    ("260E FE0F", "Telephone", "Communication", ["phone", "call", "support"]),
]


def icon_from_hex(value: str) -> str:
    return "".join(chr(int(part, 16)) for part in value.split())


def clean_words(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.casefold())
    return [word for word in words if len(word) > 1]


def has_skin_tone_modifier(icon: str) -> bool:
    """Return whether an emoji sequence contains a Fitzpatrick modifier."""
    return any(0x1F3FB <= ord(char) <= 0x1F3FF for char in icon)


def parse_emoji_test(text: str) -> list[dict]:
    group = ""
    subgroup = ""
    items: list[dict] = []
    seen: set[tuple[str, str]] = set()
    pattern = re.compile(r"^(.+?)\s+E[0-9.]+\s+(.+)$")

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("# group:"):
            group = line.split(":", 1)[1].strip()
            continue
        if line.startswith("# subgroup:"):
            subgroup = line.split(":", 1)[1].strip()
            continue
        if not line or line.startswith("#") or "fully-qualified" not in line or "#" not in line:
            continue

        _, comment = line.split("#", 1)
        match = pattern.match(comment.strip())
        if not match:
            continue
        icon = match.group(1).strip()
        # Keep only Unicode's default (yellow/unspecified) presentation. Skin
        # tone variants account for thousands of near-identical picker cells.
        if has_skin_tone_modifier(icon):
            continue
        name = match.group(2).strip().title()
        name_key = name.casefold()
        key = (icon, group)
        if key in seen:
            continue
        seen.add(key)

        keywords = clean_words(name)
        keywords.extend(clean_words(group))
        keywords.extend(clean_words(subgroup.replace("-", " ")))
        keywords.extend(KEYWORD_OVERRIDES.get(name_key, []))

        items.append(
            {
                "icon": icon,
                "name": name,
                "category": group,
                "keywords": sorted(set(keywords)),
                "aliases": [],
            }
        )
    return items


def custom_items() -> list[dict]:
    items: list[dict] = []
    for icon_hex, name, category, keywords in CUSTOM_ITEMS:
        base_keywords = clean_words(name)
        base_keywords.extend(clean_words(category))
        base_keywords.extend(keywords)
        items.append(
            {
                "icon": icon_from_hex(icon_hex),
                "name": name,
                "category": category,
                "keywords": sorted(set(base_keywords)),
                "aliases": [],
            }
        )
    return items


def download_unicode_data(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8")


def build_database(source: Path | None = None, url: str = UNICODE_EMOJI_TEST_URL) -> list[dict]:
    if source:
        text = source.read_text(encoding="utf-8")
    else:
        text = download_unicode_data(url)
    return parse_emoji_test(text) + custom_items()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build SmartAction emoji database.")
    parser.add_argument("--source", type=Path, help="Local emoji-test.txt path.")
    parser.add_argument("--url", default=UNICODE_EMOJI_TEST_URL)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    items = build_database(args.source, args.url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(items)} emoji records to {args.output}")


if __name__ == "__main__":
    main()
