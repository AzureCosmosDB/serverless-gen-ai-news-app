import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch


APP_DIR = Path(__file__).resolve().parents[1] / "chat-functions-app"


class CosmosSetupTests(unittest.TestCase):
    def setUp(self):
        with patch.dict("os.environ", {"cosmos_db_key": "test-key"}):
            spec = importlib.util.spec_from_file_location("cosmos_setup", APP_DIR / "cosmos_client.py")
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)

    def test_normal_startup_gets_existing_containers_without_creating_resources(self):
        client = Mock()
        with patch.object(self.module, "CosmosClient", return_value=client):
            result = self.module.CosmosDBClient()
        client.create_database_if_not_exists.assert_not_called()
        database = client.get_database_client.return_value
        database.create_container_if_not_exists.assert_not_called()
        self.assertIs(result.container, database.get_container_client.return_value)

    def test_explicit_setup_keeps_both_excluded_paths_and_vector_policy(self):
        client = Mock()
        with patch.object(self.module, "CosmosClient", return_value=client):
            self.module.CosmosDBClient(create_resources=True)
        calls = client.create_database_if_not_exists.return_value.create_container_if_not_exists.call_args_list
        self.assertEqual(len(calls), 2)
        for call in calls:
            self.assertEqual(call.kwargs["indexing_policy"]["excludedPaths"],
                             [{"path": '/"_etag"/?'}, {"path": "/vector/*"}])
            self.assertEqual(call.kwargs["vector_embedding_policy"]["vectorEmbeddings"][0]["path"],
                             "/vector")


if __name__ == "__main__":
    unittest.main()
