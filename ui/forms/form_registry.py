from __future__ import annotations

_FORM_REGISTRY: dict[str, type] = {}


def register_form(cls):
    """Class decorator — adds the class to the form registry by its form_id."""
    _FORM_REGISTRY[cls.form_id] = cls
    return cls


def get_form(form_id: str) -> type | None:
    return _FORM_REGISTRY.get(form_id)


def registered_forms() -> list[str]:
    return list(_FORM_REGISTRY)
