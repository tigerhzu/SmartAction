from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QHeaderView,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.powershell_library import CATEGORIES, RISK_LEVELS, PowerShellLibrary
from core.powershell_runner import (
    is_user_admin,
    mask_script_preview,
    parameter_summary,
    run_powershell_script,
)
from ui.style_tokens import (
    ASH,
    BONE,
    CHARCOAL,
    EMBER,
    EMBER_HOVER,
    EMBER_PRESSED,
    EMBER_WASH,
    FOG,
    SIGNAL_AMBER,
    SIGNAL_AMBER_WASH,
    SIGNAL_RED,
    SIGNAL_RED_WASH,
    STEEL,
    VOID,
)
from ui.widgets import CHECKBOX_STYLE
from ui.window_utils import fit_window_to_screen, handle_fullscreen_shortcut

_BTN_PRIMARY = f"""
    QPushButton {{
        background: {EMBER}; color: {VOID}; border: none;
        border-radius: 3px; padding: 0 14px;
        min-height: 36px; font-size: 14px; font-weight: 600;
    }}
    QPushButton:hover {{ background: {EMBER_HOVER}; }}
    QPushButton:pressed {{ background: {EMBER_PRESSED}; }}
    QPushButton:disabled {{ background: {STEEL}; color: {FOG}; }}
"""

_BTN_SECONDARY = f"""
    QPushButton {{
        background: transparent; color: {BONE};
        border: 1px solid {ASH}; border-radius: 3px;
        padding: 0 14px; min-height: 36px; font-size: 14px;
    }}
    QPushButton:hover {{ background: {STEEL}; border-color: {EMBER}; }}
    QPushButton:pressed {{ background: {VOID}; }}
    QPushButton:disabled {{ background: {STEEL}; color: {FOG}; border-color: {ASH}; }}
"""

_BTN_DANGER = f"""
    QPushButton {{
        background: {SIGNAL_RED_WASH}; color: {SIGNAL_RED};
        border: 1px solid {SIGNAL_RED}; border-radius: 3px;
        padding: 0 14px; min-height: 36px; font-size: 14px;
    }}
    QPushButton:hover {{ background: rgba(229, 72, 77, 0.20); }}
    QPushButton:pressed {{ background: {VOID}; }}
    QPushButton:disabled {{ background: {STEEL}; color: {FOG}; border-color: {ASH}; }}
"""

_FIELD = f"""
    QLineEdit, QComboBox {{
        color: {BONE}; background: {CHARCOAL};
        border: 1px solid {ASH}; border-radius: 3px;
        min-height: 34px; padding: 0 8px; font-size: 14px;
    }}
    QLineEdit:focus, QComboBox:focus {{ border-color: {EMBER}; }}
    QLineEdit:hover, QComboBox:hover {{ border-color: {STEEL}; }}
    QComboBox:hover {{ border-color: {EMBER}; }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
        background: transparent;
    }}
    QComboBox QAbstractItemView {{
        color: {BONE};
        background: {CHARCOAL};
        border: 1px solid {ASH};
        selection-color: {EMBER};
        selection-background-color: {EMBER_WASH};
        outline: 0;
    }}
    QPlainTextEdit, QTextEdit {{
        color: {BONE}; background: {CHARCOAL};
        border: 1px solid {ASH}; border-radius: 3px;
        padding: 8px; font-size: 14px;
        selection-color: {VOID};
        selection-background-color: {EMBER};
    }}
    QPlainTextEdit:focus, QTextEdit:focus {{
        border-color: {EMBER};
    }}
    {CHECKBOX_STYLE}
"""

_WINDOW_STYLE = f"""
    QDialog {{ background: {VOID}; color: {BONE}; }}
    QLabel {{ color: {BONE}; }}
"""

