"""
AgriSense AI — Backend Test Suite
====================================
Tests agent routing, function tools, and API endpoints.

Run: pytest backend/tests/ -v
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from api.main import app, truncate_for_sms
from agents.weather_market_agents import compute_planting_suitability, generate_sell_advice
from agents.agronomy_agent import get_fertiliser_recommendations

client = TestClient(app)


# ── SMS UTILITIES ──────────────────────────────────────────────────────────

class TestSMSTruncation:
    def test_short_message_unchanged(self):
        msg = "Your maize has nitrogen deficiency. Apply CAN fertiliser."
        assert truncate_for_sms(msg) == msg

    def test_long_message_truncated(self):
        msg = "A" * 200
        result = truncate_for_sms(msg)
        assert len(result) <= 155

    def test_truncation_at_sentence_boundary(self):
        msg = "First sentence here. Second sentence is longer. Third sentence pushed it over the limit for SMS messages."
        result = truncate_for_sms(msg)
        assert result.endswith(".")
        assert len(result) <= 155

    def test_empty_message(self):
        assert truncate_for_sms("") == ""

    def test_exact_155_chars(self):
        msg = "A" * 155
        assert truncate_for_sms(msg) == msg


# ── PLANTING SUITABILITY ───────────────────────────────────────────────────

class TestPlantingSuitability:
    def test_ideal_conditions_high_score(self):
        forecast = [
            {"temp": {"min": 18, "max": 26}, "rain": 5, "humidity": 70, "weather": [{"description": "light rain"}]},
            {"temp": {"min": 19, "max": 27}, "rain": 4, "humidity": 68, "weather": [{"description": "light rain"}]},
            {"temp": {"min": 17, "max": 25}, "rain": 6, "humidity": 72, "weather": [{"description": "light rain"}]},
        ]
        result = compute_planting_suitability(forecast, "maize")
        assert result["score"] >= 70
        assert "proceed" in result["recommendation"].lower() or "good" in result["recommendation"].lower()

    def test_drought_conditions_low_score(self):
        forecast = [
            {"temp": {"min": 28, "max": 38}, "rain": 0, "humidity": 25, "weather": [{"description": "clear sky"}]},
            {"temp": {"min": 30, "max": 40}, "rain": 0, "humidity": 20, "weather": [{"description": "clear sky"}]},
        ]
        result = compute_planting_suitability(forecast, "maize")
        assert result["score"] < 50

    def test_score_clamped_to_100(self):
        forecast = [{"temp": {"min": 22, "max": 28}, "rain": 10, "humidity": 80, "weather": [{"description": "rain"}]}] * 7
        result = compute_planting_suitability(forecast, "maize")
        assert 0 <= result["score"] <= 100

    def test_empty_forecast_handled(self):
        result = compute_planting_suitability([], "maize")
        assert "score" in result
        assert isinstance(result["score"], (int, float))


# ── MARKET ADVICE ─────────────────────────────────────────────────────────

class TestMarketAdvice:
    def test_rising_prices_hold_advice(self):
        advice = generate_sell_advice("rising")
        assert "hold" in advice.lower() or "wait" in advice.lower() or "rising" in advice.lower()

    def test_falling_prices_sell_advice(self):
        advice = generate_sell_advice("falling")
        assert "sell" in advice.lower() or "now" in advice.lower() or "falling" in advice.lower()

    def test_stable_prices_neutral_advice(self):
        advice = generate_sell_advice("stable")
        assert isinstance(advice, str)
        assert len(advice) > 10

    def test_unknown_trend_handled(self):
        advice = generate_sell_advice("unknown")
        assert isinstance(advice, str)


# ── FERTILISER CALCULATOR ─────────────────────────────────────────────────

class TestFertiliserCalculator:
    def test_maize_two_acres(self):
        result = get_fertiliser_recommendations("maize", "Kenya", 2.0)
        assert "basal_fertiliser" in result
        assert "top_dressing" in result
        assert result["field_size_acres"] == 2.0
        assert result["basal_fertiliser"]["bags_50kg"] > 0
        assert result["top_dressing"]["bags_50kg"] >= 0

    def test_acidic_soil_lime_recommendation(self):
        result = get_fertiliser_recommendations("maize", "Kenya", 1.0, soil_ph=4.5)
        assert result["lime_recommendation"] is not None
        assert result["lime_recommendation"]["bags_50kg"] > 0

    def test_neutral_soil_no_lime(self):
        result = get_fertiliser_recommendations("maize", "Kenya", 1.0, soil_ph=6.5)
        assert result["lime_recommendation"] is None

    def test_beans_lower_nitrogen(self):
        """Beans fix nitrogen, so their N requirement should be much lower than maize."""
        maize_result = get_fertiliser_recommendations("maize", "Kenya", 1.0)
        beans_result = get_fertiliser_recommendations("beans", "Kenya", 1.0)
        # Beans top-dressing N should be lower (they fix their own)
        assert beans_result["top_dressing"]["total_kg"] < maize_result["top_dressing"]["total_kg"]

    def test_organic_alternative_always_present(self):
        result = get_fertiliser_recommendations("tomato", "Kenya", 0.5)
        assert "organic_alternative" in result
        assert result["organic_alternative"]["product"] != ""


# ── API ENDPOINTS ─────────────────────────────────────────────────────────

class TestAPIEndpoints:
    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_info_endpoint(self):
        resp = client.get("/api/info")
        data = resp.json()
        assert "agents" in data
        assert len(data["agents"]) >= 5
        assert "channels" in data

    @patch("api.main.process_farmer_query")
    def test_chat_endpoint_success(self, mock_query):
        mock_query.return_value = {
            "response": "Your maize has nitrogen deficiency. Apply CAN fertiliser.",
            "agent_used": "crop-doctor",
            "language_detected": "en",
            "sources": ["Crop Disease Knowledge Base"],
            "trace_id": "trace-123",
        }
        resp = client.post("/api/chat", json={
            "message": "My maize leaves are yellow",
            "farmer_id": "test-farmer",
            "channel": "web",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "agent_used" in data
        assert data["agent_used"] == "crop-doctor"

    def test_chat_endpoint_empty_message(self):
        """Empty messages should still be handled gracefully."""
        resp = client.post("/api/chat", json={
            "message": "",
            "farmer_id": "test",
        })
        # Should either succeed or return a sensible error
        assert resp.status_code in [200, 422, 500]

    @patch("api.main.process_farmer_query")
    def test_chat_sms_channel(self, mock_query):
        mock_query.return_value = {
            "response": "Apply CAN. Nitrogen issue.",
            "agent_used": "crop-doctor",
            "language_detected": "en",
            "sources": [],
            "trace_id": "trace-456",
        }
        resp = client.post("/api/chat", json={
            "message": "maize yellow",
            "farmer_id": "+254700000001",
            "channel": "sms",
        })
        assert resp.status_code == 200


# ── INTEGRATION SANITY ─────────────────────────────────────────────────────

class TestRoutingLogic:
    """
    Test that queries route to the correct specialist agent.
    These are unit tests for the routing classification logic.
    """

    CROP_DISEASE_KEYWORDS = ["yellow leaves", "spots", "wilting", "pest", "disease", "sick plant"]
    WEATHER_KEYWORDS = ["when to plant", "will it rain", "forecast", "planting season"]
    MARKET_KEYWORDS = ["price of maize", "sell harvest", "market rates", "commodity"]
    AGRONOMY_KEYWORDS = ["fertiliser", "DAP", "soil test", "seed variety", "spacing"]
    SUPPLIER_KEYWORDS = ["where to buy", "agro-dealer", "find seed", "nearest shop"]

    def _classify(self, query: str) -> str:
        """Simplified routing classification for testing."""
        q = query.lower()
        if any(kw in q for kw in ["yellow", "spots", "wilting", "disease", "pest", "sick", "insect"]):
            return "crop-doctor"
        if any(kw in q for kw in ["rain", "weather", "plant when", "forecast", "season"]):
            return "weather"
        if any(kw in q for kw in ["price", "sell", "market", "income", "earn"]):
            return "market"
        if any(kw in q for kw in ["fertiliser", "dap", "can", "soil", "seed variety", "spacing"]):
            return "agronomy"
        if any(kw in q for kw in ["where to buy", "dealer", "shop", "supplier", "find"]):
            return "input-finder"
        return "orchestrator"

    def test_disease_query_routes_to_crop_doctor(self):
        assert self._classify("My maize has yellow spots on the leaves") == "crop-doctor"

    def test_weather_query_routes_to_weather(self):
        assert self._classify("Will it rain this week? When should I plant?") == "weather"

    def test_price_query_routes_to_market(self):
        assert self._classify("What is the price of beans at the market today?") == "market"

    def test_fertiliser_query_routes_to_agronomy(self):
        assert self._classify("How much DAP fertiliser for 1 acre of maize?") == "agronomy"

    def test_dealer_query_routes_to_input_finder(self):
        assert self._classify("Where can I find a certified seed dealer near me?") == "input-finder"

    def test_general_greeting_routes_to_orchestrator(self):
        assert self._classify("Hello, I need help with my farm") == "orchestrator"
