from pydantic import BaseModel

class PromptRequest(BaseModel):
    prompt: str

class NewsSummaryRequestSchema(BaseModel):
    content: str

class NewsSummaryCustomModelRequestSchema(BaseModel):
    content: str
    llm_model: str