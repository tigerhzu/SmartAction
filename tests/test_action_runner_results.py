from __future__ import annotations

import unittest
from unittest.mock import patch

from core.action_runner import (
    ACTION_DISPATCHED,
    ACTION_HANDLER_ERROR,
    ACTION_UNSUPPORTED,
    ActionRunner,
)
from core.menu_model import MenuItem


class ActionRunnerResultTests(unittest.TestCase):
    def test_success_means_handler_dispatch_returned(self) -> None:
        class Handler:
            def execute(self, payload: str, context: dict) -> None:
                self.payload = payload

        item = MenuItem("open", "Open", action_type="test", action_payload="payload")
        with patch("core.action_runner.get_action", return_value=Handler):
            result = ActionRunner().run(item, {"source": "test"})

        self.assertEqual(result.status, ACTION_DISPATCHED)
        self.assertTrue(result.success)
        self.assertTrue(result.dispatched)
        self.assertEqual(result.handler, "Handler")
        self.assertIsNone(result.error)

    def test_unsupported_type_is_structured(self) -> None:
        item = MenuItem("missing", "Missing", action_type="not-registered")
        with patch("core.action_runner.get_action", return_value=None), patch(
            "core.action_runner.registered_types", return_value=["url"]
        ):
            result = ActionRunner().run(item)

        self.assertEqual(result.status, ACTION_UNSUPPORTED)
        self.assertFalse(result.success)
        self.assertEqual(result.error.code, "unsupported_action_type")  # type: ignore[union-attr]
        self.assertEqual(result.to_dict()["error"]["details"], {"registered_types": ["url"]})

    def test_handler_exception_is_returned_instead_of_raised(self) -> None:
        class BrokenHandler:
            def execute(self, payload: str, context: dict) -> None:
                raise RuntimeError("dispatch failed")

        item = MenuItem("broken", "Broken", action_type="broken")
        with patch("core.action_runner.get_action", return_value=BrokenHandler):
            result = ActionRunner().run(item)

        self.assertEqual(result.status, ACTION_HANDLER_ERROR)
        self.assertFalse(result.dispatched)
        self.assertEqual(result.handler, "BrokenHandler")
        self.assertEqual(result.error.code, "handler_exception")  # type: ignore[union-attr]
        self.assertEqual(result.error.details, {"exception_type": "RuntimeError"})  # type: ignore[union-attr]


if __name__ == "__main__":
    unittest.main()
