from openai import OpenAI, APIError, RateLimitError
from typing import List, Dict, Optional, Union
import itertools

from .config import Config

_id_counter = itertools.count(start=1000000)

openai_client = OpenAI(api_key=Config.OpenAI.OPENAI_TOKEN)

def llm_generate(prompt: List[Dict[str, str]]) -> Optional[Union[str, Dict[str, str]]]:
    if Config.OpenAI.OPENAI_ENABLED:
        try:
            completion = openai_client.chat.completions.create(
                model=Config.OpenAI.OPENAI_LLM_MODEL,
                messages=prompt,
            )
            completion_content =  completion.choices[0].message.content
            return completion_content
        except APIError as error:
            print(f"[OpenAI] An error occurred: {error}")
            return None
        except RateLimitError as error:
            print(f"[OpenAI] Rate limit exceeded: {error}")
            return None
    else:
        return None