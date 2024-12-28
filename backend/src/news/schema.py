from typing import Literal

from pydantic import BaseModel

class PromptRequest(BaseModel):
    prompt: str

class NewsSummaryRequestSchema(BaseModel):
    content: str

class NewsSummaryCustomModelRequestSchema(BaseModel):
    content: str
    llm_model: Literal["openai", "anthropic", "claude"]