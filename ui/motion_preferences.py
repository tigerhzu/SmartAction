"""Compatibility facade for the Core-owned runtime preference."""
from core.runtime_preferences import RuntimePreferencesService


def reduced_motion_enabled() -> bool:
    return RuntimePreferencesService.reduced_motion_enabled()


def set_reduced_motion_enabled(enabled: bool) -> None:
    RuntimePreferencesService.set_reduced_motion_enabled(enabled)
