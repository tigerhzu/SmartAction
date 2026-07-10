"""Neon landing-page style launcher for SmartAction."""
from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QTimer, Qt, QUrl
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCloseEvent,
    QDesktopServices,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from core.action_runner import ActionRunner
from core.actions_config import ActionsConfig
from core.debug_log import debug_log
from core.menu_model import MenuItem
from core.paths import BUNDLE_DIR
from core.theme import DEFAULT_THEME
from ui.style_tokens import BONE, FOG, HEADLINE_FONT_FAMILY, VOID

NEON_BG = "#050711"
INK = "#080B16"
PANEL = "#101426"
PANEL_ALT = "#151A31"
LINE = "#263255"
CYAN = "#3DF6FF"
MAGENTA = "#FF3DF2"
LIME = "#B8FF4D"
AMBER = "#FFB547"
PINK = "#FF4B8B"


WINDOW_QSS = f"""
    QWidget {{
        background: {NEON_BG};
        color: {BONE};
        font-family: "Segoe UI Variable", "Segoe UI", "{HEADLINE_FONT_FAMILY}";
    }}
    QLabel {{
        background: transparent;
        color: {BONE};
    }}
    QLabel#eyebrow {{
        color: {CYAN};
        font-size: 11px;
        font-weight: 800;
    }}
    QLabel#title {{
        color: #FFFFFF;
        font-family: "{HEADLINE_FONT_FAMILY}", "Segoe UI";
        font-size: 48px;
        font-weight: 900;
    }}
    QLabel#subtitle {{
        color: #B6BDD7;
        font-size: 14px;
        line-height: 1.35;
    }}
    QLabel#sectionTitle {{
        color: #FFFFFF;
        font-size: 18px;
        font-weight: 800;
    }}
    QLabel#muted {{
        color: #97A0C4;
        font-size: 12px;
    }}
    QLabel#cardTitle {{
        color: #FFFFFF;
        font-size: 14px;
        font-weight: 800;
    }}
    QLabel#metricValue {{
        color: #FFFFFF;
        font-size: 22px;
        font-weight: 900;
    }}
    QLabel#metricLabel {{
        color: #9EA8D2;
        font-size: 11px;
        font-weight: 700;
    }}
    QFrame#topBar {{
        background: rgba(8, 12, 28, 0.78);
        border: 1px solid rgba(61, 246, 255, 0.16);
        border-radius: 8px;
    }}
    QFrame#glassPanel {{
        background: rgba(16, 20, 38, 0.86);
        border: 1px solid rgba(61, 246, 255, 0.18);
        border-radius: 8px;
    }}
    QFrame#showcasePanel {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 rgba(18, 25, 52, 0.95),
            stop:0.55 rgba(20, 15, 45, 0.95),
            stop:1 rgba(8, 20, 38, 0.96));
        border: 1px solid rgba(255, 61, 242, 0.24);
        border-radius: 8px;
    }}
    QFrame#communityCard {{
        background: rgba(18, 23, 42, 0.92);
        border: 1px solid rgba(184, 255, 77, 0.16);
        border-radius: 8px;
    }}
    QFrame#metricCard {{
        background: rgba(255, 255, 255, 0.045);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 7px;
    }}
    QPushButton {{
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 6px;
        color: #EEF4FF;
        font-size: 13px;
        font-weight: 800;
        min-height: 34px;
        padding: 0 14px;
    }}
    QPushButton:hover {{
        background: rgba(61, 246, 255, 0.13);
        border-color: rgba(61, 246, 255, 0.54);
    }}
    QPushButton:pressed {{
        background: rgba(61, 246, 255, 0.22);
    }}
    QPushButton#primaryButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {CYAN}, stop:0.52 {MAGENTA}, stop:1 {AMBER});
        border: none;
        color: #050711;
        min-height: 42px;
    }}
    QPushButton#primaryButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #73FBFF, stop:0.52 #FF72F7, stop:1 #FFD078);
    }}
    QPushButton#downloadButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {LIME}, stop:1 {CYAN});
        border: none;
        color: #07100B;
        min-height: 42px;
    }}
    QPushButton#navButton {{
        min-width: 38px;
        max-width: 38px;
        min-height: 34px;
        padding: 0;
        font-size: 18px;
    }}
"""


