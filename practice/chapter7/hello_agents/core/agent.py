from abc import ABC, abstractmethod
from typing import Optional, List
from .message import Message
from .config import Config
from .llm import HelloAgentsLLM


class Agent(ABC):

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
    ):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.config = config or Config()
        self._history: List[Message] = []

    @abstractmethod
    def run(self, input_text: str, **kwargs) -> str:
        pass

    def add_message(self, message: Message) -> None:
        self._history.append(message)

    def get_history(self) -> List[Message]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()
