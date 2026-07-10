# SmartAction UI Audit

Date: 2026-07-09
Scope: every PySide6 (Qt) UI surface in `ui/`, `app/`, plus the data/theme layers that back them (`core/theme.py`, `core/config_manager.py`, `core/menu_model.py`).

This document only describes **what exists today**. No redesign decisions are made here — see `docs/ui-redesign-plan.md` for that.

---

## 1. What screens exist today

| Screen | File(s) | Reached from | Status |
|---|---|---|---|
| Dev launcher window | `ui/main_window.py` | Manual/dev run only | Live, minor |
| **Radial quick-launch menu ("the ring")** | `ui/ring_ui.py`, `ui/theme_painter.py`, `core/theme.py` | Global hotkey, tray | **Live, core product** |
| Settings (production) | `ui/settings_window.py` | Tray → "Open Settings", dev launcher | **Live, core product** |
| Settings (legacy sidebar) | `ui/settings_ui.py` + `ui/pages/*.py` | Nothing in the shipped app imports this | **Dead code** (see §3) |
| Emoji / icon picker | `ui/emoji_picker.py` | Launched from Settings' icon field | Live |
| Hotkey picker | `ui/hotkey_picker.py` | Launched from Settings' hotkey row | Live |
| Help viewer (Markdown) | `ui/help_modal.py` | Settings help menu | Live, low-traffic |
| Tray icon + menu | `ui/tray_icon.py` | Always running | Live, brand-defining (draws its own icon) |
| Startup splash | `ui/startup_splash.py` | App launch (video/gif/image) | Live |
| Client workspace manager | `ui/client_workspace_window.py` | Tray, dev launcher | Live, IT-support feature |
| PowerShell script library | `ui/powershell_library_window.py` | Tray, dev launcher | Live, IT-support feature |
| Environment check result | `ui/environment_check_window.py` | Triggered by an action | Live |
| PowerShell-backed forms (Add Local User, Join Domain) | `ui/forms/*.py` | Triggered by an action | Live, **has a reboot side effect** |

## 2. Purpose of each screen

- **Ring (radial menu)** — the product's signature interaction: press a hotkey, a translucent 8-slot wheel appears at the cursor, each slot is an app/URL/PowerShell/folder shortcut. Supports nested folders (drill-in/back) and 5 visual themes (`purple`, `tiger`, `ice`, `lava`, `cosmic`).
- **Settings window** — CRUD for the action list that populates the ring: labels, icons, action type/target, sub-actions, hotkey, theme picker, profile import/export.
- **Emoji/icon picker** — assigns an icon (emoji or bundled icon) to any action; has recent/favorites, search, category tabs.
- **Hotkey picker** — click-based (no raw key capture) builder for the global show-ring hotkey, with a dangerous-shortcut blocklist.
- **Client workspace** — for IT-support use: define a client, a Firefox container, and a set of maintenance URLs; "Launch Workspace" opens them all at once.
- **PowerShell library** — a catalog of reusable admin scripts with risk levels, parameters, and a mandatory confirmation gate before running anything marked "dangerous."
- **Environment check / forms** — one-off diagnostic and provisioning dialogs (add local user, join domain) run via background PowerShell.
- **Startup splash / tray** — app entry chrome; splash plays a short video/gif/image on launch, tray hosts the persistent background presence and quick actions.

## 3. Current UI problems

