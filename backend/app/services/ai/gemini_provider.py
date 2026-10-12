from .base import AIProvider
from typing import List, Dict, Any, Optional
import json
import re
import httpx
from fastapi import HTTPException
from app.core.config import settings

class GeminiProvider(AIProvider):
    """Google Gemini AI Provider for DevFlow.
    
    Uses official Gemini REST API (v1beta) with free-tier models (default: gemini-1.5-flash).
    Conforms to AIProvider base interface.
    Advisory-only: never executes code or performs unapproved mutations.
    Keeps API keys exclusively server-side.
    """

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        json_schema: Optional[Dict] = None
    ) -> str:
        api_key = settings.GEMINI_API_KEY or settings.AI_API_KEY
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="Gemini API key is not configured. Please set GEMINI_API_KEY in the backend environment."
            )

        model = settings.GEMINI_MODEL or "gemini-3.8-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        # 1. Prepare system instruction
        full_system = system_prompt
        if json_schema:
            full_system += f"\n\nIMPORTANT: You must respond strictly in valid JSON matching this schema:\n{json.dumps(json_schema)}"

        system_instruction = {
            "parts": [{"text": full_system}]
        }

        # 2. Prepare contents (alternating user/model turns)
        formatted_contents = self._format_messages(messages)

        # 3. Generation configuration
        generation_config: Dict[str, Any] = {
            "temperature": 0.2 if json_schema else 0.7,
            "maxOutputTokens": 2048,
        }
        if json_schema:
            generation_config["responseMimeType"] = "application/json"

        payload = {
            "contents": formatted_contents,
            "systemInstruction": system_instruction,
            "generationConfig": generation_config,
        }

        # 4. Execute request with strict bounds & error handling
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload
                )
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Gemini AI request timed out. Please try again.")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Gemini connection error: {str(e)}")

        # 5. Handle HTTP status codes
        if res.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="Gemini AI rate limit or quota exceeded. Please wait a moment and try again."
            )
        elif res.status_code in (401, 403):
            raise HTTPException(
                status_code=502,
                detail="Gemini authentication failed. Please verify GEMINI_API_KEY in the backend configuration."
            )
        elif res.status_code == 400:
            err_msg = res.json().get("error", {}).get("message", res.text) if res.headers.get("content-type", "").startswith("application/json") else res.text
            raise HTTPException(
                status_code=400,
                detail=f"Gemini invalid request: {err_msg}"
            )
        elif res.status_code >= 500:
            raise HTTPException(
                status_code=502,
                detail="Gemini service is temporarily unavailable. Please try again later."
            )
        elif res.status_code != 200:
            raise HTTPException(
                status_code=res.status_code,
                detail=f"Gemini API error: {res.text}"
            )

        data = res.json()
        candidates = data.get("candidates", [])
        if not candidates:
            # Check for prompt feedback block
            block_reason = data.get("promptFeedback", {}).get("blockReason")
            if block_reason:
                raise HTTPException(status_code=400, detail=f"Request blocked by safety policy ({block_reason}).")
            raise HTTPException(status_code=500, detail="Gemini returned no response candidates.")

        candidate = candidates[0]
        finish_reason = candidate.get("finishReason")
        if finish_reason == "SAFETY":
            raise HTTPException(status_code=400, detail="AI response blocked by safety filters.")

        content_parts = candidate.get("content", {}).get("parts", [])
        if not content_parts:
            raise HTTPException(status_code=500, detail="Gemini candidate contained no content parts.")

        text = content_parts[0].get("text", "")

        # 6. Sanitize and validate structured response if requested
        if json_schema:
            text = self._clean_json_text(text)
            try:
                json.loads(text)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="AI provider returned malformed JSON response.")

        return text

    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Normalize messages to alternating user and model turns required by Gemini."""
        if not messages:
            return [{"role": "user", "parts": [{"text": "Hello"}]}]

        turns: List[Dict[str, Any]] = []
        for msg in messages:
            role = "model" if msg.get("role") in ("assistant", "model") else "user"
            content = msg.get("content", "").strip()
            if not content:
                continue

            if turns and turns[-1]["role"] == role:
                # Merge consecutive turns of the same role
                turns[-1]["parts"][0]["text"] += f"\n\n{content}"
            else:
                turns.append({"role": role, "parts": [{"text": content}]})

        # Ensure turns start with "user"
        if turns and turns[0]["role"] == "model":
            turns.insert(0, {"role": "user", "parts": [{"text": "Begin context."}]})

        if not turns:
            turns.append({"role": "user", "parts": [{"text": "Hello"}]})

        return turns

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown fences (```json ... ```) from JSON output."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()
