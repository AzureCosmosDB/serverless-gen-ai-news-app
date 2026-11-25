import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

import azure.functions as func


APP_DIR = Path(__file__).resolve().parents[1] / "chat-functions-app"


class ChatTests(unittest.TestCase):
    def setUp(self):
        self.openai = Mock()
        self.openai.chat_completion.return_value = ("News response", False)
        dependencies = {
            "openai_client": Mock(OpenAIClient=Mock(return_value=self.openai)),
            "cosmos_client": Mock(CosmosDBClient=Mock(return_value=Mock())),
        }
        with patch.dict(sys.modules, dependencies):
            spec = importlib.util.spec_from_file_location("chat_app", APP_DIR / "function_app.py")
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)
        self.handler = self.module.chat_query.build().get_user_function()

    def request(self, body):
        return func.HttpRequest(
            method="POST", url="/api/query", body=body, headers={"Content-Type": "application/json"}
        )

    def test_invalid_inputs_return_json_400_without_calling_openai(self):
        for body in (b"", b"{", b"null", b"[]", b"{}", b'{"message": "  "}',
                     b'{"message": 42}', b'{"message": "news", "chatHistory": {}}'):
            with self.subTest(body=body):
                response = self.handler(self.request(body))
                self.assertIsInstance(response, func.HttpResponse)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.mimetype, "application/json")
                self.assertIn("error", json.loads(response.get_body()))
        self.openai.chat_completion.assert_not_called()

    def test_message_does_not_require_history(self):
        response = self.handler(self.request(b'{"message": "news"}'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.get_body()), {"response": "News response", "cached": False})

    def test_service_failure_returns_json_and_does_not_expose_exception(self):
        self.openai.chat_completion.side_effect = RuntimeError("private-service-detail")
        with self.assertLogs(level="ERROR"):
            response = self.handler(self.request(b'{"message": "news", "chatHistory": []}'))
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", json.loads(response.get_body()))
        self.assertNotIn("private-service-detail", response.get_body().decode())


if __name__ == "__main__":
    unittest.main()