1. **No unified visual system.** There is no `app.setStyleSheet()`, no QSS resource file in actual use (`resources/styles/dark.qss` / `light.qss` are empty placeholders, not loaded anywhere), no QPalette theming. Every dialog defines its own near-duplicate `_BTN_PRIMARY` / `_FIELD` / `_TABLE` QSS strings inline in Python.
2. **Two competing accent colors.** Most dialogs use purple (`#5B21B6`/`#6D28D9`/`#4C1D95`), but `ui/widgets.py`, `ui/forms/base_form.py`, and the entire legacy `ui/pages/*` + `ui/settings_ui.py` cluster use a different blue (`#2563EB`/`#1D4ED8`). A single app should not have two brand accents.
3. **Looks like a generic form app, not a branded tool.** No custom typography (nothing ever sets a font family — everything falls back to the Windows default UI font), light-mode `QLineEdit`/`QTableWidget`/`QPushButton` defaults dominate every screen except the ring itself and a few "console" panels. This is the core complaint driving the redesign request.
4. **Inconsistent "dark console" pockets.** `powershell_library_window.py`'s script table/details, `environment_check_window.py`'s output panel, and `settings_window.py`'s theme-picker strip are dark islands inside otherwise all-white dialogs — a deliberate-looking but never-unified pattern.
5. **Duplicated palette source of truth.** `core/theme.py`'s `THEMES` dict (used by ring rendering + Settings swatches) has an independent, hand-kept-in-sync duplicate in `ui/theme_painter.py`'s `_theme_colors()`. Editing one without the other silently desyncs the "official" swatch color from the procedural-fallback render.
6. **Dead/legacy code still shipping.** `ui/settings_ui.py` + `ui/pages/{about,general,hotkey,menus}_page.py` (≈780 lines) implement an entire second Settings UI on a different data model (`ConfigManager.menu_items` / `MenuItem` tree) that the live app never opens (`app/application.py` only ever constructs `ui.settings_window.SettingsWindow`). `ui/menu_editor.py` is a 2-line stub. These inflate the surface area a redesign could mistakenly "fix" for no benefit.
7. **Small/inconsistent type scale.** Body text is `13px` almost everywhere, captions `11–12px`, titles `14–22px` — workable but tight for a "premium tool" feel, and sizes aren't tied to any scale (e.g. `settings_window.py` mixes `12px` table text with `13px` fields with ad hoc `14–22px` headers, chosen per-dialog rather than from a scale).
8. **Bilingual copy baked into base classes.** `ui/forms/base_form.py` and its subclasses default to Traditional Chinese status strings; `client_workspace_window.py` mixes Chinese and English UI copy. Not a bug, but any redesign of copy/labels must treat this as bilingual, not English-only.
9. **Minor inconsistencies worth cleaning up:** icon-picker grid uses `COLS = 8` while hotkey-picker hardcodes `10` columns inline; separator gray `#E8E8EE` (widgets.py) vs `#E5E7EB` (everywhere else); legacy `ConfigManager` default theme string `"dark"` doesn't match any key in `THEMES`.

## 4. Files responsible for UI (by risk tier)

**Tier 1 — highest value, highest risk (custom-painted, animated):**
- `ui/ring_ui.py` (722 lines) — the ring itself. Full custom `QPainter` drawing, coordinate-transform stack, hit-testing math, open/close/nav animations, a 42ms theme-frame timer.
- `ui/theme_painter.py` (369 lines) — shared "energy bubble" rendering used by both the ring and the Settings theme cards.
- `core/theme.py` (128 lines) — the theme color data (`THEMES` dict), the only real design-token file today.

**Tier 2 — largest surface, high value:**
- `ui/settings_window.py` (1939 lines) — production Settings; custom-painted `_ActionListWidget` (drag handles) and `_ThemeCard` widgets live here too.
- `ui/client_workspace_window.py` (981 lines)
- `ui/powershell_library_window.py` (603 lines)
- `ui/emoji_picker.py` (636 lines)
- `ui/hotkey_picker.py` (353 lines)

**Tier 3 — small, low-risk, high visual-consistency payoff:**
- `ui/main_window.py`, `ui/help_modal.py`, `ui/tray_icon.py`, `ui/startup_splash.py`, `ui/environment_check_window.py`, `ui/widgets.py`, `ui/forms/*.py`.

**Tier 4 — likely dead, confirm before touching:**
- `ui/settings_ui.py`, `ui/pages/about_page.py`, `ui/pages/general_page.py`, `ui/pages/hotkey_page.py`, `ui/pages/menus_page.py`, `ui/menu_editor.py`.

## 5. Where to focus first (highest visual impact, most reachable)

In rough priority order:

1. **A single shared style module** (new file, e.g. `ui/style.py` or `core/theme_tokens.py`) holding the full token set (colors, spacing, radii, type scale) so every dialog stops hand-copying QSS strings. This is the prerequisite for everything else and touches no risky logic.
2. **Settings window** (`ui/settings_window.py`) — largest, most-used surface; swapping its QSS constants to reference shared tokens is low-risk (pure string substitution) and highest visible payoff.
3. **Tray icon** (`ui/tray_icon.py`) — tiny file, but it is literally the brand mark; updating its drawn colors to match a new palette is cheap and immediately visible everywhere (every user sees it constantly).
4. **Ring theme set** (`core/theme.py` + `theme_painter.py`) — already has a `tiger` theme; making it (or a new premium variant) the default, and fixing the palette duplication between the two files, directly serves the "Tiger / power / premium" brief.
5. **Client workspace / PowerShell library / emoji / hotkey dialogs** — once shared tokens exist, restyling these is mechanical (swap inline QSS constants) with low logic risk, since none of them have as much custom-paint coupling as the ring or `_ActionListWidget`.
6. **Startup splash + main window** — small, cosmetic-only, safe to reskin any time.

