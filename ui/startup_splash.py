from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QMovie, QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.debug_log import debug_log
from core.paths import BUNDLE_DIR
from ui.style_tokens import ASH, BONE, CHARCOAL, EMBER, EMBER_HOVER, EMBER_PRESSED, FOG, VOID
from ui.window_utils import center_window, fit_window_to_screen


_VIDEO_SIZE = (900, 500)
_VIDEO_MIN_SIZE = (520, 320)


class StartupSplash(QWidget):
    splash_finished = Signal()

    def __init__(self, media_path: Path, duration_seconds: int = 5) -> None:
        super().__init__()
        self._media_path = media_path
        self._duration_ms = max(1, min(int(duration_seconds or 5), 5)) * 1000
        self._finished = False
        self._player = None
        self._audio = None
        self._movie = None
        self._media_widget: QWidget | None = None
        self._source_pixmap: QPixmap | None = None
        self._build_ui()

    def start(self) -> bool:
        suffix = self._media_path.suffix.lower()
        try:
            if suffix == ".mp4":
                ok = self._start_mp4()
            elif suffix == ".gif":
                ok = self._start_gif()
            elif suffix in {".png", ".jpg", ".jpeg"}:
                ok = self._start_image()
            else:
                return False
        except Exception as exc:
            debug_log(f"startup splash failed to initialize: {exc}")
            return False

        if not ok:
            return False
        self._center_on_screen()
        self.show()
        QTimer.singleShot(self._duration_ms, self._finish)
        return True

    def _build_ui(self) -> None:
        self.setWindowTitle("SmartAction")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        fit_window_to_screen(
            self,
            _VIDEO_SIZE,
            _VIDEO_MIN_SIZE,
            width_ratio=0.72,
            height_ratio=0.72,
            allow_maximize=False,
        )
        self.setFixedSize(self.size())
        self.setStyleSheet(f"""
            QWidget {{ background: {VOID}; color: {BONE}; }}
            QLabel#status {{
                color: {EMBER};
                font-size: 13px;
                font-weight: 600;
            }}
            QLabel#host {{
                background: {CHARCOAL};
                border: 1px solid {ASH};
                border-radius: 3px;
            }}
            QPushButton {{
                background: {CHARCOAL};
                color: {BONE};
                border: 1px solid {ASH};
                border-radius: 3px;
                padding: 0 14px;
                min-height: 28px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {EMBER};
                color: {VOID};
                border-color: {EMBER};
            }}
            QPushButton:pressed {{
                background: {EMBER_PRESSED};
                color: {VOID};
                border-color: {EMBER_PRESSED};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 14)
        root.setSpacing(10)

        self._host = QLabel()
        self._host.setObjectName("host")
        self._host.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._host.setMinimumSize(320, 180)
        root.addWidget(self._host, stretch=1)

        self._status = QLabel("Loading SmartAction...")
        self._status.setObjectName("status")
        self._status.setStyleSheet(f"color: {EMBER_HOVER};")
        root.addWidget(self._status, alignment=Qt.AlignmentFlag.AlignLeft)

        self._skip = QPushButton("Skip")
        self._skip.setToolTip("Skip startup splash")
        self._skip.clicked.connect(self._finish)
        root.addWidget(self._skip, alignment=Qt.AlignmentFlag.AlignRight)

    def _start_mp4(self) -> bool:
        if not self._media_path.exists():
            return False
        try:
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
            from PySide6.QtMultimediaWidgets import QVideoWidget
        except Exception as exc:
            debug_log(f"Qt Multimedia unavailable for startup mp4: {exc}")
            return False

        video = QVideoWidget(self)
        video.setStyleSheet(f"background: {CHARCOAL}; border: 1px solid {ASH}; border-radius: 3px;")
        self.layout().replaceWidget(self._host, video)
        self._host.hide()
        self._media_widget = video

        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._audio.setMuted(True)
        self._audio.setVolume(0)
        self._player.setAudioOutput(self._audio)
        self._player.setVideoOutput(video)
        self._player.errorOccurred.connect(self._on_media_error)
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._player.setSource(QUrl.fromLocalFile(str(self._media_path)))
        self._player.play()
        return True

    def _start_gif(self) -> bool:
        if not self._media_path.exists():
            return False
        self._movie = QMovie(str(self._media_path))
        if not self._movie.isValid():
            debug_log(f"startup gif invalid: {self._media_path}")
            return False
        self._movie.setScaledSize(self._host.size())
        self._host.setMovie(self._movie)
        self._movie.start()
        return True

    def _start_image(self) -> bool:
        if not self._media_path.exists():
            return False
        pixmap = QPixmap(str(self._media_path))
        if pixmap.isNull():
            return False
        self._source_pixmap = pixmap
        self._apply_image_pixmap()
        return True

    def _on_media_error(self, *_args) -> None:
        debug_log(f"startup splash media playback failed: {self._media_path}")
        self._finish()

    def _on_media_status(self, status) -> None:
        try:
            from PySide6.QtMultimedia import QMediaPlayer
            if status == QMediaPlayer.MediaStatus.EndOfMedia:
                self._finish()
        except Exception:
            return

    def _center_on_screen(self) -> None:
        center_window(self)

    def _apply_image_pixmap(self) -> None:
        if self._source_pixmap is None:
            return
        host_size = self._host.size()
        if not host_size.isValid() or host_size.width() <= 0 or host_size.height() <= 0:
            host_size = self.size()
        scaled = self._source_pixmap.scaled(
            host_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._host.setPixmap(scaled)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._movie is not None:
            self._movie.setScaledSize(self._host.size())
        self._apply_image_pixmap()

    def closeEvent(self, event) -> None:
        self._finish()
        super().closeEvent(event)

    def _finish(self) -> None:
        if self._finished:
            return
        self._finished = True
        try:
            if self._player is not None:
                self._player.stop()
            if self._movie is not None:
                self._movie.stop()
        except Exception:
            pass
        self.hide()
        self.splash_finished.emit()
        self.close()


def resolve_startup_media(config_path: str | None = None) -> Path | None:
    configured = Path(config_path or "assets/startup/startup.mp4")
    candidates: list[Path] = []

    if configured.is_absolute():
        candidates.append(configured)
    else:
        if getattr(sys, "frozen", False):
            candidates.append(Path(sys.executable).resolve().parent / configured)
        candidates.append(BUNDLE_DIR / configured)

    fallback_names = ["startup.gif", "startup.png", "startup.jpg", "startup.jpeg"]
    for base in list(candidates):
        for name in fallback_names:
            candidates.append(base.parent / name)

    for path in candidates:
        if path.exists() and path.is_file():
            return path
    return None
