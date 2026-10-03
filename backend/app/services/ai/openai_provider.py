from .base import AIProvider
from typing import List, Dict, Any, Optional
import httpx
from fastapi import HTTPException
from app.core.config import settings

class OpenAIProvider(AIProvider):
    async def chat(self, messages: List[Dict[str, str]], system_prompt: str, json_schema: Optional[Dict] = None) -> str:
        url = settings.AI_BASE_URL or "https://api.openai.com/v1"
        api_key = settings.AI_API_KEY
        if not api_key:
            raise HTTPException(status_code=500, detail="AI API key not configured")
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload_messages = [{"role": "system", "content": system_prompt}] + messages
        
        payload = {
            "model": settings.AI_MODEL or "gpt-3.5-turbo",
            "messages": payload_messages,
        }
        
        if json_schema:
            payload["response_format"] = {"type": "json_object"}
            # OpenAI requires 'json' in the prompt to reliably return json object
            payload_messages[0]["content"] += "\nRespond strictly in JSON matching this schema:\n" + str(json_schema)

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(f"{url}/chat/completions", headers=headers, json=payload)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=f"AI Provider error: {res.text}")
            
            data = res.json()
            return data["choices"][0]["message"]["content"]
