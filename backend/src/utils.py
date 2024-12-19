from openai import OpenAI, APIError, RateLimitError
from typing import List, Dict, Optional, Union
import itertools

from .config import Config

_id_counter = itertools.count(start=1000000)