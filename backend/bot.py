from typing import List, Any, Optional
from ollama import Client
from dotenv import load_dotenv
import os

load_dotenv()
PORT = os.getenv('PORT')

class Bot: 
    def __init__(self : "Bot", history: List[dict[str,str]], chatlog: List[dict[str,str]]) -> None: 
        self.history : List[dict[str,str]] = history
        self.chatlog :List[dict[str,str]] = chatlog


class OpenAIConnection:
    def __init__(self : "OpenAIConnection", bot : Bot, model : str, assistant_model : str, temperature : float, max_tokens : int):
        self.bot : Bot = bot
        self.model : str = model
        self.assistant_model = assistant_model
        self.temperature : float = temperature
        self.token_limit : int = max_tokens
        self.client = Client(
            host=PORT,
        )
        self.pipeline: Optional[Any] = None