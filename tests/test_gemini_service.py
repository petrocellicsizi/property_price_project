import pytest
from unittest.mock import MagicMock
from core.gemini_service import GeminiEvaluationService
import json

@pytest.fixture
def gemini_mock(mocker):
    mocker.patch("core.gemini_service.os.environ.get", return_value="dummy_key")
    # Ne mockoljuk ki a teljes modult, csak a Clientet
    mock_client = MagicMock()
    mocker.patch("core.gemini_service.genai.Client", return_value=mock_client)
    service = GeminiEvaluationService()
    service.client = mock_client
    return service

def test_evaluate_all_notes(gemini_mock):
    resp_mock = MagicMock()
    resp_mock.text = '{"overall_summary": "ok", "evaluations": {}}'
    gemini_mock.client.models.generate_content.return_value = resp_mock
    res = gemini_mock.evaluate_all_notes({"property": {"notes": "test"}})
    assert "evaluations" in res

def test_generate_simulation_summary(gemini_mock):
    resp_mock = MagicMock()
    resp_mock.text = "Summary test"
    gemini_mock.client.models.generate_content.return_value = resp_mock
    res = gemini_mock.generate_simulation_summary({}, {})
    assert res == "Summary test"

def test_chat_with_assistant(gemini_mock):
    chat_mock = MagicMock()
    chat_mock.send_message.return_value.text = "Hello"
    gemini_mock.client.chats.create.return_value = chat_mock
    res = gemini_mock.chat_with_assistant("Hi", {}, [])
    assert res["text"] == "Hello"

def test_analyze_location(gemini_mock):
    chat_mock = MagicMock()
    chat_mock.send_message.return_value.text = '{"score": 9, "location_analysis": "test", "recommended_growth_pct": 5.0, "category": "test"}'
    gemini_mock.client.chats.create.return_value = chat_mock
    res = gemini_mock.analyze_location("Test cím")
    assert res["score"] == 9