_TABLE_STYLE = f"""
    QTableWidget {{
        background: {CHARCOAL};
        alternate-background-color: {STEEL};
        color: {BONE};
        border: 1px solid {ASH};
        border-radius: 3px;
        gridline-color: {ASH};
        outline: 0;
        selection-background-color: {EMBER_WASH};
        selection-color: {EMBER};
    }}
    QTableWidget::item {{
        color: {BONE};
        padding: 6px 8px;
        border: none;
    }}
    QTableWidget::item:hover {{
        background: {STEEL};
    }}
    QTableWidget::item:selected {{
        background: {EMBER_WASH};
        color: {EMBER};
    }}
    QTableWidget::item:selected:active {{
        background: {EMBER_WASH};
        color: {EMBER};
    }}
    QTableWidget::item:selected:!active {{
        background: {STEEL};
        color: {EMBER};
    }}
    QTableWidget::item:focus {{
        border: 1px solid {EMBER};
        color: {EMBER};
    }}
    QHeaderView::section {{
        background: {VOID};
        color: {BONE};
        border: none;
        border-right: 1px solid {ASH};
        border-bottom: 1px solid {ASH};
        padding: 7px 8px;
        font-size: 12px;
        font-weight: 600;
    }}
    QTableCornerButton::section {{
        background: {VOID};
        border: none;
    }}
"""

_DETAILS_STYLE = f"""
    QPlainTextEdit {{
        background: {VOID};
        color: {BONE};
        border: 1px solid {ASH};
        border-radius: 3px;
        padding: 10px;
        selection-color: {VOID};
        selection-background-color: {EMBER};
    }}
    QPlainTextEdit:focus {{
        border-color: {EMBER};
    }}
"""

_SCROLLBARS = f"""
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {ASH};
        border-radius: 5px;
        min-height: 28px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {EMBER};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
"""

