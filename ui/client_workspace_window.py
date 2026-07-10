from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.client_workspace import (
    ClientWorkspaceError,
    ClientWorkspaceStore,
    SMARTACTION_FIREFOX_PROFILE,
    check_firefox_helper,
    ensure_smartaction_firefox_profile,
    get_setup_status,
    install_firefox_helper_extension,
    is_firefox_helper_host_installed,
    list_firefox_profiles,
    launch_client_workspace,
    open_firefox_addons,
    repair_native_host_setup,
)
from core.paths import DOCS_DIR
from ui.window_utils import fit_window_to_screen, handle_fullscreen_shortcut
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
    SIGNAL_GREEN,
    SIGNAL_GREEN_WASH,
    SIGNAL_RED,
    SIGNAL_RED_HOVER,
    SIGNAL_RED_WASH,
    STEEL,
    VOID,
)


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

_BTN_SMALL = f"""
    QPushButton {{
        background: transparent; color: {BONE};
        border: 1px solid {ASH}; border-radius: 3px;
        padding: 0 10px; min-height: 28px; font-size: 12px;
    }}
    QPushButton:hover {{ background: {STEEL}; border-color: {EMBER}; }}
    QPushButton:pressed {{ background: {VOID}; }}
    QPushButton:disabled {{ background: {STEEL}; color: {FOG}; border-color: {ASH}; }}
"""

_BTN_SECONDARY = f"""
    QPushButton {{
        background: transparent; color: {BONE};
        border: 1px solid {ASH}; border-radius: 3px;
        padding: 0 12px; min-height: 36px; font-size: 14px;
    }}
    QPushButton:hover {{ background: {STEEL}; border-color: {EMBER}; }}
    QPushButton:pressed {{ background: {VOID}; }}
    QPushButton:disabled {{ background: {STEEL}; color: {FOG}; border-color: {ASH}; }}
"""

_BTN_DANGER = f"""
    QPushButton {{
        background: {SIGNAL_RED_WASH}; color: {SIGNAL_RED};
        border: 1px solid {SIGNAL_RED}; border-radius: 3px;
        padding: 0 12px; min-height: 36px; font-size: 14px;
    }}
    QPushButton:hover {{ background: rgba(229, 72, 77, 0.20); }}
    QPushButton:disabled {{ color: {FOG}; border-color: {ASH}; background: {STEEL}; }}
"""

_FIELD = f"""
    QLineEdit {{
        color: {BONE}; background: {CHARCOAL};
        border: 1px solid {ASH}; border-radius: 3px;
        min-height: 34px; padding: 0 8px; font-size: 14px;
        selection-background-color: {EMBER}; selection-color: {VOID};
    }}
    QLineEdit:focus {{ border-color: {EMBER}; }}
"""

_COMBO = f"""
    QComboBox {{
        color: {BONE}; background: {CHARCOAL};
        border: 1px solid {ASH}; border-radius: 3px;
        min-height: 34px; padding: 0 8px; font-size: 14px;
        selection-background-color: {EMBER}; selection-color: {VOID};
    }}
    QComboBox:focus {{ border-color: {EMBER}; }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox QAbstractItemView {{
        color: {BONE};
        background: {CHARCOAL};
        border: 1px solid {ASH};
        selection-background-color: {EMBER_WASH};
        selection-color: {EMBER};
        outline: 0;
    }}
"""