## 6. Where NOT to make careless changes

- **`ui/ring_ui.py` paint/hit-test coupling.** The `paintEvent` transform stack (translate → scale → translate), `_slot_centre()` trig math, and `_hit_slot`/`_hit_centre` hit-testing all assume identical geometry constants. Any resize of `ITEM_RADIUS`, `ITEM_ORBIT`, `NUM_SLOTS`, or `WINDOW_SIZE` must update paint math and hit-test math together, and be retested across multi-monitor cursor positions (`_position_at_cursor` clamps to screen bounds).
- **The dismiss/outside-click state machine** in `ring_ui.py` (`_outside_click_enabled`, `_is_dismissing`, `_pressed_inside_ring`, `_ignore_next_click`, plus a 150ms guard timer). Heavily `debug_log`-instrumented — evidence of past bugs. Do not "simplify" without testing every open/dismiss path.
- **Theme timer lifecycle.** Both `ring_ui.py` and `settings_window.py` start/stop a 42ms `QTimer` on show/hide. A redesign changing show/hide flow must keep start/stop paired, or a timer will keep firing against a hidden widget.
- **`core/theme.py` vs `theme_painter.py`'s `_theme_colors()` duplication.** These must be edited together. Introducing a new theme or recoloring an existing one in only one file will make the ring and its Settings preview swatch disagree.
- **`_ActionListWidget`'s drag-handle hit region** (`_HANDLE_WIDTH = 34`) is manually kept in sync with the QSS `padding: 9px 42px 9px 14px` on the list rows. Changing row height/padding without updating the handle rect breaks drag-to-reorder hit-testing.
- **Immediate-save-on-reorder.** Reordering actions in Settings writes to disk instantly (`_config.save_raw_actions`), unlike every other field which only commits on the dialog's Save button. A redesign must not accidentally change this asymmetry without deciding it's intentional.
- **`action_type` branching in `_SubActionDialog`** (`folder`, `powershell_library`, `environment_check`, `client_workspace`, etc.) gates which fields are visible. A layout redesign that reorders/hides fields without preserving this branching will silently break specific action types.
- **`ConfirmRunDialog` in the PowerShell library** — a genuine safety gate for scripts marked `"dangerous"`. Never visually de-emphasize or bypass this confirmation.
- **`JoinDomainForm`'s reboot confirmation** (`ui/forms/join_domain_form.py`) can call `subprocess.Popen(["shutdown", "/r", "/t", "10"])`. Do not alter this Yes/No flow's default button or remove the confirmation while restyling.
- **Startup splash media fallback chain** (mp4 → gif → static image, with a runtime widget-swap for the video) is packaging-sensitive (frozen-exe path resolution). Test all three media types after any visual change here.
- **Bilingual strings** — don't assume any user-facing copy is English-only; Chinese strings are hardcoded defaults in several places, not just translations layered on top.
- **Legacy `settings_ui.py` / `pages/*` cluster** — confirm with the project owner that it's genuinely unreachable before deleting or redesigning; it's excluded from the redesign plan's scope by default, but removal is a separate decision from restyling.

## 7. Existing design-token foundation

`core/theme.py` is the only structured "token" file in the app today: a `THEMES` dict keyed `purple`/`tiger`/`ice`/`lava`/`cosmic`, each with a `preview_color` hex and RGBA tuples for slot/glow/rim/card colors. A `tiger` theme **already exists** (`preview_color: "#F97316"`) with matching painted assets in `assets/themes/tiger/` (rim.png, rim_active.png, card_bg.png, animated frame sequence). This is a strong existing foundation for the "Tiger / power / premium" brand direction requested for the redesign — it doesn't need to be invented from scratch, only extended into a proper app-wide token system and (likely) promoted to the default.
