"""Phase-1 AI plan preview and confirmation dialog.

The dialog never executes a plan. It emits an approval signal only after the
locally validated plan has been shown to the user.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.ai_agent.models import PlanModelError, RiskLevel
from core.ai_agent.provider import ProviderError
from core.ai_agent.service import AIAgentService, PlanProposal
from core.ai_agent.validator import PlanValidationError
from ui.style_tokens import (
    ASH,
    BONE,
    BODY_FONT_FAMILY,
    CHARCOAL,
    EMBER,
    EMBER_HOVER,
    EMBER_PRESSED,
    FOG,
    SIGNAL_AMBER,
    SIGNAL_GREEN,
    SIGNAL_RED,
    STEEL,
    VOID,
)
from ui.window_utils import center_window, fit_window_to_screen


class AIAgentWindow(QDialog):
    plan_confirmed = Signal(object)

    def __init__(self, service: AIAgentService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self._proposal: PlanProposal | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("SmartAction AI Agent — Plan Preview")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        fit_window_to_screen(self, (820, 620), (680, 500))
        self.setStyleSheet(
            f"""
            QDialog {{ background: {VOID}; color: {BONE}; font-family: {BODY_FONT_FAMILY}; }}
            QLabel {{ color: {BONE}; }}
            QPlainTextEdit, QTableWidget {{
                background: {CHARCOAL}; color: {BONE}; border: 1px solid {ASH};
                border-radius: 5px; selection-background-color: {EMBER};
            }}
            QHeaderView::section {{
                background: {STEEL}; color: {FOG}; border: none;
                border-right: 1px solid {ASH}; padding: 7px;
            }}
            QPushButton {{
                min-height: 34px; padding: 0 16px; border-radius: 4px;
                border: 1px solid {ASH}; background: {STEEL}; color: {BONE};
            }}
            QPushButton:hover {{ border-color: {EMBER_HOVER}; }}
            QPushButton:pressed {{ background: {EMBER_PRESSED}; }}
            QPushButton:disabled {{ background: {CHARCOAL}; color: {FOG}; border-color: {ASH}; }}
            QPushButton#primaryButton {{
                background: {EMBER}; color: {VOID}; border-color: {EMBER}; font-weight: 700;
            }}
            QPushButton#primaryButton:hover {{ background: {EMBER_HOVER}; }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(12)

        title = QLabel("AI EXECUTION PLAN")
        title.setStyleSheet("font-size: 20px; font-weight: 800;")
        root.addWidget(title)
        intro = QLabel(
            "Phase 1 uses an offline Mock Provider. It can reference saved SmartAction actions only; "
            "approval does not execute the plan."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color: {FOG};")
        root.addWidget(intro)

        prompt_label = QLabel("Request")
        prompt_label.setStyleSheet("font-weight: 700;")
        root.addWidget(prompt_label)
        self._request = QPlainTextEdit()
        self._request.setObjectName("aiRequestInput")
        self._request.setAccessibleName("AI request")
        self._request.setPlaceholderText("Example: 幫我開啟 Porsche 工作環境")
        self._request.setMaximumHeight(92)
        root.addWidget(self._request)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self._generate = QPushButton("Generate plan")
        self._generate.setObjectName("primaryButton")
        self._generate.setAccessibleName("Generate execution plan")
        self._generate.clicked.connect(self._generate_plan)
        action_row.addWidget(self._generate)
        root.addLayout(action_row)

        self._summary = QLabel("No plan generated.")
        self._summary.setWordWrap(True)
        self._summary.setStyleSheet("font-weight: 700;")
        root.addWidget(self._summary)

        self._steps = QTableWidget(0, 4)
        self._steps.setObjectName("aiPlanTable")
        self._steps.setAccessibleName("Execution plan steps")
        self._steps.setHorizontalHeaderLabels(["Step", "Tool", "Saved action ID", "Risk"])
        self._steps.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._steps.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._steps.verticalHeader().setVisible(False)
        header = self._steps.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        root.addWidget(self._steps, stretch=1)

        self._status = QLabel("Every plan requires confirmation.")
        self._status.setObjectName("aiPlanStatus")
        self._status.setAccessibleName("Plan validation status")
        self._status.setWordWrap(True)
        self._status.setStyleSheet(f"color: {FOG};")
        root.addWidget(self._status)

        bottom = QHBoxLayout()
        bottom.addStretch()
        cancel = QPushButton("Close")
        cancel.clicked.connect(self.reject)
        bottom.addWidget(cancel)
        self._confirm = QPushButton("Approve preview")
        self._confirm.setObjectName("primaryButton")
        self._confirm.setAccessibleName("Approve the displayed plan preview")
        self._confirm.setEnabled(False)
        self._confirm.clicked.connect(self._confirm_plan)
        bottom.addWidget(self._confirm)
        root.addLayout(bottom)
        center_window(self)

    def _generate_plan(self) -> None:
        self._proposal = None
        self._confirm.setEnabled(False)
        self._steps.setRowCount(0)
        try:
            proposal = self._service.propose(self._request.toPlainText())
        except (ProviderError, PlanValidationError, PlanModelError) as exc:
            self._summary.setText("Plan rejected")
            self._set_status(str(exc), SIGNAL_RED)
            return

        self._proposal = proposal
        plan = proposal.plan
        self._summary.setText(plan.summary)
        self._steps.setRowCount(len(plan.steps))
        for row, step in enumerate(plan.steps):
            values = (str(row + 1), step.action_type, step.action_id, step.risk_level.value)
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in (0, 3):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._steps.setItem(row, column, item)

        if plan.has_high_risk_step:
            self._confirm.setEnabled(False)
            self._set_status(
                "High-risk step detected. Phase 1 permits preview only and blocks approval/execution.",
                SIGNAL_RED,
            )
        else:
            self._confirm.setEnabled(True)
            notice = " ".join(proposal.validation_notices)
            text = "Plan validated against saved SmartAction resources. Review it before approval."
            if notice:
                text = f"{text} {notice}"
            color = SIGNAL_AMBER if proposal.validation_notices else SIGNAL_GREEN
            self._set_status(text, color)

    def _confirm_plan(self) -> None:
        if self._proposal is None or self._proposal.plan.has_high_risk_step:
            return
        self._confirm.setEnabled(False)
        self.plan_confirmed.emit(self._proposal)
        self._set_status(
            "Preview approved. Phase 1 has no execution adapter, so no action was run.",
            SIGNAL_GREEN,
        )

    def _set_status(self, text: str, color: str) -> None:
        self._status.setText(text)
        self._status.setStyleSheet(f"color: {color};")

    @property
    def confirm_enabled(self) -> bool:
        """Small test seam; the UI remains the source of truth."""
        return self._confirm.isEnabled()
