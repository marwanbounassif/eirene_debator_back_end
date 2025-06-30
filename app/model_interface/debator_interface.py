from abc import ABC, abstractmethod
from typing import List


class DebatorInterface(ABC):
    @staticmethod
    @abstractmethod
    def format_character_for_prompt(character: dict) -> str:
        pass

    @abstractmethod
    def debate(self, char_description: str, prompt: List[str]) -> str:
        pass

    @abstractmethod
    def create_character_from_description(user_input) -> str:
        pass
