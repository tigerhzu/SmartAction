"""
Theme catalog for the Ring UI.

Each theme is a dict of RGBA tuples — no Qt imports, so this module
can be loaded anywhere without a QApplication.

Keys
----
name           Display name shown in Settings
preview_color  Hex string for the Settings theme-picker button background
slot           Leaf action bubble fill          (R, G, B, A)
slot_h         Leaf action bubble fill (hover)
folder         Folder bubble fill
folder_h       Folder bubble fill (hover)
glow           Drop-shadow tinted glow behind each bubble
shadow         Dark drop-shadow behind each bubble
center         Centre close/back button fill
center_x       Centre button fill when hovering over close action
center_b       Centre button fill when hovering over back action
rim            Inner highlight ring on the bubble edge
empty          Ghost ring for empty slot positions
card_bg        Floating label card background
card_text      Floating label card text
card_shadow    Floating label card drop-shadow
bubble_main    Energy-bubble rim gradient main color (ui.theme_painter, painter-fallback path)
bubble_dark    Energy-bubble rim gradient dark stop
bubble_highlight  Energy-bubble glass sheen / rim highlight stroke
bubble_glow    Energy-bubble outer glow tint (distinct from the `glow` key above)
"""
from __future__ import annotations

THEMES: dict[str, dict] = {
    "purple": {
        "name":          "Purple",
        "preview_color": "#7C3AED",
        "slot":          ( 88,  28, 175, 255),
        "slot_h":        (109,  40, 217, 255),
        "folder":        (109,  40, 217, 255),
        "folder_h":      (124,  58, 237, 255),
        "glow":          ( 88,  28, 175,  60),
        "shadow":        (  0,   0,   0,  40),
        "center":        ( 26,  18,  66, 230),
        "center_x":      (220,  50,  50, 245),
        "center_b":      ( 88,  28, 175, 245),
        "rim":           (255, 255, 255,  55),
        "empty":         (170, 140, 230,  22),
        "card_bg":       (255, 255, 255, 252),
        "card_text":     ( 26,  18,  66, 255),
        "card_shadow":   (  0,   0,   0,  30),
        "bubble_main":      (154,  79, 255, 255),
        "bubble_dark":      ( 83,  32, 188, 255),
        "bubble_highlight": (222, 198, 255, 210),
        "bubble_glow":      (139,  92, 246,  82),
    },
    "tiger": {
        "name":          "Tiger Fur",
        "preview_color": "#F97316",
        "slot":          (175,  72,  10, 255),
        "slot_h":        (217,  92,  15, 255),
        "folder":        (217,  92,  15, 255),
        "folder_h":      (249, 115,  22, 255),
        "glow":          (249, 115,  22,  60),
        "shadow":        (  0,   0,   0,  45),
        "center":        ( 28,  10,   4, 230),
        "center_x":      (220,  50,  50, 245),
        "center_b":      (217,  92,  15, 245),
        "rim":           (255, 210, 120,  55),
        "empty":         (200, 130,  55,  22),
        "card_bg":       (255, 247, 237, 252),
        "card_text":     ( 28,  15,   4, 255),
        "card_shadow":   (  0,   0,   0,  30),
        "bubble_main":      (255, 151,  34, 255),
        "bubble_dark":      ( 91,  40,   6, 255),
        "bubble_highlight": (255, 195,  86, 210),
        "bubble_glow":      (249, 115,  22,  88),
    },
    "ice": {
        "name":          "Ice / Frozen",
        "preview_color": "#38BDF8",
        "slot":          ( 10, 100, 160, 255),
        "slot_h":        ( 14, 132, 205, 255),
        "folder":        ( 14, 132, 205, 255),
        "folder_h":      ( 56, 189, 248, 255),
        "glow":          ( 56, 189, 248,  55),
        "shadow":        (  0,   0,   0,  38),
        "center":        (  8,  25,  38, 230),
        "center_x":      (220,  50,  50, 245),
        "center_b":      ( 14, 132, 205, 245),
        "rim":           (186, 230, 253,  65),
        "empty":         (100, 180, 230,  22),
        "card_bg":       (240, 249, 255, 252),
        "card_text":     (  8,  47,  73, 255),
        "card_shadow":   (  0,   0,   0,  28),
        "bubble_main":      (178, 243, 255, 255),
        "bubble_dark":      ( 28, 143, 211, 255),
        "bubble_highlight": (235, 255, 255, 225),
        "bubble_glow":      ( 56, 189, 248,  82),
    },
    "lava": {
        "name":          "Fire / Lava",
        "preview_color": "#EF4444",
        "slot":          (155,  20,  20, 255),
        "slot_h":        (200,  30,  30, 255),
        "folder":        (200,  30,  30, 255),
        "folder_h":      (239,  68,  68, 255),
        "glow":          (239,  68,  68,  65),
        "shadow":        (  0,   0,   0,  45),
        "center":        ( 24,   8,   8, 230),
        "center_x":      (220,  50,  50, 245),
        "center_b":      (200,  30,  30, 245),
        "rim":           (255, 160, 110,  55),
        "empty":         (180,  60,  60,  22),
        "card_bg":       (254, 242, 242, 252),
        "card_text":     ( 69,  10,  10, 255),
        "card_shadow":   (  0,   0,   0,  30),
        "bubble_main":      (255,  86,  34, 255),
        "bubble_dark":      (100,   8,  12, 255),
        "bubble_highlight": (255, 210,  66, 220),
        "bubble_glow":      (239,  68,  68,  92),
    },
    "cosmic": {
        "name":          "Space / Cosmic",
        "preview_color": "#6366F1",
        "slot":          ( 55,  45, 160, 255),
        "slot_h":        ( 75,  65, 200, 255),
        "folder":        ( 75,  65, 200, 255),
        "folder_h":      ( 99, 102, 241, 255),
        "glow":          ( 99, 102, 241,  60),
        "shadow":        (  0,   0,   0,  45),
        "center":        ( 10,  10,  30, 230),
        "center_x":      (220,  50,  50, 245),
        "center_b":      ( 75,  65, 200, 245),
        "rim":           (180, 180, 255,  55),
        "empty":         ( 80,  80, 180,  22),
        "card_bg":       (238, 242, 255, 252),
        "card_text":     ( 30,  27,  75, 255),
        "card_shadow":   (  0,   0,   0,  30),
        "bubble_main":      (117,  80, 255, 255),
        "bubble_dark":      ( 15,  20,  70, 255),
        "bubble_highlight": (197, 168, 255, 205),
        "bubble_glow":      ( 99, 102, 241,  84),
    },
}

DEFAULT_THEME = "tiger"
THEME_ORDER   = ["tiger", "purple", "ice", "lava", "cosmic"]
