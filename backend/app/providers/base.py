from abc import ABC, abstractmethod
from typing import Any

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_response(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system_instruction: str,
    ) -> dict[str, Any]:
        """
        Send messages and tools to the selected LLM provider.

        Returns a normalized response:
        {
            "type": "text",
            "text": "Hello"
        }

        Or:
        {
            "type": "tool_calls",
            "tool_calls": [
                {
                    "id": "call_123",
                    "name": "check_slots",
                    "arguments": {"start_time": None}
                }
            ]
        }
        """
        pass
    
