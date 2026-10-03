from .base import AIProvider
from typing import List, Dict, Any, Optional
import json

class MockAIProvider(AIProvider):
    async def chat(self, messages: List[Dict[str, str]], system_prompt: str, json_schema: Optional[Dict] = None) -> str:
        last_msg = messages[-1]["content"].lower()
        
        if json_schema:
            if "subtasks" in json_schema.get("properties", {}):
                return json.dumps({
                    "subtasks": [
                        {"title": "Subtask 1", "description": "Auto generated", "priority": "MEDIUM", "labels": ["ai"]},
                        {"title": "Subtask 2", "description": "Auto generated 2", "priority": "LOW", "labels": ["ai"]}
                    ]
                })
            elif "title" in json_schema.get("properties", {}):
                return json.dumps({
                    "title": "Generated Task", "description": "This is a mock description.", "priority": "HIGH", "labels": ["mock"]
                })
        
        if "summary" in last_msg:
            return "This is a mock summary of your project. It looks healthy!"
        if "next" in last_msg:
            return "You should probably work on the overdue tasks first."
        if "readme" in last_msg:
            return "# Mock README\n\nThis is a generated readme."
            
        return "I am a mock AI. I see you said: " + messages[-1]["content"]
