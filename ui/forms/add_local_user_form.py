from __future__ import annotations

from PySide6.QtWidgets import QCheckBox

from ui.forms.base_form import BaseForm
from ui.forms.form_registry import register_form
from ui.widgets import CHECKBOX_STYLE


@register_form
class AddLocalUserForm(BaseForm):
    """Form: create a new local Windows user account."""

    form_id = "add_local_user"

    def __init__(self, parent=None) -> None:
        super().__init__("加入 Local User", parent)

        self._username   = self._make_field("username")
        self._password   = self._make_field(password=True)
        self._fullname   = self._make_field("Full Name")
        self._is_admin   = QCheckBox("加入 Administrators 群組")
        self._is_admin.setStyleSheet(CHECKBOX_STYLE)

        self._fields_layout.addRow("Username:", self._username)
        self._fields_layout.addRow("Password:", self._password)
        self._fields_layout.addRow("Full Name:", self._fullname)
        self._fields_layout.addRow("", self._is_admin)

        self._username.setFocus()

    # ── BaseForm interface ────────────────────────────────────────────────────

    def _script_name(self) -> str:
        return "add_local_user"

    def _validate(self) -> str | None:
        if not self._username.text().strip():
            return "請輸入使用者名稱（Username）"
        if not self._password.text():
            return "請輸入密碼（Password）"
        return None

    def _collect_params(self) -> dict:
        params: dict = {
            "Username": self._username.text().strip(),
            "Password": self._password.text(),
            "FullName": self._fullname.text().strip(),
        }
        if self._is_admin.isChecked():
            params["AddToAdmins"] = "true"
        return params

    def _on_success(self, output: str) -> None:
        username = self._username.text().strip()
        admin_note = "（已加入 Administrators）" if self._is_admin.isChecked() else ""
        self._show_status(f"✓ 使用者 {username} 建立成功！{admin_note}", ok=True)
        self._fields_widget.setEnabled(False)
        self._btn_execute.setEnabled(False)
        self._btn_cancel.setText("Close")