_TABLE = f"""
    QTableWidget {{
        color: {BONE};
        background-color: {CHARCOAL};
        border: 1px solid {ASH};
        border-radius: 3px;
        gridline-color: {ASH};
        outline: none;
        selection-background-color: {EMBER_WASH};
        selection-color: {EMBER};
    }}
    QTableWidget::item {{ padding: 6px 8px; color: {BONE}; border: none; }}
    QTableWidget::item:hover {{ background: {STEEL}; }}
    QTableWidget::item:selected {{ background: {EMBER_WASH}; color: {EMBER}; }}
    QTableWidget::item:selected:!active {{ background: {STEEL}; color: {EMBER}; }}
    QTableWidget::item:focus {{ border: 1px solid {EMBER}; color: {EMBER}; }}
    QHeaderView::section {{
        color: {FOG};
        background-color: {VOID};
        border: none;
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


def _caption(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {FOG};")
    return label


def _profile_label(profile) -> str:
    suffix = "  [Default=1]" if getattr(profile, "is_default", False) else ""
    return f"{profile.name}  -  {profile.path}{suffix}"


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


def show_info_message(parent: QWidget, title: str, text: str) -> QMessageBox.StandardButton:
    return _show_message(parent, title, text, QMessageBox.Icon.Information)


def show_warning_message(parent: QWidget, title: str, text: str) -> QMessageBox.StandardButton:
    return _show_message(parent, title, text, QMessageBox.Icon.Warning)


def show_error_message(parent: QWidget, title: str, text: str) -> QMessageBox.StandardButton:
    return _show_message(parent, title, text, QMessageBox.Icon.Critical)


def show_confirm_message(parent: QWidget, title: str, text: str) -> QMessageBox.StandardButton:
    return _show_message(
        parent,
        title,
        text,
        QMessageBox.Icon.Question,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )


def show_helper_setup_message(parent: QWidget, text: str) -> None:
    box = QMessageBox(parent)
    box.setWindowTitle("Client Workspace")
    box.setText(text)
    box.setIcon(QMessageBox.Icon.Critical)
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    setup_btn = box.addButton("Open Helper Setup", QMessageBox.ButtonRole.ActionRole)
    box.addButton("Close", QMessageBox.ButtonRole.RejectRole)
    box.setStyleSheet(_MESSAGE_BOX_STYLE)
    box.exec()
    if box.clickedButton() is setup_btn:
        from ui.help_modal import HelpModal

        dlg = HelpModal(
            parent,
            title="Container Helper Setup",
            markdown_path=DOCS_DIR / "firefox-container-helper.md",
        )
        dlg.exec()


class _ClientDialog(QDialog):
    def __init__(self, client: dict[str, Any] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._client = client or {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("Edit Client" if self._client else "Add Client")
        self.setMinimumWidth(520)
        self.setStyleSheet(f"QDialog {{ background: {VOID}; color: {BONE}; }} QLabel {{ color: {BONE}; }}" + _FIELD + _SCROLLBARS)
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(10)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._name = QLineEdit(self._client.get("name", ""))
        self._container = QLineEdit(self._client.get("containerName", ""))
        self._profile = QComboBox()
        self._profile.setStyleSheet(_COMBO)
        self._container.setPlaceholderText("Reserved for future Firefox Container integration")
        form.addRow(_caption("NAME"), self._name)
        form.addRow(_caption("CONTAINER"), self._container)
        form.addRow(_caption("FIREFOX PROFILE"), self._make_profile_picker())
        root.addLayout(form)

        row = QHBoxLayout()
        row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(_BTN_SECONDARY)
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setStyleSheet(_BTN_PRIMARY)
        save.clicked.connect(self._on_save)
        row.addWidget(cancel)
        row.addWidget(save)
        root.addLayout(row)

    def _on_save(self) -> None:
        if not self._name.text().strip():
            show_warning_message(self, "Client", "Client name is required.")
            self._name.setFocus()
            return
        self.accept()

    def data(self) -> dict[str, Any]:
        return {
            **self._client,
            "name": self._name.text().strip(),
            "containerName": self._container.text().strip(),
            "firefoxProfile": str(self._profile.currentData() or "").strip(),
            "urls": self._client.get("urls", []),
        }

    def _make_profile_picker(self) -> QWidget:
        wrap = QWidget()
        row = QHBoxLayout(wrap)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(self._profile, 1)

        btn_create = QPushButton("Create SmartAction Profile")
        btn_create.setStyleSheet(_BTN_SECONDARY)
        btn_create.setToolTip(f"Create or select Firefox profile: {SMARTACTION_FIREFOX_PROFILE}")
        btn_create.clicked.connect(self._create_smartaction_profile)
        row.addWidget(btn_create)

        self._reload_profiles(self._client.get("firefoxProfile", ""))
        return wrap

    def _reload_profiles(self, selected_name: str = "") -> None:
        self._profile.blockSignals(True)
        self._profile.clear()
        profiles = list_firefox_profiles()
        if not profiles:
            self._profile.addItem("No Firefox profiles found. Create SmartAction-ClientWorkspace.", "")
        else:
            for profile in profiles:
                self._profile.addItem(_profile_label(profile), profile.name)
        selected = selected_name or SMARTACTION_FIREFOX_PROFILE
        idx = self._profile.findData(selected)
        if idx < 0:
            default_idx = next(
                (i for i, profile in enumerate(profiles) if getattr(profile, "is_default", False)),
                0,
            )
            idx = default_idx if profiles else 0
        self._profile.setCurrentIndex(idx)
        self._profile.blockSignals(False)

    def _create_smartaction_profile(self) -> None:
        try:
            profile = ensure_smartaction_firefox_profile()
        except ClientWorkspaceError as exc:
            show_error_message(self, "Firefox Profile", str(exc))
            return
        except Exception as exc:
            show_error_message(self, "Firefox Profile", f"Failed to create Firefox profile:\n{exc}")
            return
        self._reload_profiles(profile.name)
        show_info_message(
            self,
            "Firefox Profile",
            f"Firefox profile is ready:\n{profile.name}\n\n{profile.path}",
        )


class _UrlDialog(QDialog):
    def __init__(self, url_data: dict[str, str] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._url_data = url_data or {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("Edit URL" if self._url_data else "Add URL")
        self.setMinimumWidth(560)
        self.setStyleSheet(f"QDialog {{ background: {VOID}; color: {BONE}; }} QLabel {{ color: {BONE}; }}" + _FIELD + _SCROLLBARS)
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._name = QLineEdit(self._url_data.get("name", ""))
        self._url = QLineEdit(self._url_data.get("url", ""))
        self._url.setPlaceholderText("https://admin.example.com")
        form.addRow(_caption("NAME"), self._name)
        form.addRow(_caption("URL"), self._url)
        root.addLayout(form)

        row = QHBoxLayout()
        row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(_BTN_SECONDARY)
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setStyleSheet(_BTN_PRIMARY)
        save.clicked.connect(self._on_save)
        row.addWidget(cancel)
        row.addWidget(save)
        root.addLayout(row)

    def _on_save(self) -> None:
        if not self._name.text().strip():
            show_warning_message(self, "URL", "URL name is required.")
            self._name.setFocus()
            return
        if not self._url.text().strip():
            show_warning_message(self, "URL", "URL is required.")
            self._url.setFocus()
            return
        self.accept()

    def data(self) -> dict[str, str]:
        return {
            "name": self._name.text().strip(),
            "url": self._url.text().strip(),
        }


class ClientWorkspaceWindow(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = ClientWorkspaceStore()
        self._selected_id: str | None = None
        self._helper_connected: bool | None = None
        self._build_ui()
        self._refresh_clients()

    def _build_ui(self) -> None:
        self.setWindowTitle("Client Workspace")
        fit_window_to_screen(self, (1300, 760), (860, 560), width_ratio=0.94, height_ratio=0.88)
        self.setStyleSheet(f"QDialog {{ background: {VOID}; color: {BONE}; }} QLabel {{ color: {BONE}; }}" + _FIELD + _SCROLLBARS)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(12)

        title = QLabel("Client Workspace")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {BONE};")
        root.addWidget(title)

        body = QHBoxLayout()
        body.setSpacing(14)
        left = QVBoxLayout()
        left.addWidget(_caption("CLIENTS"))
        self._client_list = QListWidget()
        self._client_list.setMinimumWidth(260)
        self._client_list.currentRowChanged.connect(self._on_client_selected)
        self._client_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {ASH}; border-radius: 3px;
                background: {CHARCOAL}; color: {BONE}; padding: 4px;
                outline: none;
            }}
            QListWidget::item {{ padding: 8px; border-radius: 3px; }}
            QListWidget::item:hover {{ background: {STEEL}; color: {EMBER}; }}
            QListWidget::item:selected {{ background: {EMBER_WASH}; color: {EMBER}; }}
            QListWidget::item:focus {{ border: 1px solid {EMBER}; }}
        """)
        left.addWidget(self._client_list, stretch=1)

        self._no_clients_hint = QLabel("尚未建立客戶")
        self._no_clients_hint.setStyleSheet(f"color: {FOG}; font-size: 12px;")
        left.addWidget(self._no_clients_hint)

        client_buttons = QHBoxLayout()
        add_client = QPushButton("Add Client")
        add_client.setStyleSheet(_BTN_PRIMARY)
        add_client.clicked.connect(self._add_client)
        edit_client = QPushButton("Edit")
        edit_client.setStyleSheet(_BTN_SECONDARY)
        edit_client.clicked.connect(self._edit_client)
        delete_client = QPushButton("Delete")
        delete_client.setStyleSheet(_BTN_DANGER)
        delete_client.clicked.connect(self._delete_client)
        self._client_buttons = (edit_client, delete_client)
        client_buttons.addWidget(add_client)
        client_buttons.addWidget(edit_client)
        client_buttons.addWidget(delete_client)
        left.addLayout(client_buttons)
        body.addLayout(left)

        right = QVBoxLayout()
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._name = QLineEdit()
        self._client_id = QLineEdit()
        self._container = QLineEdit()
        self._profile = QLineEdit()
        for field in (self._client_id, self._name, self._container, self._profile):
            field.setReadOnly(True)
        form.addRow(_caption("ID"), self._client_id)
        form.addRow(_caption("NAME"), self._name)
        form.addRow(_caption("CONTAINER"), self._container)
        form.addRow(_caption("FIREFOX PROFILE"), self._profile)
        right.addLayout(form)

        self._container_status = QLabel("")
        self._container_status.setWordWrap(True)
        self._container_status.setStyleSheet(
            f"font-size: 12px; color: {FOG}; background: {CHARCOAL}; "
            f"border: 1px solid {ASH}; border-radius: 3px; padding: 8px;"
        )
        right.addWidget(self._container_status)

        self._setup_status = QLabel("")
        self._setup_status.setWordWrap(True)
        self._setup_status.setStyleSheet(
            f"font-size: 12px; color: {FOG}; background: {CHARCOAL}; "
            f"border: 1px solid {ASH}; border-radius: 3px; padding: 8px;"
        )
        right.addWidget(self._setup_status)

        self._empty_hint = QLabel("No URLs configured for this client.")
        self._empty_hint.setText("尚未新增維運網址")
        self._empty_hint.setStyleSheet(f"color: {FOG}; font-size: 12px;")
        right.addWidget(self._empty_hint)

        self._url_table = QTableWidget(0, 2)
        self._url_table.setHorizontalHeaderLabels(["Name", "URL"])
        self._url_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._url_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._url_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._url_table.verticalHeader().setVisible(False)
        self._url_table.setStyleSheet(_TABLE)
        hdr = self._url_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._url_table.itemSelectionChanged.connect(self._update_buttons)
        right.addWidget(self._url_table, stretch=1)

        url_buttons = QHBoxLayout()
        add_url = QPushButton("Add URL")
        add_url.setStyleSheet(_BTN_SECONDARY)
        add_url.clicked.connect(self._add_url)
        edit_url = QPushButton("Edit URL")
        edit_url.setStyleSheet(_BTN_SECONDARY)
        edit_url.clicked.connect(self._edit_url)
        delete_url = QPushButton("Delete URL")
        delete_url.setStyleSheet(_BTN_DANGER)
        delete_url.clicked.connect(self._delete_url)
        self._url_buttons = (add_url, edit_url, delete_url)
        url_buttons.addWidget(add_url)
        url_buttons.addWidget(edit_url)
        url_buttons.addWidget(delete_url)
        url_buttons.addStretch()
        right.addLayout(url_buttons)

        launch_row = QHBoxLayout()
        self._launch = QPushButton("Launch Workspace")
        self._launch.setMinimumHeight(40)
        self._launch.setStyleSheet(_BTN_PRIMARY + """
            QPushButton {
                font-size: 14px;
                border-radius: 3px;
                padding: 0 22px;
            }
        """)
        self._launch.clicked.connect(self._launch_workspace)
        install_helper = QPushButton("Install Helper Extension")
        install_helper.setStyleSheet(_BTN_SMALL)
        install_helper.setToolTip("Open the Container Helper XPI with the selected Firefox profile.")
        install_helper.clicked.connect(self._install_helper_extension)
        check_helper = QPushButton("Check Helper")
        check_helper.setStyleSheet(_BTN_SMALL)
        check_helper.setToolTip("Check whether the Container Helper Extension is installed and responding.")
        check_helper.clicked.connect(self._check_helper)
        repair_setup = QPushButton("Repair Setup")
        repair_setup.setStyleSheet(_BTN_SMALL)
        repair_setup.setToolTip("Reinstall Native Messaging Host files and registry.")
        repair_setup.clicked.connect(self._repair_setup)
        open_addons = QPushButton("Open Add-ons")
        open_addons.setStyleSheet(_BTN_SMALL)
        open_addons.setToolTip("Open about:addons with the selected Firefox profile.")
        open_addons.clicked.connect(self._open_addons)
        export_btn = QPushButton("Export JSON")
        export_btn.setStyleSheet(_BTN_SMALL)
        export_btn.clicked.connect(self._export_json)
        import_btn = QPushButton("Import JSON")
        import_btn.setStyleSheet(_BTN_SMALL)
        import_btn.clicked.connect(self._import_json)
        close = QPushButton("Close")
        close.setStyleSheet(_BTN_SMALL)
        close.clicked.connect(self.accept)
        launch_row.addWidget(self._launch)
        launch_row.addWidget(install_helper)
        launch_row.addWidget(check_helper)
        launch_row.addWidget(repair_setup)
        launch_row.addWidget(open_addons)
        launch_row.addStretch()
        launch_row.addWidget(export_btn)
        launch_row.addWidget(import_btn)
        launch_row.addWidget(close)
        right.addLayout(launch_row)

        body.addLayout(right, stretch=1)
        root.addLayout(body, stretch=1)

    def keyPressEvent(self, event) -> None:
        if handle_fullscreen_shortcut(self, event):
            return
        super().keyPressEvent(event)

    def _refresh_clients(self) -> None:
        current_id = self._selected_id
        self._client_list.blockSignals(True)
        self._client_list.clear()
        for client in self._store.clients():
            item = QListWidgetItem(client.get("name", "Untitled Client"))
            item.setData(Qt.ItemDataRole.UserRole, client.get("id", ""))
            self._client_list.addItem(item)
        self._client_list.blockSignals(False)
        self._no_clients_hint.setVisible(self._client_list.count() == 0)
        row = 0
        if current_id:
            for idx in range(self._client_list.count()):
                if self._client_list.item(idx).data(Qt.ItemDataRole.UserRole) == current_id:
                    row = idx
                    break
        if self._client_list.count():
            self._client_list.setCurrentRow(row)
        else:
            self._selected_id = None
            self._load_client(None)

    def _current_client(self) -> dict[str, Any] | None:
        return self._store.get(self._selected_id) if self._selected_id else None

    def _on_client_selected(self, row: int) -> None:
        if row < 0:
            self._selected_id = None
            self._helper_connected = None
            self._load_client(None)
            return
        self._selected_id = self._client_list.item(row).data(Qt.ItemDataRole.UserRole)
        self._helper_connected = None
        self._load_client(self._current_client())

    def _load_client(self, client: dict[str, Any] | None) -> None:
        self._client_id.setText(client.get("id", "") if client else "")
        self._name.setText(client.get("name", "") if client else "")
        self._container.setText(client.get("containerName", "") if client else "")
        self._profile.setText(client.get("firefoxProfile", "") if client else "")
        self._url_table.setRowCount(0)
        for url_data in (client.get("urls", []) if client else []):
            row = self._url_table.rowCount()
            self._url_table.insertRow(row)
            self._url_table.setItem(row, 0, QTableWidgetItem(url_data.get("name", "")))
            self._url_table.setItem(row, 1, QTableWidgetItem(url_data.get("url", "")))
        self._empty_hint.setVisible(bool(client and not client.get("urls")))
        self._update_container_status(client)
        self._refresh_setup_status(client)
        self._update_buttons()

    def _update_container_status(self, client: dict[str, Any] | None) -> None:
        if not client:
            self._container_status.setText("Firefox Container 狀態：尚未選擇客戶")
            self._container_status.setStyleSheet(
                f"font-size: 12px; color: {FOG}; background: {CHARCOAL}; "
                f"border: 1px solid {ASH}; border-radius: 3px; padding: 8px;"
            )
            return
        container = str(client.get("containerName", "")).strip()
        if not container:
            self._container_status.setText("Firefox Container 狀態：未設定 Container，使用一般 Firefox 分頁開啟。")
            self._container_status.setStyleSheet(
                f"font-size: 12px; color: {FOG}; background: {CHARCOAL}; "
                f"border: 1px solid {ASH}; border-radius: 3px; padding: 8px;"
            )
            return
        if not is_firefox_helper_host_installed():
            self._container_status.setText(
                "Firefox Container 狀態：已設定 Container，"
                "但 Helper 尚未完整就緒。請確認 Extension 已安裝、Firefox Profile 正確、Native Messaging Host 已註冊。"
            )
            self._container_status.setStyleSheet(
                f"font-size: 12px; color: {SIGNAL_AMBER}; background: {SIGNAL_AMBER_WASH}; "
                f"border: 1px solid {SIGNAL_AMBER}; border-radius: 3px; padding: 8px;"
            )
            return
        self._container_status.setText(
            f"Firefox Container 狀態：已設定 Container「{container}」，將使用 Container Helper Extension 開啟。"
        )
        self._container_status.setStyleSheet(
            f"font-size: 12px; color: {SIGNAL_GREEN}; background: {SIGNAL_GREEN_WASH}; "
            f"border: 1px solid {SIGNAL_GREEN}; border-radius: 3px; padding: 8px;"
        )

    def _refresh_setup_status(self, client: dict[str, Any] | None = None) -> None:
        client = client if client is not None else self._current_client()
        if not client:
            self._setup_status.setText("Setup Status：尚未選擇客戶")
            return
        status = get_setup_status(client, self._helper_connected)

        def yes_no(value: bool | None) -> str:
            if value is None:
                return "Not checked"
            return "OK" if value else "Missing"

        lines = [
            "Setup Status",
            f"Firefox: {yes_no(status['firefox_installed'])}",
            f"Firefox Multi-Account Containers: {yes_no(status['multi_account_containers_installed'])}",
            f"SmartAction Container Helper: {yes_no(status['container_helper_installed'])}",
            f"Native Host: {yes_no(status['native_host_registered'])}",
            f"Helper connected: {yes_no(status['helper_connected'])}",
        ]
        if status.get("profile_name"):
            lines.append(f"Profile: {status['profile_name']}")
        if status.get("xpi_path"):
            lines.append(f"XPI: {status['xpi_path']}")
        self._setup_status.setText("\n".join(lines))

    def _update_buttons(self) -> None:
        has_client = self._current_client() is not None
        has_url = self._url_table.currentRow() >= 0
        for button in self._client_buttons:
            button.setEnabled(has_client)
        self._url_buttons[0].setEnabled(has_client)
        self._url_buttons[1].setEnabled(has_client and has_url)
        self._url_buttons[2].setEnabled(has_client and has_url)
        self._launch.setEnabled(bool(has_client and self._current_client().get("urls")))

    def _name_exists(self, name: str, ignore_id: str | None = None) -> bool:
        folded = name.strip().casefold()
        for client in self._store.clients():
            if ignore_id and client.get("id") == ignore_id:
                continue
            if str(client.get("name", "")).strip().casefold() == folded:
                return True
        return False

    def _add_client(self) -> None:
        dlg = _ClientDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.data()
        if self._name_exists(data.get("name", "")):
            show_warning_message(self, "Client", f'Client name "{data.get("name", "")}" already exists.')
            return
        try:
            client = self._store.add_client(data)
        except ClientWorkspaceError as exc:
            show_warning_message(self, "Client", str(exc))
            return
        self._selected_id = client["id"]
        self._refresh_clients()

    def keyPressEvent(self, event) -> None:
        if handle_fullscreen_shortcut(self, event):
            return
        super().keyPressEvent(event)

    def _edit_client(self) -> None:
        client = self._current_client()
        if not client:
            return
        dlg = _ClientDialog(client, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.data()
        if self._name_exists(data.get("name", ""), ignore_id=client["id"]):
            show_warning_message(self, "Client", f'Client name "{data.get("name", "")}" already exists.')
            return
        try:
            self._store.update_client(client["id"], data)
        except ClientWorkspaceError as exc:
            show_warning_message(self, "Client", str(exc))
            return
        self._refresh_clients()

    def _delete_client(self) -> None:
        client = self._current_client()
        if not client:
            return
        reply = show_confirm_message(
            self,
            "Delete Client",
            f'Delete "{client.get("name", "this client")}"?',
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._store.delete_client(client["id"])
            self._selected_id = None
            self._refresh_clients()

    def _add_url(self) -> None:
        client = self._current_client()
        if not client:
            return
        dlg = _UrlDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        client.setdefault("urls", []).append(dlg.data())
        self._store.update_client(client["id"], client)
        self._load_client(client)

    def _edit_url(self) -> None:
        client = self._current_client()
        row = self._url_table.currentRow()
        if not client or row < 0:
            return
        urls = client.setdefault("urls", [])
        if not (0 <= row < len(urls)):
            return
        dlg = _UrlDialog(urls[row], self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        urls[row] = dlg.data()
        self._store.update_client(client["id"], client)
        self._load_client(client)
        self._url_table.setCurrentCell(row, 0)

    def _delete_url(self) -> None:
        client = self._current_client()
        row = self._url_table.currentRow()
        if not client or row < 0:
            return
        urls = client.setdefault("urls", [])
        if not (0 <= row < len(urls)):
            return
        reply = show_confirm_message(
            self,
            "Delete URL",
            f'Delete "{urls[row].get("name", "this URL")}"?',
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        del urls[row]
        self._store.update_client(client["id"], client)
        self._load_client(client)

    def _install_helper_extension(self) -> None:
        client = self._current_client()
        if not client:
            show_warning_message(self, "Helper Extension", "Please select a client first.")
            return
        try:
            xpi_path = install_firefox_helper_extension(client)
        except ClientWorkspaceError as exc:
            show_helper_setup_message(self, str(exc))
            return
        except Exception as exc:
            show_error_message(self, "Helper Extension", f"Failed to open Helper Extension installer:\n{exc}")
            return
        show_info_message(
            self,
            "Helper Extension",
            "Firefox was opened with the selected profile.\n\n"
            "Install the signed Container Helper XPI when Firefox prompts you.\n\n"
            f"XPI:\n{xpi_path}",
        )
        self._refresh_setup_status(client)

    def _check_helper(self) -> None:
        client = self._current_client()
        if not client:
            show_warning_message(self, "Check Helper", "Please select a client first.")
            return
        try:
            result = check_firefox_helper(client, start_firefox=True)
        except ClientWorkspaceError as exc:
            self._helper_connected = False
            self._refresh_setup_status(client)
            show_helper_setup_message(self, str(exc))
            return
        except Exception as exc:
            self._helper_connected = False
            self._refresh_setup_status(client)
            show_error_message(self, "Check Helper", f"Helper check failed:\n{exc}")
            return
        self._helper_connected = True
        self._refresh_setup_status(client)
        show_info_message(
            self,
            "Check Helper",
            "Container Helper Extension is installed and responding.\n\n"
            f"Add-on ID: {result.get('addonId', '')}\n"
            f"Version: {result.get('version', '')}",
        )

    def _repair_setup(self) -> None:
        try:
            manifest = repair_native_host_setup()
        except ClientWorkspaceError as exc:
            show_error_message(self, "Repair Setup", str(exc))
            return
        except Exception as exc:
            show_error_message(self, "Repair Setup", f"Repair failed:\n{exc}")
            return
        self._helper_connected = None
        self._refresh_setup_status()
        show_info_message(
            self,
            "Repair Setup",
            "Native Messaging Host was repaired.\n\n"
            f"Manifest:\n{manifest}",
        )

    def _open_addons(self) -> None:
        client = self._current_client()
        if not client:
            show_warning_message(self, "Open Add-ons", "Please select a client first.")
            return
        try:
            open_firefox_addons(client)
        except ClientWorkspaceError as exc:
            show_error_message(self, "Open Add-ons", str(exc))
            return
        except Exception as exc:
            show_error_message(self, "Open Add-ons", f"Failed to open about:addons:\n{exc}")
            return

    def _launch_workspace(self) -> None:
        client = self._current_client()
        if not client:
            return
        urls = client.get("urls", [])
        if not urls:
            show_info_message(self, "Client Workspace", "尚未新增維運網址，無法啟動工作區。")
            return
        filled_urls = [u.get("url", "").strip() for u in urls if u.get("url", "").strip()]
        skipped_empty = len(urls) - len(filled_urls)
        if not filled_urls:
            show_info_message(self, "Client Workspace", "All URL fields are empty. Nothing to launch.")
            return
        invalid_scheme = [
            url for url in filled_urls
            if not (url.lower().startswith("http://") or url.lower().startswith("https://"))
        ]
        if invalid_scheme:
            preview = "\n".join(invalid_scheme[:5])
            if len(invalid_scheme) > 5:
                preview += f"\n... and {len(invalid_scheme) - 5} more"
            reply = show_confirm_message(
                self,
                "Confirm URL Format",
                "Some URLs do not start with http:// or https://.\n"
                "Please confirm the format before launching:\n\n"
                f"{preview}\n\n"
                "Continue anyway?",
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        try:
            result = launch_client_workspace(client)
        except ClientWorkspaceError as exc:
            message = str(exc)
            if str(client.get("containerName", "")).strip() and (
                "did not respond" in message
                or "Native Messaging Host" in message
                or "profile" in message.casefold()
            ):
                show_helper_setup_message(self, message)
            else:
                show_error_message(self, "Client Workspace", message)
            return
        except Exception as exc:
            show_error_message(self, "Client Workspace", f"Failed to launch Firefox:\n{exc}")
            return
        message = f"Opened {result.opened_count} URL(s) in Firefox."
        if result.used_container_helper:
            message += f"\nUsed Firefox Container: {result.container_name}"
        if result.skipped_empty_count or skipped_empty:
            message += f"\nSkipped {max(result.skipped_empty_count, skipped_empty)} empty URL field(s)."
        if result.invalid_scheme_urls:
            message += "\nSome URLs did not start with http:// or https://."
        show_info_message(self, "Client Workspace", message)

    def _export_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Client Workspaces",
            "client-workspaces.json",
            "JSON Files (*.json)",
        )
        if not path:
            return
        try:
            self._store.export_json(Path(path))
        except Exception as exc:
            show_error_message(self, "Export JSON", f"Export failed:\n{exc}")
            return
        show_info_message(self, "Export JSON", "Client workspaces exported successfully.")

    def _import_json(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Client Workspaces",
            "",
            "JSON Files (*.json)",
        )
        if not path:
            return
        reply = show_confirm_message(
            self,
            "Import JSON",
            "Importing will replace the current Client Workspace list.\nContinue?",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            backup_path = self._store.import_json(Path(path))
        except json.JSONDecodeError:
            show_error_message(self, "Import JSON", "Invalid JSON file.")
            return
        except ClientWorkspaceError as exc:
            show_error_message(self, "Import JSON", str(exc))
            return
        except Exception as exc:
            show_error_message(self, "Import JSON", f"Import failed:\n{exc}")
            return
        self._selected_id = None
        self._refresh_clients()
        show_info_message(
            self,
            "Import JSON",
            "Client workspaces imported successfully.\n"
            f"Backup created:\n{backup_path}",
        )
