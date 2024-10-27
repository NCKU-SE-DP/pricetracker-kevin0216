from sqlalchemy.orm import sessionmaker
from openai import OpenAI, APIError, RateLimitError
from typing import List, Dict, Optional, Union
import itertools

from .config import OPENAI_TOKEN, OPENAI_LLM_MODEL, OPENAI_ENABLED
from .database import db_engine

_id_counter = itertools.count(start=1000000)
session = sessionmaker(bind=db_engine)

openai_client = OpenAI(api_key=OPENAI_TOKEN)

def llm_generate(prompt: List[Dict[str, str]]) -> Optional[Union[str, Dict[str, str]]]:
    if OPENAI_ENABLED:
        try:
            completion = openai_client.chat.completions.create(
                model=OPENAI_LLM_MODEL,
                messages=prompt,
            )
            return completion.choices[0].message.content
        except APIError as error:
            print(f"[OpenAI] An error occurred: {error}")
            return None
        except RateLimitError as error:
            print(f"[OpenAI] Rate limit exceeded: {error}")
            return None
    else:
        return None