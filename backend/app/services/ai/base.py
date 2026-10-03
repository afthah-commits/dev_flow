from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class AIProvider(ABC):
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], system_prompt: str, json_schema: Optional[Dict] = None) -> str:
        pass
