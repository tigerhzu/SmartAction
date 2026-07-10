from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QLabel,
    QMessageBox, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

from core.scripts.script_runner import ScriptWorker
from ui.widgets import CHECKBOX_STYLE, make_h_separator, make_input_field
from ui.style_tokens import (
    ASH,
    BONE,
    CHARCOAL,
    EMBER,
    EMBER_HOVER,
    EMBER_PRESSED,
    FOG,
    SIGNAL_GREEN,
    SIGNAL_GREEN_WASH,
    SIGNAL_RED,
    SIGNAL_RED_WASH,
    STEEL,
    VOID,
)

_BTN_EXECUTE_STYLE = f"""
    QPushButton {{
        background: {EMBER};
        color: {VOID};
        border: none;
        border-radius: 3px;
        padding: 0 18px;
        min-height: 36px;
        font-size: 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{ background: {EMBER_HOVER}; }}
    QPushButton:pressed {{ background: {EMBER_PRESSED}; }}
    QPushButton:disabled {{ background: {STEEL}; color: {FOG}; }}
"""

_BTN_CANCEL_STYLE = f"""
    QPushButton {{
        background: transparent;
        color: {BONE};
        border: 1px solid {ASH};
        border-radius: 3px;
        padding: 0 18px;
        min-height: 36px;
        font-size: 14px;
    }}
    QPushButton:hover {{ background: {STEEL}; border-color: {EMBER}; }}
    QPushButton:pressed {{ background: {VOID}; }}
    QPushButton:disabled {{ background: {STEEL}; color: {FOG}; border-color: {ASH}; }}
"""

_FORM_MESSAGE_BOX_STYLE = f"""
    QMessageBox {{
        background-color: {VOID};
        color: {BONE};
    }}
    QMessageBox QLabel {{
        background: transparent;
        color: {BONE};
        font-size: 14px;
        selection-background-color: {EMBER};
        selection-color: {VOID};
    }}
    QMessageBox QPushButton {{
        background-color: {CHARCOAL};
        color: {BONE};
        border: 1px solid {ASH};
        border-radius: 3px;
        padding: 6px 14px;
        min-width: 76px;
        min-height: 30px;
        font-size: 14px;
    }}
    QMessageBox QPushButton:hover {{
        background-color: {STEEL};
        border-color: {EMBER};
    }}
    QMessageBox QPushButton:pressed {{
        background-color: {VOID};
    }}
"""


def show_form_message(
    parent: QWidget,
    title: str,
    text: str,
    icon: QMessageBox.Icon,
    buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
    default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
) -> QMessageBox.StandardButton:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setIcon(icon)
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    box.setStandardButtons(buttons)
    box.setDefaultButton(default_button)
    box.setStyleSheet(_FORM_MESSAGE_BOX_STYLE)
    return QMessageBox.StandardButton(box.exec())


class BaseForm(QDialog):
    """Base class for custom multi-field PowerShell forms.

    Subclasses must:
      - Set class attribute ``form_id`` (str)
      - Implement ``_script_name()`` → str
      - Implement ``_collect_params()`` → dict
      - Optionally override ``_validate()`` and ``_on_success()``
    """

    form_id: str

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self.setMinimumWidth(400)
        self.setStyleSheet(
            f"QDialog {{ background: {VOID}; color: {BONE}; }}"
            f"QLabel {{ color: {BONE}; }}"
            f"{CHECKBOX_STYLE}"
        )
        self._worker: ScriptWorker | None = None
        self._build_layout()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        # Fields area — subclass populates self._fields_layout
        self._fields_widget = QWidget()
        self._fields_layout = QFormLayout(self._fields_widget)
        self._fields_layout.setRowWrapPolicy(
            QFormLayout.RowWrapPolicy.WrapAllRows
        )
        self._fields_layout.setVerticalSpacing(10)
        self._fields_layout.setHorizontalSpacing(12)
        self._fields_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(self._fields_widget)

        # Thin progress bar (marquee while script runs)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedHeight(3)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(
            f"QProgressBar {{ border: none; background: {ASH}; border-radius: 1px; }}"
            f"QProgressBar::chunk {{ background: {EMBER}; border-radius: 1px; }}"
        )
        self._progress.setVisible(False)
        root.addWidget(self._progress)

        # Status message label
        self._status = QLabel("")
        self._status.setWordWrap(True)
        self._status.setMinimumHeight(30)
        self._status.setStyleSheet(
            f"font-size: 12px; color: {FOG}; background: {CHARCOAL}; "
            f"border: 1px solid {ASH}; border-radius: 3px; padding: 7px 9px;"
        )
        root.addWidget(self._status)

        root.addWidget(make_h_separator())

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._btn_cancel = QPushButton("Cancel")
        self._btn_cancel.setFixedHeight(36)
        self._btn_cancel.setStyleSheet(_BTN_CANCEL_STYLE)
        self._btn_cancel.clicked.connect(self.reject)

        self._btn_execute = QPushButton("Execute")
        self._btn_execute.setFixedHeight(36)
        self._btn_execute.setStyleSheet(_BTN_EXECUTE_STYLE)
        self._btn_execute.clicked.connect(self._start_execution)
        self._btn_execute.setDefault(True)

        btn_row.addStretch()
        btn_row.addWidget(self._btn_cancel)
        btn_row.addWidget(self._btn_execute)
        root.addLayout(btn_row)

    # ── Helper: field factory ─────────────────────────────────────────────────

    @staticmethod
    def _make_field(placeholder: str = "", *, password: bool = False) -> ...:
        return make_input_field(placeholder, password=password)

    # ── Subclass interface ────────────────────────────────────────────────────

    def _script_name(self) -> str:
        raise NotImplementedError

    def _collect_params(self) -> dict:
        raise NotImplementedError

    def _validate(self) -> str | None:
        """Return an error string on failure, or None if inputs are valid."""
        return None

    def _on_success(self, output: str) -> None:
        self._show_status(output or "完成。", ok=True)
        self._btn_cancel.setText("Close")

    def _on_failure(self, output: str) -> None:
        self._show_status(output or "執行失敗。", ok=False)

    # ── Execution ─────────────────────────────────────────────────────────────

    def _start_execution(self) -> None:
        error = self._validate()
        if error:
            self._show_status(error, ok=False)
            return

        params = self._collect_params()
        self._worker = ScriptWorker(self._script_name(), params, self)
        self._worker.finished.connect(self._on_script_done)
        self._set_running(True)
        self._worker.start()

    def _on_script_done(self, success: bool, output: str) -> None:
        self._set_running(False)
        if success:
            self._on_success(output)
        else:
            self._on_failure(output)

    # ── UI state ──────────────────────────────────────────────────────────────

    def _set_running(self, running: bool) -> None:
        self._fields_widget.setEnabled(not running)
        self._btn_execute.setEnabled(not running)
        self._progress.setVisible(running)
        if running:
            self._show_status("執行中，請稍候…", ok=None)

    def _show_status(self, msg: str, *, ok: bool | None) -> None:
        if ok is True:
            color = SIGNAL_GREEN
            bg = SIGNAL_GREEN_WASH
            border = SIGNAL_GREEN
        elif ok is False:
            color = SIGNAL_RED
            bg = SIGNAL_RED_WASH
            border = SIGNAL_RED
        else:
            color = FOG
            bg = CHARCOAL
            border = ASH
        self._status.setText(msg)
        self._status.setStyleSheet(
            f"font-size: 12px; color: {color}; background: {bg}; "
            f"border: 1px solid {border}; border-radius: 3px; padding: 7px 9px;"
        )

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(3000)
        super().closeEvent(event)
