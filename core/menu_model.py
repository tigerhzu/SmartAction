"""
Menu item tree model.

Each MenuItem can hold children (folder/submenu) or an action (leaf).
The tree can be arbitrarily deep — RingWindow handles navigation internally.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MenuItem:
    """A single node in the ring menu tree."""

    id: str
    label: str
    icon: str        = ""   # emoji shown inside the slot circle (overrides short_label)
    short_label: str = ""   # 1-3 char abbreviation shown inside the slot circle
    action_type: str = ""   # registered action key; "" means folder
    action_payload: str     = ""
    children: list[MenuItem] = field(default_factory=list)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @property
    def is_folder(self) -> bool:
        """True when this item navigates into a child ring level."""
        return bool(self.children)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        d: dict = {"id": self.id, "label": self.label}
        if self.icon:
            d["icon"] = self.icon
        if self.short_label:
            d["short_label"] = self.short_label
        if self.action_type:
            d["action_type"] = self.action_type
        if self.action_payload:
            d["action_payload"] = self.action_payload
        if self.children:
            d["children"] = [c.to_dict() for c in self.children]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> MenuItem:
        return cls(
            id             = data.get("id", ""),
            label          = data.get("label", ""),
            icon           = data.get("icon", ""),
            short_label    = data.get("short_label", ""),
            action_type    = data.get("action_type", ""),
            action_payload = data.get("action_payload", ""),
            children       = [cls.from_dict(c) for c in data.get("children", [])],
        )
