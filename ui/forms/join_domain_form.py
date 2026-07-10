from __future__ import annotations

import subprocess

from PySide6.QtWidgets import QMessageBox

from ui.forms.base_form import BaseForm, show_form_message
from ui.forms.form_registry import register_form


@register_form
class JoinDomainForm(BaseForm):
    """Form: join the computer to a Windows domain."""

    form_id = "join_domain"

    def __init__(self, parent=None) -> None:
        super().__init__("加入網域", parent)

        self._domain   = self._make_field("corp.example.com")
        self._username = self._make_field("administrator")
        self._password = self._make_field(password=True)

        self._fields_layout.addRow("Domain:", self._domain)
        self._fields_layout.addRow("Username:", self._username)
        self._fields_layout.addRow("Password:", self._password)

        self._domain.setFocus()

    # ── BaseForm interface ────────────────────────────────────────────────────

    def _script_name(self) -> str:
        return "join_domain"

    def _validate(self) -> str | None:
        if not self._domain.text().strip():
            return "請輸入網域名稱（Domain）"
        if not self._username.text().strip():
            return "請輸入使用者名稱（Username）"
        if not self._password.text():
            return "請輸入密碼（Password）"
        return None

    def _collect_params(self) -> dict:
        return {
            "Domain":   self._domain.text().strip(),
            "Username": self._username.text().strip(),
            "Password": self._password.text(),
        }

    def _on_success(self, output: str) -> None:
        self._show_status("✓ 成功加入網域！", ok=True)
        self._btn_execute.setEnabled(False)

        reply = show_form_message(
            self,
            "重新開機",
            "已成功將此電腦加入網域。\n\n需要重新開機才能套用變更。\n\n是否立即重新開機？",
            QMessageBox.Icon.Question,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            subprocess.Popen(["shutdown", "/r", "/t", "10"])
            show_form_message(
                self,
                "重新開機",
                "電腦將在 10 秒後重新開機。\n\n請儲存所有未儲存的工作。",
                QMessageBox.Icon.Information,
            )
            self.accept()
        else:
            self._btn_cancel.setText("Close")
