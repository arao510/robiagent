import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import datetime

# We need to patch scheduler before importing app
import sys
sys.path.insert(0, "..")


class TestAPIEndpoints:
    @pytest.fixture
    def client(self):
        with patch("apscheduler.schedulers.asyncio.AsyncIOScheduler.start"):
            with patch("apscheduler.schedulers.asyncio.AsyncIOScheduler.shutdown"):
                from api.main import app
                return TestClient(app)

    def test_root_returns_status(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "RobiAgent"
        assert data["status"] == "running"

    def test_health_endpoint(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert "status" in response.json()

    @patch("api.main.get_latest_digest")
    def test_latest_digest_returns_digest(self, mock_get, client, sample_digest):
        mock_get.return_value = sample_digest
        response = client.get("/api/digest/latest")
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2024-01-15"
        assert len(data["recommendations"]) == 1
        assert "disclaimer" in data

    @patch("api.main.get_latest_digest")
    def test_latest_digest_404_when_none(self, mock_get, client):
        mock_get.return_value = None
        response = client.get("/api/digest/latest")
        assert response.status_code == 404

    @patch("api.main.get_all_digests")
    def test_history_returns_list(self, mock_get, client, sample_digest):
        mock_get.return_value = [sample_digest]
        response = client.get("/api/digest/history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("api.main.get_performance_records")
    @patch("api.main.update_performance_outcomes")
    def test_performance_endpoint(self, mock_update, mock_get, client):
        mock_get.return_value = []
        response = client.get("/api/performance")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_trigger_run_returns_started(self, client):
        response = client.post("/api/run")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert "triggered_at" in data

    @patch("api.main.get_latest_digest")
    def test_recommendation_has_required_fields(self, mock_get, client, sample_digest):
        mock_get.return_value = sample_digest
        response = client.get("/api/digest/latest")
        rec = response.json()["recommendations"][0]

        required_fields = [
            "ticker", "signal", "entry_low", "entry_high",
            "target_price", "stop_loss", "risk_reward_ratio",
            "confidence", "reasoning", "robinhood_steps"
        ]
        for field in required_fields:
            assert field in rec, f"Missing field: {field}"

    @patch("api.main.get_latest_digest")
    def test_disclaimer_present_in_digest(self, mock_get, client, sample_digest):
        mock_get.return_value = sample_digest
        response = client.get("/api/digest/latest")
        data = response.json()
        assert "disclaimer" in data
        assert len(data["disclaimer"]) > 20
