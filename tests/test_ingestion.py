import asyncio
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch


APP_DIR = Path(__file__).resolve().parents[1] / "ingestion-functions-app"


class IngestionTests(unittest.TestCase):
    def setUp(self):
        dependencies = {
            "openai_client": Mock(OpenAIClient=Mock(return_value=Mock())),
            "news_processing": Mock(),
        }
        with patch.dict(sys.modules, dependencies):
            spec = importlib.util.spec_from_file_location("ingestion_app", APP_DIR / "function_app.py")
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)

    def test_fetch_awaits_processing_and_passes_key_outside_url(self):
        response = Mock()
        response.json.return_value = {"articles": [{"url": "https://example.com/news"}]}
        processed = [{"id": "article", "category": "Technology", "vector": [0.1]}]
        with patch.dict("os.environ", {"news_api_key": "test-key"}), \
                patch.object(self.module.requests, "get", return_value=response) as get, \
                patch.object(self.module, "process_news_articles", AsyncMock(return_value=processed)) as process:
            result = asyncio.run(self.module.fetch_news_articles())
        self.assertEqual(result, processed)
        process.assert_awaited_once_with(response.json.return_value["articles"])
        response.raise_for_status.assert_called_once()
        self.assertNotIn("test-key", get.call_args.args[0])
        self.assertEqual(get.call_args.kwargs["headers"]["X-Api-Key"], "test-key")
        self.assertGreater(get.call_args.kwargs["timeout"], 0)

    def test_provider_failure_propagates_to_timer_without_writing(self):
        handler = self.module.main.build().get_user_function()
        output = Mock()
        with patch.object(self.module, "fetch_news_articles",
                          AsyncMock(side_effect=RuntimeError("provider unavailable"))), \
                self.assertLogs(level="ERROR"), self.assertRaises(RuntimeError):
            asyncio.run(handler(Mock(past_due=False), output))
        output.set.assert_not_called()

    def test_ingestion_uses_environment_openai_key(self):
        with patch.dict("os.environ", {"openai_key": "test-openai-key"}):
            spec = importlib.util.spec_from_file_location("ingestion_openai", APP_DIR / "openai_client.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        self.assertEqual(module.OpenAIClient.openai_key, "test-openai-key")


if __name__ == "__main__":
    unittest.main()
