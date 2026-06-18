from datetime import datetime, timezone
from ollama import Client
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import HTTPException
import json
import os
import time
import uuid

load_dotenv()
OLLAMA_HOST = os.getenv('OLLAMA_HOST') or os.getenv('PORT') or 'http://localhost:11434'

#LIMIT VARS
WORD_LIMIT = 120
SUMMARY_WORD_LIMIT=500
MSG_LIMIT=8
SILENCE_TIMEOUT = 3.0
MIC_THRESHOLD = 500

class Part(BaseModel):
    type: str
    text: str

class Author(BaseModel):
    id: str
    displayName: str
    avatarUrl: str
    isOnline: bool
    role: str

class Message(BaseModel):
    id: str
    conversationId: str
    role: str
    status: str = "sent"
    createdAt: str
    author: Author
    parts: list[Part]

class MessageList(BaseModel):
    memo: list[Message]

#region agent log
def _agent_log(hypothesis_id: str, location: str, message: str, data: dict):
    with open("C:/Python/project_nekomimi/debug-9db512.log", "a", encoding="utf-8") as file:
        file.write(json.dumps({"sessionId": "9db512", "runId": "initial", "hypothesisId": hypothesis_id, "location": location, "message": message, "data": data, "timestamp": int(time.time() * 1000)}) + "\n")
#endregion

class Bot: 
    def __init__(self : "Bot", model : str, assistant_model : str):
        self.model : str = model
        self.assistant_model = assistant_model
        self.client = Client(
            host=OLLAMA_HOST,
        )

    def trim_history(self : "Bot", history : MessageList, msg_limit : int = MSG_LIMIT) -> MessageList: # cuts down chat history attribute to recent x messages
        try:
            if len(history.memo) > msg_limit:
                history = MessageList(memo=history.memo[-(msg_limit):])
            print("Trimmed history")
            return history
        except Exception as e:
            print(f"bot.py trim_history: {e}")
            raise HTTPException(status_code=500, detail="History trimming failed")

    def format_ollama_messages(self : "Bot", history : MessageList) -> list[dict[str, str]]:
        messages = []
        for msg in history.memo:
            text_part = next((part for part in msg.parts if part.type == "text"), None)
            if text_part is not None and text_part.text.strip():
                messages.append({"role": msg.role, "content": text_part.text})
        return messages
    
    def chat(self : "Bot", history : MessageList) -> MessageList:
        try: 
            MessageList.model_validate(history)
            complete_response = "" 
            if (len(history.memo) > 0):
                if (len(history.memo) > MSG_LIMIT):
                    history = self.trim_history(history,MSG_LIMIT)

                ollama_messages = self.format_ollama_messages(history)
                #region agent log
                _agent_log("H3,H4", "backend/bot.py:91", "prepared ollama request", {"host": OLLAMA_HOST, "model": self.model, "formattedType": type(ollama_messages).__name__, "messageCount": len(ollama_messages), "roles": [msg.get("role") for msg in ollama_messages]})
                #endregion
                if not ollama_messages:
                    raise HTTPException(status_code=400, detail="No text message to send")

                response = self.client.chat(
                    model=self.model,
                    messages=ollama_messages,
                    stream=True
                )
                print("Shoyu: ")
                for chunk in response:
                    #region agent log
                    _agent_log("H5", "backend/bot.py:102", "received ollama stream chunk", {"chunkType": type(chunk).__name__, "topLevelKeys": list(chunk.keys()) if isinstance(chunk, dict) else None, "messageKeys": list(chunk.get("message", {}).keys()) if isinstance(chunk, dict) and isinstance(chunk.get("message"), dict) else None})
                    #endregion
                    content = chunk['message']['content']
                    complete_response += content
                    print(content, end='', flush=True)
                reply = Message(
                    id=f"assistant-{uuid.uuid4()}",
                    conversationId=history.memo[-1].conversationId,
                    role="assistant",
                    status="sent",
                    createdAt=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    author=Author(
                        id="agent",
                        displayName="Shoyu",
                        avatarUrl="assets/shoyu_neutral2.jpg",
                        isOnline=True,
                        role="assistant"
                    ),
                    parts=[Part(type="text", text=complete_response)]
                )
                history.memo.append(reply)
                print("bot.py chat()", history)
                MessageList.model_validate(history)
                #complete_response = self.removeUnwantedChars(complete_response)
                #self.text_to_speech(complete_response, 'af_bella,af_heart')
            return history
        except HTTPException:
            raise
        except Exception as e:
            print(f"bot.py chat: {e}")
            #region agent log
            _agent_log("H3,H4,H5", "backend/bot.py:130", "bot chat raised exception", {"exceptionType": type(e).__name__, "exceptionMessage": str(e)})
            #endregion
            raise HTTPException(status_code=502, detail="Chat generation failed")

Base_LLM = Bot( "shoyu_v1", "shoyu_stm")