_MESSAGE_BOX_STYLE = f"""
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


def _show_message(
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
    box.setStyleSheet(_MESSAGE_BOX_STYLE)
    return QMessageBox.StandardButton(box.exec())


def _show_warning(parent: QWidget, title: str, text: str) -> QMessageBox.StandardButton:
    return _show_message(parent, title, text, QMessageBox.Icon.Warning)


def _show_info(parent: QWidget, title: str, text: str) -> QMessageBox.StandardButton:
    return _show_message(parent, title, text, QMessageBox.Icon.Information)


def _show_confirm(parent: QWidget, title: str, text: str) -> QMessageBox.StandardButton:
    return _show_message(
        parent,
        title,
        text,
        QMessageBox.Icon.Question,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )


def _caption(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {FOG};")
    return label


def _summary(text: str, limit: int = 72) -> str:
    clean = " ".join(str(text or "").split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3].rstrip() + "..."


class ScriptEditorDialog(QDialog):
    def __init__(self, script: dict[str, Any] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._script = script or {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("Edit Script" if self._script else "Add Script")
        fit_window_to_screen(self, (640, 680), (560, 500), width_ratio=0.86, height_ratio=0.88)
        self.setStyleSheet(f"QDialog {{ background: {VOID}; color: {BONE}; }} QLabel {{ color: {BONE}; }}" + _FIELD + _SCROLLBARS)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(10)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        self._name = QLineEdit(self._script.get("name", ""))
        self._description = QTextEdit(self._script.get("description", ""))
        self._description.setFixedHeight(72)
        self._category = QComboBox()
        self._category.addItems(CATEGORIES)
        self._category.setCurrentText(self._script.get("category", "Custom"))
        self._need_admin = QCheckBox("Requires administrator")
        self._need_admin.setChecked(bool(self._script.get("need_admin", False)))
        self._risk = QComboBox()
        self._risk.addItems(RISK_LEVELS)
        self._risk.setCurrentText(self._script.get("risk_level", "safe"))
        self._content = QPlainTextEdit(self._script.get("script_content", ""))
        self._content.setMinimumHeight(180)
        self._params = QPlainTextEdit(json.dumps(self._script.get("parameters", []), indent=2))
        self._params.setMinimumHeight(120)
        self._params.setPlaceholderText('[{"name": "Target", "type": "text", "required": true}]')

        form.addRow(_caption("NAME"), self._name)
        form.addRow(_caption("DESCRIPTION"), self._description)
        form.addRow(_caption("CATEGORY"), self._category)
        form.addRow(_caption("ADMIN"), self._need_admin)
        form.addRow(_caption("RISK"), self._risk)
        form.addRow(_caption("SCRIPT"), self._content)
        form.addRow(_caption("PARAMETERS JSON"), self._params)
        root.addLayout(form)

        hint = QLabel('Use placeholders like {{Target}} in script_content. Parameter type can be "text" or "password".')
        hint.setStyleSheet(f"font-size: 12px; color: {FOG};")
        root.addWidget(hint)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(_BTN_SECONDARY)
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setStyleSheet(_BTN_PRIMARY)
        save.clicked.connect(self._on_save)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        root.addLayout(buttons)

    def _on_save(self) -> None:
        if not self._name.text().strip():
            _show_warning(self, "Missing Name", "Script name is required.")
            return
        if not self._content.toPlainText().strip():
            _show_warning(self, "Missing Script", "Script content is required.")
            return
        try:
            params = json.loads(self._params.toPlainText().strip() or "[]")
            if not isinstance(params, list):
                raise ValueError("parameters must be a JSON array")
        except Exception as exc:
            _show_warning(self, "Invalid Parameters", f"Parameters JSON is invalid:\n{exc}")
            return
        self.accept()

    def result_data(self) -> dict[str, Any]:
        return {
            "name": self._name.text().strip(),
            "description": self._description.toPlainText().strip(),
            "category": self._category.currentText(),
            "script_content": self._content.toPlainText().strip(),
            "need_admin": self._need_admin.isChecked(),
            "risk_level": self._risk.currentText(),
            "parameters": json.loads(self._params.toPlainText().strip() or "[]"),
        }


class ParameterDialog(QDialog):
    def __init__(self, script: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._script = script
        self._fields: dict[str, QLineEdit] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle(f"Parameters - {self._script.get('name', '')}")
        self.setStyleSheet(f"QDialog {{ background: {VOID}; }} QLabel {{ color: {BONE}; }}" + _FIELD + _SCROLLBARS)
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        form = QFormLayout()
        for param in self._script.get("parameters", []):
            name = str(param.get("name", ""))
            field = QLineEdit()
            if param.get("type") == "password":
                field.setEchoMode(QLineEdit.EchoMode.Password)
            field.setPlaceholderText("Required" if param.get("required") else "Optional")
            self._fields[name] = field
            form.addRow(_caption(name), field)
        root.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(_BTN_SECONDARY)
        cancel.clicked.connect(self.reject)
        run = QPushButton("Continue")
        run.setStyleSheet(_BTN_PRIMARY)
        run.clicked.connect(self._on_continue)
        buttons.addWidget(cancel)
        buttons.addWidget(run)
        root.addLayout(buttons)

    def _on_continue(self) -> None:
        for param in self._script.get("parameters", []):
            name = str(param.get("name", ""))
            if param.get("required") and not self._fields[name].text().strip():
                _show_warning(self, "Missing Parameter", f"{name} is required.")
                return
        self.accept()

    def values(self) -> dict[str, str]:
        return {name: field.text() for name, field in self._fields.items()}


class ConfirmRunDialog(QDialog):
    def __init__(self, script: dict[str, Any], values: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._script = script
        self._values = values
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("Confirm Dangerous Script")
        fit_window_to_screen(self, (620, 520), (520, 420), width_ratio=0.82, height_ratio=0.82)
        self.setStyleSheet(f"QDialog {{ background: {VOID}; }} QLabel {{ color: {BONE}; }}" + _FIELD + _SCROLLBARS)
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(10)

        summary = QLabel(
            f"<b>{self._script.get('name')}</b><br>"
            f"{self._script.get('description', '')}<br><br>"
            f"Category: {self._script.get('category')}<br>"
            f"Need admin: {self._script.get('need_admin')}<br>"
            f"Risk level: <b>{self._script.get('risk_level')}</b>"
        )
        summary.setWordWrap(True)
        root.addWidget(summary)

        params = QPlainTextEdit(parameter_summary(self._values, self._script.get("parameters", [])))
        params.setReadOnly(True)
        params.setFixedHeight(90)
        root.addWidget(_caption("PARAMETERS"))
        root.addWidget(params)

        preview = QPlainTextEdit(mask_script_preview(
            self._script.get("script_content", ""),
            self._values,
            self._script.get("parameters", []),
        ))
        preview.setReadOnly(True)
        root.addWidget(_caption("SCRIPT PREVIEW"))
        root.addWidget(preview, stretch=1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(_BTN_SECONDARY)
        cancel.clicked.connect(self.reject)
        run = QPushButton("Run Script")
        run.setStyleSheet(_BTN_DANGER)
        run.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(run)
        root.addLayout(buttons)


class ResultDialog(QDialog):
    def __init__(self, script_name: str, result, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._script_name = script_name
        self._result = result
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle(f"PowerShell Result - {self._script_name}")
        fit_window_to_screen(self, (760, 620), (620, 460), width_ratio=0.86, height_ratio=0.84)
        self.setStyleSheet(f"QDialog {{ background: {VOID}; }} QLabel {{ color: {BONE}; }}" + _FIELD + _SCROLLBARS)
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        status = "success" if self._result.success else "failed"
        header = QLabel(
            f"<b>Status:</b> {status}<br>"
            f"<b>Exit code:</b> {self._result.exit_code}<br>"
            f"<b>Duration:</b> {self._result.duration_seconds:.2f}s"
        )
        root.addWidget(header)
        if self._result.friendly_error:
            friendly = QLabel(self._result.friendly_error)
            friendly.setWordWrap(True)
            friendly.setStyleSheet(
                f"color: {SIGNAL_AMBER}; background: {SIGNAL_AMBER_WASH}; "
                f"border: 1px solid {SIGNAL_AMBER}; border-radius: 3px; padding: 8px;"
            )
            root.addWidget(friendly)
        output = QPlainTextEdit(
            f"STDOUT\n------\n{self._result.stdout or '(empty)'}\n\n"
            f"STDERR\n------\n{self._result.stderr or '(empty)'}"
        )
        output.setReadOnly(True)
        root.addWidget(output, stretch=1)
        buttons = QHBoxLayout()
        buttons.addStretch()
        close = QPushButton("Close")
        close.setStyleSheet(_BTN_PRIMARY)
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        root.addLayout(buttons)


class PowerShellLibraryWindow(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._library = PowerShellLibrary()
        self._selected_id: str | None = None
        self._build_ui()
        self._refresh()
        if self._library.recovery_message:
            _show_warning(self, "PowerShell Library Recovered", self._library.recovery_message)

    def _build_ui(self) -> None:
        self.setWindowTitle("PowerShell Library")
        fit_window_to_screen(self, (1120, 760), (820, 560))
        self.setStyleSheet(_WINDOW_STYLE + _FIELD + _SCROLLBARS)
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("PowerShell Library")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {BONE};")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QLabel("Category:"))
        self._category_filter = QComboBox()
        self._category_filter.addItems(["All"] + CATEGORIES)
        self._category_filter.currentTextChanged.connect(self._refresh)
        header.addWidget(self._category_filter)
        root.addLayout(header)

        body = QHBoxLayout()
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Name", "Category", "Risk", "Admin", "Description"])
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(_TABLE_STYLE)
        self._table.verticalHeader().setVisible(False)
        header_view = self._table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._table.itemSelectionChanged.connect(self._on_selected)
        body.addWidget(self._table, stretch=3)

        details_box = QVBoxLayout()
        self._details = QPlainTextEdit()
        self._details.setReadOnly(True)
        self._details.setStyleSheet(_DETAILS_STYLE)
        details_box.addWidget(_caption("DETAILS"))
        details_box.addWidget(self._details, stretch=1)
        body.addLayout(details_box, stretch=2)
        root.addLayout(body, stretch=1)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background: {ASH};")
        root.addWidget(line)

        buttons = QHBoxLayout()
        self._btn_add = QPushButton("Add")
        self._btn_add.setStyleSheet(_BTN_PRIMARY)
        self._btn_add.clicked.connect(self._add)
        self._btn_edit = QPushButton("Edit")
        self._btn_edit.setStyleSheet(_BTN_SECONDARY)
        self._btn_edit.clicked.connect(self._edit)
        self._btn_delete = QPushButton("Delete")
        self._btn_delete.setStyleSheet(_BTN_DANGER)
        self._btn_delete.clicked.connect(self._delete)
        self._btn_run = QPushButton("Run Script")
        self._btn_run.setStyleSheet(_BTN_PRIMARY)
        self._btn_run.clicked.connect(self._run)
        close = QPushButton("Close")
        close.setStyleSheet(_BTN_SECONDARY)
        close.clicked.connect(self.accept)
        for btn in (self._btn_add, self._btn_edit, self._btn_delete, self._btn_run):
            buttons.addWidget(btn)
        buttons.addStretch()
        buttons.addWidget(close)
        root.addLayout(buttons)
        self._update_buttons()

    def keyPressEvent(self, event) -> None:
        if handle_fullscreen_shortcut(self, event):
            return
        super().keyPressEvent(event)

    def _refresh(self) -> None:
        category = self._category_filter.currentText() if hasattr(self, "_category_filter") else "All"
        scripts = self._library.scripts(category)
        self._table.setRowCount(0)
        for script in scripts:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(script["name"]))
            self._table.setItem(row, 1, QTableWidgetItem(script["category"]))
            self._table.setItem(row, 2, QTableWidgetItem(script["risk_level"]))
            self._table.setItem(row, 3, QTableWidgetItem("Yes" if script["need_admin"] else "No"))
            self._table.setItem(row, 4, QTableWidgetItem(_summary(script["description"])))
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, script["id"])
        self._selected_id = None
        if scripts:
            self._set_details_message("Select a script to view details.")
        else:
            self._set_details_message("No scripts in this category.")
        self._update_buttons()

    def _on_selected(self) -> None:
        items = self._table.selectedItems()
        if not items:
            self._selected_id = None
            self._set_details_message("Select a script to view details.")
            self._update_buttons()
            return
        row = items[0].row()
        self._selected_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        script = self._current_script()
        if script:
            params = json.dumps(script.get("parameters", []), indent=2)
            self._details.setPlainText(
                f"Name: {script['name']}\n"
                f"Description: {script['description']}\n"
                f"Category: {script['category']}\n"
                f"Need admin: {script['need_admin']}\n"
                f"Risk level: {script['risk_level']}\n\n"
                f"Parameters:\n{params}\n\n"
                f"Script:\n{script['script_content']}"
            )
        self._update_buttons()

    def _set_details_message(self, message: str) -> None:
        self._details.setPlainText(message)

    def _current_script(self) -> dict[str, Any] | None:
        return self._library.get(self._selected_id) if self._selected_id else None

    def _update_buttons(self) -> None:
        has_selection = bool(self._selected_id)
        for btn in (getattr(self, "_btn_edit", None), getattr(self, "_btn_delete", None), getattr(self, "_btn_run", None)):
            if btn:
                btn.setEnabled(has_selection)

    def _add(self) -> None:
        dlg = ScriptEditorDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._library.add(dlg.result_data())
            self._refresh()

    def _edit(self) -> None:
        script = self._current_script()
        if not script:
            return
        dlg = ScriptEditorDialog(script, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._library.update(script["id"], dlg.result_data())
            self._refresh()

    def _delete(self) -> None:
        script = self._current_script()
        if not script:
            return
        reply = _show_confirm(self, "Delete Script", f'Delete "{script["name"]}"?')
        if reply == QMessageBox.StandardButton.Yes:
            self._library.delete(script["id"])
            self._refresh()

    def _collect_parameters(self, script: dict[str, Any]) -> dict[str, str] | None:
        if not script.get("parameters"):
            return {}
        dlg = ParameterDialog(script, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None
        return dlg.values()

    def _run(self) -> None:
        script = self._current_script()
        if not script:
            return
        values = self._collect_parameters(script)
        if values is None:
            return
        if script.get("risk_level") == "dangerous":
            confirm = ConfirmRunDialog(script, values, self)
            if confirm.exec() != QDialog.DialogCode.Accepted:
                return
        elif script.get("need_admin") and not is_user_admin():
            _show_info(
                self,
                "Administrator Recommended",
                "This script may require administrator privileges. If it fails, run SmartAction as administrator.",
            )
        result = run_powershell_script(script["script_content"], values, script.get("parameters", []))
        ResultDialog(script["name"], result, self).exec()
