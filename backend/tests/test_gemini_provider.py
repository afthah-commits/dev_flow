import pytest
import json
import httpx
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.config import settings
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.service import get_ai_provider


@pytest.mark.asyncio
async def test_gemini_missing_api_key(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(settings, "AI_API_KEY", None)
    provider = GeminiProvider()

    with pytest.raises(HTTPException) as exc_info:
        await provider.chat(
            messages=[{"role": "user", "content": "Hello"}],
            system_prompt="You are DevFlow assistant."
        )
    assert exc_info.value.status_code == 500
    assert "Gemini API key is not configured" in exc_info.value.detail


@pytest.mark.asyncio
async def test_gemini_chat_success(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
    provider = GeminiProvider()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello! I can help you with your project."}]
                },
                "finishReason": "STOP"
            }
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        reply = await provider.chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are DevFlow AI."
        )

        assert reply == "Hello! I can help you with your project."
        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        assert "gemini-1.5-flash" in mock_post.call_args[0][0]
        assert "test-gemini-key" in mock_post.call_args[0][0]
        assert call_kwargs["json"]["contents"][0]["role"] == "user"
        assert call_kwargs["json"]["contents"][0]["parts"][0]["text"] == "Hi"


@pytest.mark.asyncio
async def test_gemini_structured_json_with_codeblock_stripping(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-key")
    provider = GeminiProvider()

    sample_json = {"title": "Implement Auth", "priority": "HIGH"}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    # Gemini sometimes wraps in ```json markdown block
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": f"```json\n{json.dumps(sample_json)}\n```"}]
                },
                "finishReason": "STOP"
            }
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        reply = await provider.chat(
            messages=[{"role": "user", "content": "Create task"}],
            system_prompt="You are DevFlow AI.",
            json_schema={"type": "object", "properties": {"title": {"type": "string"}}}
        )

        parsed = json.loads(reply)
        assert parsed["title"] == "Implement Auth"
        assert parsed["priority"] == "HIGH"


@pytest.mark.asyncio
async def test_gemini_malformed_json_raises(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-key")
    provider = GeminiProvider()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Not a valid JSON object"}]
                },
                "finishReason": "STOP"
            }
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(HTTPException) as exc_info:
            await provider.chat(
                messages=[{"role": "user", "content": "Create task"}],
                system_prompt="You are DevFlow AI.",
                json_schema={"type": "object"}
            )
        assert exc_info.value.status_code == 500
        assert "malformed JSON" in exc_info.value.detail


@pytest.mark.asyncio
async def test_gemini_rate_limit_429(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-key")
    provider = GeminiProvider()

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "RESOURCE_EXHAUSTED"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(HTTPException) as exc_info:
            await provider.chat(
                messages=[{"role": "user", "content": "Hello"}],
                system_prompt="System"
            )
        assert exc_info.value.status_code == 429
        assert "quota exceeded" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_gemini_auth_error_401(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "invalid-key")
    provider = GeminiProvider()

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "API_KEY_INVALID"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(HTTPException) as exc_info:
            await provider.chat(
                messages=[{"role": "user", "content": "Hello"}],
                system_prompt="System"
            )
        assert exc_info.value.status_code == 502
        assert "authentication failed" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_gemini_timeout(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-key")
    provider = GeminiProvider()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Timed out")

        with pytest.raises(HTTPException) as exc_info:
            await provider.chat(
                messages=[{"role": "user", "content": "Hello"}],
                system_prompt="System"
            )
        assert exc_info.value.status_code == 504
        assert "timed out" in exc_info.value.detail.lower()


def test_get_ai_provider_factory(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    provider = get_ai_provider()
    assert isinstance(provider, GeminiProvider)

    monkeypatch.setattr(settings, "AI_PROVIDER", "mock")
    provider_mock = get_ai_provider()
    assert provider_mock.__class__.__name__ == "MockAIProvider"
