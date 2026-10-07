import pytest
from unittest.mock import MagicMock
from core.gemini_service import GeminiService

@pytest.fixture
def gemini_mock(mocker):
    mocker.patch("core.gemini_service.genai")
    service = GeminiService()
    service.model = MagicMock()
    service.chat_session = MagicMock()
    return service

def test_evaluate_all_notes(gemini_mock):
    gemini_mock.model.generate_content.return_value.text = '```json\n{"evaluations": {}}\n```'
    res = gemini_mock.evaluate_all_notes({"property": {"notes": "test"}})
    assert "evaluations" in res

def test_generate_simulation_summary(gemini_mock):
    gemini_mock.model.generate_content.return_value.text = "Summary test"
    res = gemini_mock.generate_simulation_summary({}, {})
    assert res == "Summary test"

def test_chat_with_assistant(gemini_mock):
    gemini_mock.chat_session.send_message.return_value.text = '```json\n{"reply": "Hello"}\n```'
    res = gemini_mock.chat_with_assistant("Hi", {}, [])
    assert res["reply"] == "Hello"

def test_analyze_location(gemini_mock):
    gemini_mock.model.generate_content.return_value.text = '```json\n{"score": 9}\n```'
    res = gemini_mock.analyze_location("Test cím")
    assert res["score"] == 9
