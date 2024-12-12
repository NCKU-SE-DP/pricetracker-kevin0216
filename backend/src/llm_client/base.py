import abc
from pydantic import BaseModel, Field
from openai import OpenAI
from enum import Enum

class PromptPassingInterface(BaseModel):
    system_content: str = Field(...)
    user_content: str = Field(...)

    @property
    def to_dict(self):
        value = [
            {"role": "system", "content": f"{self.system_content}"},
            {"role": "user", "content": f"{self.user_content}"},
        ]
        return value

class RelevanceEvaluation(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class LLMClientBase(metaclass=abc.ABCMeta):
    openai_client: OpenAI | None

    @abc.abstractmethod
    def _generate(self, prompt: PromptPassingInterface) -> str:
        """
        Generate the response based on the prompt.
        :param prompt:
        :return:
        """
        return NotImplemented