SHOWCASES = [
    {
        "kicker": "Featured arena",
        "title": "Radial Command Arena",
        "body": "A fast-launch command wheel styled like a playable loadout: apps, scripts, URLs, forms, and submenus in one hotkey.",
        "accent": CYAN,
        "alt": MAGENTA,
        "stats": ("Hotkey", "Ctrl+Space", "Loadouts", "Multi-action"),
    },
    {
        "kicker": "Script ops",
        "title": "PowerShell Arcade",
        "body": "Collect reusable admin scripts, run them with guardrails, and turn routine support jobs into one-click missions.",
        "accent": MAGENTA,
        "alt": AMBER,
        "stats": ("Library", "Ready", "Runs", "On demand"),
    },
    {
        "kicker": "Team worlds",
        "title": "Client Workspace Hub",
        "body": "Jump between client-specific browser containers and saved workspaces with a launcher surface built for support crews.",
        "accent": LIME,
        "alt": CYAN,
        "stats": ("Profiles", "Isolated", "Helper", "Firefox"),
    },
]


class NeonStageWidget(QWidget):
    """Animated pseudo-3D showcase painted with Qt primitives."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(330, 250)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._phase = 0.0
        self._accent = QColor(CYAN)
        self._alt = QColor(MAGENTA)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def set_palette(self, accent: str, alt: str) -> None:
        self._accent = QColor(accent)
        self._alt = QColor(alt)
        self.update()

    def _tick(self) -> None:
        self._phase = (self._phase + 0.035) % (math.pi * 2.0)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: D401 - Qt override
        del event
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        self._draw_backdrop(p, rect)
        self._draw_grid(p, rect)
        self._draw_prism(p, rect)
        self._draw_orbits(p, rect)
        p.end()

    def _draw_backdrop(self, p: QPainter, rect: QRectF) -> None:
        path = QPainterPath()
        path.addRoundedRect(rect, 8, 8)
        bg = QLinearGradient(rect.topLeft(), rect.bottomRight())
        bg.setColorAt(0.0, QColor(12, 18, 42, 245))
        bg.setColorAt(0.48, QColor(32, 13, 56, 238))
        bg.setColorAt(1.0, QColor(5, 15, 27, 248))
        p.fillPath(path, QBrush(bg))

        glow = QRadialGradient(rect.center(), rect.width() * 0.62)
        glow.setColorAt(0.0, QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 58))
        glow.setColorAt(0.55, QColor(self._alt.red(), self._alt.green(), self._alt.blue(), 25))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillPath(path, QBrush(glow))
        p.setPen(QPen(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 82), 1.2))
        p.drawPath(path)

    def _draw_grid(self, p: QPainter, rect: QRectF) -> None:
        horizon = rect.top() + rect.height() * 0.62
        floor = QRectF(rect.left() + 10, horizon, rect.width() - 20, rect.height() * 0.30)
        p.setPen(QPen(QColor(61, 246, 255, 52), 1))
        for i in range(9):
            t = i / 8
            x = floor.left() + floor.width() * t
            p.drawLine(QPointF(x, floor.bottom()), QPointF(rect.center().x(), horizon))
        for i in range(7):
            y = horizon + (i / 6) ** 1.8 * floor.height()
            p.drawLine(QPointF(floor.left(), y), QPointF(floor.right(), y))

    def _draw_prism(self, p: QPainter, rect: QRectF) -> None:
        cx = rect.center().x()
        cy = rect.top() + rect.height() * 0.47 + math.sin(self._phase) * 7
        scale = min(rect.width(), rect.height()) / 260.0
        tilt = math.sin(self._phase * 0.85) * 12 * scale

        top = QPolygonF([
            QPointF(cx - 70 * scale + tilt, cy - 38 * scale),
            QPointF(cx, cy - 72 * scale),
            QPointF(cx + 74 * scale + tilt, cy - 34 * scale),
            QPointF(cx + 4 * scale, cy + 2 * scale),
        ])
        left = QPolygonF([
            QPointF(cx - 70 * scale + tilt, cy - 38 * scale),
            QPointF(cx + 4 * scale, cy + 2 * scale),
            QPointF(cx + 4 * scale, cy + 88 * scale),
            QPointF(cx - 76 * scale + tilt, cy + 42 * scale),
        ])
        right = QPolygonF([
            QPointF(cx + 4 * scale, cy + 2 * scale),
            QPointF(cx + 74 * scale + tilt, cy - 34 * scale),
            QPointF(cx + 78 * scale + tilt, cy + 44 * scale),
            QPointF(cx + 4 * scale, cy + 88 * scale),
        ])

        shadow = QRadialGradient(QPointF(cx, cy + 96 * scale), 118 * scale)
        shadow.setColorAt(0.0, QColor(0, 0, 0, 120))
        shadow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(shadow))
        p.drawEllipse(QPointF(cx, cy + 98 * scale), 118 * scale, 26 * scale)

        top_grad = QLinearGradient(top.boundingRect().topLeft(), top.boundingRect().bottomRight())
        top_grad.setColorAt(0, QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 220))
        top_grad.setColorAt(1, QColor(255, 255, 255, 34))
        left_grad = QLinearGradient(left.boundingRect().topLeft(), left.boundingRect().bottomRight())
        left_grad.setColorAt(0, QColor(70, 24, 114, 236))
        left_grad.setColorAt(1, QColor(7, 12, 31, 238))
        right_grad = QLinearGradient(right.boundingRect().topLeft(), right.boundingRect().bottomRight())
        right_grad.setColorAt(0, QColor(self._alt.red(), self._alt.green(), self._alt.blue(), 212))
        right_grad.setColorAt(1, QColor(9, 16, 37, 238))

        p.setBrush(QBrush(left_grad))
        p.drawPolygon(left)
        p.setBrush(QBrush(right_grad))
        p.drawPolygon(right)
        p.setBrush(QBrush(top_grad))
        p.drawPolygon(top)

        p.setPen(QPen(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 190), 1.5))
        p.drawPolyline(top + QPolygonF([top[0]]))
        p.setPen(QPen(QColor(255, 255, 255, 64), 1))
        for y in (24, 48, 70):
            yy = cy + y * scale
            p.drawLine(QPointF(cx - 48 * scale + tilt * 0.4, yy), QPointF(cx + 55 * scale + tilt * 0.2, yy - 6 * scale))

    def _draw_orbits(self, p: QPainter, rect: QRectF) -> None:
        cx = rect.center().x()
        cy = rect.top() + rect.height() * 0.46
        p.setBrush(Qt.BrushStyle.NoBrush)
        for i, color in enumerate((self._accent, self._alt, QColor(LIME))):
            width = 118 + i * 32
            height = 34 + i * 9
            offset = math.sin(self._phase + i) * 10
            p.save()
            p.translate(cx, cy + offset)
            p.rotate(-10 + i * 14 + math.sin(self._phase * 0.7 + i) * 8)
            p.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 96 - i * 20), 1.2))
            p.drawEllipse(QRectF(-width / 2, -height / 2, width, height))
            p.restore()

        p.setPen(Qt.PenStyle.NoPen)
        for i in range(10):
            angle = self._phase + i * 0.71
            radius = 88 + (i % 3) * 24
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle * 1.31) * 52
            p.setBrush(QColor(255, 255, 255, 120 if i % 2 else 190))
            p.drawEllipse(QPointF(x, y), 2.0, 2.0)


class MainWindow(QWidget):
    """Gaming-platform inspired landing page for the SmartAction launcher."""

    def __init__(self, config: ActionsConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._runner = ActionRunner()
        self._ring = None
        self._settings_win = None
        self._showcase_index = 0
        self._showcase_title: QLabel | None = None
        self._showcase_kicker: QLabel | None = None
        self._showcase_body: QLabel | None = None
        self._showcase_stat_a: QLabel | None = None
        self._showcase_stat_b: QLabel | None = None
        self._showcase_chip_a: QLabel | None = None
        self._showcase_chip_b: QLabel | None = None
        self._stage: NeonStageWidget | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("SmartAction")
        self.setMinimumSize(980, 740)
        self.resize(1060, 760)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet(WINDOW_QSS)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(14)

        root.addWidget(self._build_top_bar())

        hero = QHBoxLayout()
        hero.setSpacing(18)
        hero.addWidget(self._build_hero_copy(), 5)
        self._stage = NeonStageWidget()
        hero.addWidget(self._stage, 4)
        root.addLayout(hero, 5)

        root.addWidget(self._build_showcase(), 3)
        root.addLayout(self._build_community_grid(), 2)
        root.addWidget(self._build_command_strip())

        self._sync_showcase()

    def _build_top_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("topBar")
        frame.setFixedHeight(62)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 10, 14, 10)
        layout.setSpacing(12)

        brand = QVBoxLayout()
        brand.setSpacing(1)
        name = QLabel("SMARTACTION")
        name.setObjectName("sectionTitle")
        sub = QLabel("Retro-future command platform")
        sub.setObjectName("muted")
        brand.addWidget(name)
        brand.addWidget(sub)
        layout.addLayout(brand)
        layout.addStretch()

        launch = QPushButton("Launch Ring")
        launch.setObjectName("primaryButton")
        launch.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        launch.clicked.connect(self._on_open_ring)
        layout.addWidget(launch)

        settings = QPushButton("Settings")
        settings.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        settings.clicked.connect(self._on_open_settings)
        layout.addWidget(settings)
        return frame

    def _build_hero_copy(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 10, 4, 6)
        layout.setSpacing(14)
        layout.addStretch()

        eyebrow = QLabel("NEON OPS / WINDOWS ACTION LAUNCHER")
        eyebrow.setObjectName("eyebrow")
        layout.addWidget(eyebrow)

        title = QLabel("SmartAction")
        title.setObjectName("title")
        title.setWordWrap(True)
        layout.addWidget(title)

        subtitle = QLabel(
            "A dark arcade-style control deck for launching scripts, apps, "
            "client workspaces, and radial commands at speed."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        subtitle.setMaximumWidth(560)
        layout.addWidget(subtitle)

        ctas = QHBoxLayout()
        ctas.setSpacing(10)
        download = QPushButton("Download Build")
        download.setObjectName("downloadButton")
        download.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        download.clicked.connect(self._on_download_cta)
        ctas.addWidget(download)
        launch = QPushButton("Play the Ring")
        launch.setObjectName("primaryButton")
        launch.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
        launch.clicked.connect(self._on_open_ring)
        ctas.addWidget(launch)
        ctas.addStretch()
        layout.addLayout(ctas)

        metrics = QHBoxLayout()
        metrics.setSpacing(10)
        metrics.addWidget(self._stat_pill("4 launch lanes"))
        metrics.addWidget(self._stat_pill("24 theme frames"))
        metrics.addWidget(self._stat_pill("1 hotkey hub"))
        metrics.addStretch()
        layout.addLayout(metrics)
        layout.addStretch()
        return panel

    def _build_showcase(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("showcasePanel")
        self._add_shadow(frame, QColor(255, 61, 242, 52), blur=30)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(18)

        copy = QVBoxLayout()
        copy.setSpacing(7)
        self._showcase_kicker = QLabel()
        self._showcase_kicker.setObjectName("eyebrow")
        self._showcase_title = QLabel()
        self._showcase_title.setObjectName("sectionTitle")
        self._showcase_body = QLabel()
        self._showcase_body.setObjectName("subtitle")
        self._showcase_body.setWordWrap(True)
        copy.addWidget(self._showcase_kicker)
        copy.addWidget(self._showcase_title)
        copy.addWidget(self._showcase_body)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        self._showcase_chip_a = self._chip("")
        self._showcase_chip_b = self._chip("")
        chips.addWidget(self._showcase_chip_a)
        chips.addWidget(self._showcase_chip_b)
        chips.addStretch()
        copy.addLayout(chips)
        layout.addLayout(copy, 5)

        stats = QHBoxLayout()
        stats.setSpacing(10)
        self._showcase_stat_a = self._metric_card("", "")
        self._showcase_stat_b = self._metric_card("", "")
        stats.addWidget(self._showcase_stat_a)
        stats.addWidget(self._showcase_stat_b)
        layout.addLayout(stats, 3)

        nav = QVBoxLayout()
        nav.setSpacing(8)
        prev_btn = QPushButton("<")
        prev_btn.setObjectName("navButton")
        prev_btn.clicked.connect(lambda: self._move_showcase(-1))
        next_btn = QPushButton(">")
        next_btn.setObjectName("navButton")
        next_btn.clicked.connect(lambda: self._move_showcase(1))
        nav.addWidget(prev_btn)
        nav.addWidget(next_btn)
        layout.addLayout(nav)
        return frame

    def _build_community_grid(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.addWidget(self._community_card("Community Builds", "Share action packs, theme frames, and workflow ideas."))
        layout.addWidget(self._community_card("Squad Workspaces", "Keep client worlds tidy with named profiles and focused URLs."))
        layout.addWidget(self._community_card("Mod-Ready Scripts", "Turn trusted PowerShell routines into replayable launch actions."))
        return layout

    def _build_command_strip(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("glassPanel")
        frame.setFixedHeight(66)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)
        label = QLabel("Quick access")
        label.setObjectName("muted")
        layout.addWidget(label)
        layout.addStretch()

        ps = QPushButton("PowerShell Library")
        ps.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        ps.clicked.connect(self._on_open_powershell_library)
        layout.addWidget(ps)

        workspace = QPushButton("Client Workspace")
        workspace.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        workspace.clicked.connect(self._on_open_client_workspace)
        layout.addWidget(workspace)

        settings = QPushButton("Settings")
        settings.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        settings.clicked.connect(self._on_open_settings)
        layout.addWidget(settings)
        return frame

    def _metric_card(self, value: str, label: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("metricCard")
        frame.setMinimumWidth(126)
        frame.setMinimumHeight(64)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)
        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        value_label.setMinimumHeight(27)
        label_label = QLabel(label)
        label_label.setObjectName("metricLabel")
        label_label.setMinimumHeight(18)
        label_label.setWordWrap(True)
        layout.addWidget(value_label)
        layout.addWidget(label_label)
        frame.setProperty("valueLabel", value_label)
        frame.setProperty("labelLabel", label_label)
        return frame

    def _community_card(self, title: str, body: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("communityCard")
        frame.setMinimumHeight(112)
        self._add_shadow(frame, QColor(61, 246, 255, 28), blur=20)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)
        heading = QLabel(title)
        heading.setObjectName("cardTitle")
        copy = QLabel(body)
        copy.setObjectName("muted")
        copy.setWordWrap(True)
        pulse = QLabel("LIVE")
        pulse.setStyleSheet(f"color: {LIME}; font-size: 11px; font-weight: 900;")
        layout.addWidget(pulse)
        layout.addWidget(heading)
        layout.addWidget(copy)
        layout.addStretch()
        return frame

    def _chip(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: #EAF7FF;
            background: rgba(61, 246, 255, 0.10);
            border: 1px solid rgba(61, 246, 255, 0.26);
            border-radius: 6px;
            padding: 5px 9px;
            font-size: 11px;
            font-weight: 800;
        """)
        return label

    def _stat_pill(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setFixedHeight(34)
        label.setMinimumWidth(126)
        label.setStyleSheet(f"""
            color: #EAF7FF;
            background: rgba(255, 255, 255, 0.055);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 7px;
            padding: 0 12px;
            font-size: 12px;
            font-weight: 900;
        """)
        return label

    def _move_showcase(self, direction: int) -> None:
        self._showcase_index = (self._showcase_index + direction) % len(SHOWCASES)
        self._sync_showcase()

    def _sync_showcase(self) -> None:
        item = SHOWCASES[self._showcase_index]
        if self._showcase_kicker:
            self._showcase_kicker.setText(item["kicker"].upper())
        if self._showcase_title:
            self._showcase_title.setText(item["title"])
        if self._showcase_body:
            self._showcase_body.setText(item["body"])
        if self._showcase_chip_a:
            self._showcase_chip_a.setText(str(item["stats"][0]))
        if self._showcase_chip_b:
            self._showcase_chip_b.setText(str(item["stats"][2]))
        self._set_metric(self._showcase_stat_a, str(item["stats"][1]), str(item["stats"][0]))
        self._set_metric(self._showcase_stat_b, str(item["stats"][3]), str(item["stats"][2]))
        if self._stage:
            self._stage.set_palette(str(item["accent"]), str(item["alt"]))

    def _set_metric(self, frame: QFrame | None, value: str, label: str) -> None:
        if frame is None:
            return
        value_label = frame.property("valueLabel")
        label_label = frame.property("labelLabel")
        if isinstance(value_label, QLabel):
            value_label.setText(value)
        if isinstance(label_label, QLabel):
            label_label.setText(label)

    def _add_shadow(self, widget: QWidget, color: QColor, *, blur: int) -> None:
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setColor(color)
        shadow.setOffset(0, 10)
        widget.setGraphicsEffect(shadow)

    def _on_download_cta(self) -> None:
        release_dir = _first_existing_path(
            BUNDLE_DIR / "dist" / "SmartAction-Release",
            Path.cwd() / "dist" / "SmartAction-Release",
            Path.cwd() / "dist",
        )
        target = release_dir or Path.cwd()
        debug_log(f"download CTA opened: target={target.resolve()}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target.resolve())))

    def _on_open_ring(self) -> None:
        if self._ring is None:
            from ui.ring_ui import RingWindow
            self._ring = RingWindow()
            self._ring.item_activated.connect(self._on_item_activated)
        if self._ring.isVisible():
            self._ring.close_ring()
            return
        items = self._config.load_actions()
        debug_log(
            f"opening ring via dev main window: loaded_actions_count={len(items)} "
            f"raw_actions_count={len(self._config.get_raw_actions())} "
            f"selected_theme_id={DEFAULT_THEME!r} (dev main window default)"
        )
        self._ring.show_at_cursor(items)

    def _on_item_activated(self, item: MenuItem) -> None:
        context = {"parent_widget": self}
        QTimer.singleShot(120, lambda: self._runner.run(item, context))

    def _on_open_settings(self) -> None:
        from ui.settings_window import SettingsWindow
        debug_log(
            f"opening settings via dev main window: config_path={self._config.path.resolve()} "
            f"raw_actions_count={len(self._config.get_raw_actions())} "
            f"selected_theme_id={self._config.get_theme()!r}"
        )
        win = SettingsWindow(self._config, parent=self)
        win.exec()

    def _on_open_powershell_library(self) -> None:
        from ui.powershell_library_window import PowerShellLibraryWindow
        win = PowerShellLibraryWindow(parent=self)
        win.exec()

    def _on_open_client_workspace(self) -> None:
        from ui.client_workspace_window import ClientWorkspaceWindow
        win = ClientWorkspaceWindow(parent=self)
        win.exec()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()


def _first_existing_path(*paths: Path) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None
