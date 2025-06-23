from abc import ABC, abstractmethod

class LLMAgent(ABC):
    @abstractmethod
    def one_shot_mode(self, user_input: str, system_info: str) -> str:
        pass
    