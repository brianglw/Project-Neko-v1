#run: .venv/Scripts/activate
try: #imports 
    import requests
    import keyboard
    import os
    import json
    import re
    import winsound
    import warnings
    import sqlite3
    import pyaudio
    import wave
    import numpy as np
    import time
    from faster_whisper import WhisperModel
    from typing import List, Any, Optional
    from ollama import Client
    from dotenv import load_dotenv
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    from pydantic import BaseModel

    from bot import Bot, OpenAIConnection
except KeyboardInterrupt as e:
    print(f"Error: {e}")
    print("Exiting the program.")


#retrieve localhost from .env file
load_dotenv()
# if os.name == 'nt':
#     import sys
#     sys.stdout.reconfigure(encoding='utf-8')
HF_TOKEN = os.getenv('HF_TOKEN')
#PATHS
PATH="C:/Python/project_nekomimi/backend" 
HISTORY_PATH = f"{PATH}/db/history.db"
CHATLOG_PATH = f"{PATH}/db/chatlog.db"
PORT = os.getenv('PORT')

#LIMIT VARS
WORD_LIMIT = 120
SUMMARY_WORD_LIMIT=500
MSG_LIMIT=14
SILENCE_TIMEOUT = 3.0
MIC_THRESHOLD = 500

#GLOBAL VARS
CHAT_HISTORY=[]
NEW_MSG=[]

# SYSTEM_PROMPT = ""
ASSISTANT_PROMPT = ""

app = FastAPI(debug=True)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/loadDB")
async def getChatHistory():
    def loadFile(path : str) -> List[dict]: #extracts db files into a class field
        db = []
        try: 
            with sqlite3.connect(path) as conn: 
                cur = conn.cursor()
                cur.execute("select count(*) from history")
                numRows = cur.fetchone()[0]
                if (numRows > 0):
                    res = cur.execute("select * from history")
                    for entry in res:
                        print("Printing History: " + str(entry[0]) + ": " + entry[1] + " " + entry[2])
                        db.append({'role': entry[1], 'content': entry[2]})
        except Exception as e:            
            print(f"Error loading file: {e}")
        return db
    
    data = loadFile(HISTORY_PATH)
    print("loaded file data:", data)
    return data

@app.post("/dumpDB")
async def addChatHistory(data : dict):
    def saveFile(path : str, data : dict): #saves summarized history to history.db
        db = []
        try:
            with sqlite3.connect(path) as conn:
                cur = conn.cursor()
                cur.execute(f"delete from history")
                formatted_data = [(msg['role'], msg['content']) for i, msg in enumerate(db)]
                for entry in data:
                    print("saving to history: " + entry['role'] + " " + entry['content'])
                    cur.execute(f"insert into history values(null,?,?)", (entry['role'], entry['content']))
                conn.commit()
            return data
        except Exception as e:
            print(f"Error Saving File: {e}")
            return None
    return saveFile(HISTORY_PATH, data)
    

@app.post("/dumpLog")
async def addChatLog(data : dict):
    def saveChatLog(path : str, data : dict):
        db = []
        try: 
            with sqlite3.connect(f"{CHATLOG_PATH}") as conn:
                cur = conn.cursor()
                data = [(msg['role'], msg['content']) for i, msg in enumerate()]
                print("Saving chat log: ")
                for entry in data:
                    print("saving to chatlog: " + entry[0] + " " + entry[1])
                    cur.execute(f"insert into chatlog values(null,?,?)", (entry[0], entry[1]))
                cur.execute("select * from chatlog")
                conn.commit()
        except Exception as e:
            print(f"Error Saving Chatlog: {e}")
            return None
    return saveChatLog(CHATLOG_PATH, data)


#summarizeHistory
@app.post("/summarize")
async def summarizeHistory():
    def summarize_history(self : "OpenAIConnection", msg_limit : int = MSG_LIMIT) -> None: # cuts down chat history attribute to 1 summary when history exceeds context length
        try: 
            lastTwoMsgs = []
            complete_response = ""
            msgSum = ""
            if int(len(self.bot.history)) > msg_limit: 
                for msg in self.bot.history:
                    msgSum += f"\n('role': {msg['role']}, 'content': {msg['content']})"
                    # summary_prompt.append({'role': msg['role'], 'content': msg['content']})
            print(msgSum)
            summary_prompt : List[dict[str,str]] = [{'role': 'user', 'content': msgSum}]
            response = self.client.chat(
                model=self.assistant_model,
                messages=summary_prompt,
                stream=True
            )
            print("Summarizing chat history")
            for chunk in response:
                content = chunk['message']['content']
                complete_response += content
                print(content, end='', flush=True)
            lastTwoMsgs = self.bot.history[-2:]
            self.bot.history = []
            self.bot.history.append({'role': 'assistant', 'content': complete_response})
            self.bot.history = self.bot.history + lastTwoMsgs
        except Exception as e:
            print(f"Error while summarizing: {e}")
        return

#runLLM
@app.get("/run")
async def run():
    return

#chatLLM
@app.post("/chat")
async def chat():
    return


if __name__ == "__main__": # python -m uvicorn server:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)