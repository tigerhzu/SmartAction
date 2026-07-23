"""
Shared visual design tokens for SmartAction's dialogs.

Pure data/string constants — no Qt imports, no widget logic. This is the
single source of truth for the "cut steel, tiger ember" visual system
described in docs/ui-redesign-plan.md. Dialogs should reference these names
instead of hardcoding hex/pixel values so the whole app can be restyled by
editing one file.

This module does not (yet) get applied to any dialog's QSS — that happens
incrementally, one screen at a time, in later redesign passes.
"""
from __future__ import annotations

from core.fonts import UI_DISPLAY_FONT_CANDIDATES, UI_FONT_CANDIDATES

# ── Color ─────────────────────────────────────────────────────────────────────
# Base surfaces (darkest → lightest)
VOID     = "#0B0D10"   # app / dialog background
CHARCOAL = "#15181D"   # panels, inputs, tables
STEEL    = "#1E2229"   # hover backgrounds, disabled surfaces
ASH      = "#2A2F38"   # hairline borders / dividers

# Text
BONE = "#ECE8E1"   # primary text (warm off-white, not stark white)
FOG  = "#9AA0AA"   # secondary / muted text, placeholders

# Brand accent — "Tiger ember"
EMBER         = "#F2760B"   # primary accent — buttons, selection, focus
EMBER_HOVER   = "#FF8B2E"   # hover state
EMBER_PRESSED = "#C2570A"   # active/pressed state
EMBER_WASH    = "rgba(242, 118, 11, 0.12)"   # selected-row tint, not a glow

# Ring launcher accents
NEON_CYAN       = "#3DF6FF"
RING_LABEL_BG   = "#0F1218"
RING_LABEL_EDGE = "#36404D"

# Semantic
SIGNAL_RED         = "#E5484D"   # danger / destructive actions
SIGNAL_RED_HOVER   = "#F16065"
SIGNAL_RED_PRESSED = "#C93E42"
SIGNAL_RED_WASH    = "rgba(229, 72, 77, 0.12)"
SIGNAL_GREEN      = "#3FB27F"   # success / connected
SIGNAL_GREEN_WASH = "rgba(63, 178, 127, 0.12)"
SIGNAL_AMBER = "#D9932A"   # warning
SIGNAL_AMBER_WASH = "rgba(217, 147, 42, 0.12)"

# ── Spacing scale (px, 4px base grid) ─────────────────────────────────────────
SPACE_4  = 4
SPACE_8  = 8
SPACE_12 = 12
SPACE_16 = 16
SPACE_20 = 20
SPACE_24 = 24
SPACE_32 = 32
SPACE_40 = 40

# ── Shape ─────────────────────────────────────────────────────────────────────
# Signature element: a single cut top-right corner instead of a rounded one.
CORNER_CUT_PX = 6

# ── Typography ────────────────────────────────────────────────────────────────
# Body/UI face — native Windows, zero bundling risk.
BODY_FONT_FAMILY = f'"{UI_FONT_CANDIDATES[0]}"'
# Display/headline face — bundled (see core/fonts.py), used sparingly for
# dialog titles, ring branding, and about-page text only. Never body text.
HEADLINE_FONT_FAMILY = UI_DISPLAY_FONT_CANDIDATES[0]
# Console/monospace — already used by PowerShell Library / Environment Check.
MONO_FONT_FAMILY = 'Consolas, "Cascadia Mono", monospace'

# Type scale (px)
SIZE_DISPLAY     = 30   # ring/brand headline text (Oswald)
SIZE_H1          = 20   # dialog titles
SIZE_H2          = 14   # section labels
SIZE_BODY        = 14   # fields, buttons, general text
SIZE_BODY_DENSE  = 13   # table/list rows
SIZE_CAPTION     = 12   # secondary/help text
SIZE_MICRO       = 11   # version tags, timestamps
SIZE_MONO        = 13   # console/script output

# ── Control sizing ────────────────────────────────────────────────────────────
BUTTON_MIN_HEIGHT = 36
FIELD_HEIGHT      = 34
ROW_HEIGHT        = 36
