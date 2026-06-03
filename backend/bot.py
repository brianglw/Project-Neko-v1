from typing import List, Any, Optional
from ollama import Client
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
import os
import sqlite3

load_dotenv()
PORT = os.getenv('PORT')

#LIMIT VARS
WORD_LIMIT = 120
SUMMARY_WORD_LIMIT=500
MSG_LIMIT=8
SILENCE_TIMEOUT = 3.0
MIC_THRESHOLD = 500

class Message(BaseModel):
    role: str
    content: str

class MessageList(BaseModel):
    memo: list[Message]

class Bot: 
    def __init__(self : "Bot", model : str, assistant_model : str):
        self.model : str = model
        self.assistant_model = assistant_model
        self.client = Client(
            host=PORT,
        )
    def _createtables_(self:"Bot", filename:str, path:str):
        try:
            with sqlite3.connect(f"{path}") as conn: 
                cur = conn.cursor()
                cur.execute(f"create table if not exists {filename}(id integer primary key autoincrement, role text, msg text)")
                conn.commit()
            return {}
        except Exception as e:
            print(f"bot.py _createtables_(): {e}")

    def _cleartable_(self:"Bot",path:str,filename:str):
        try:
            with sqlite3.connect(f"{path}") as conn:
                cur = conn.cursor()
                cur.execute(f"delete from {filename}")
                cur.execute(f"select * from {filename}")
                print(f"fetching files from {filename}", cur.fetchall())
                conn.commit()
                return {}
        except Exception as e:
            print(f"bot.py _cleartable_: {e}")


    def trim_history(self : "Bot", history : MessageList, msg_limit : int = MSG_LIMIT) -> MessageList: # cuts down chat history attribute to recent x messages
        try:
            if len(history.memo) > msg_limit:
                history.memo = history.memo[-(msg_limit):]
            print("Trimmed history", history)
            return history
        except Exception as e:
            print(f"bot.py trim_history: {e}")
    
    def chat(self : "Bot", history : MessageList) -> MessageList:
        try: 
            print("Validating history from API...")
            MessageList.model_validate(history)
            complete_response = "" 
            if (len(history.memo) > MSG_LIMIT):
                history = self.trim_history(history,MSG_LIMIT)
            response = self.client.chat(
                model=self.model,
                messages=history.memo,
                stream=True
            )
            for chunk in response:
                content = chunk['message']['content']
                complete_response += content
                print(content, end='', flush=True)
                
            complete_response = {"role": "assistant", "content": complete_response}
            history.memo.append(complete_response)
            print(history)  
            MessageList.model_validate(history)
            #complete_response = self.removeUnwantedChars(complete_response)
            #self.text_to_speech(complete_response, 'af_bella,af_heart')
            return history
        except ValidationError as err:
            print(f"bot.py chat: {err}")
        except Exception as e:
            print(f"bot.py chat: {e}")
            return None

Base_LLM = Bot( "shoyu_v1", "shoyu_stm")