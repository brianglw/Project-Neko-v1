#run: .venv/Scripts/activate
# python -m uvicorn server:app --reload
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
    from dotenv import load_dotenv
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    from pydantic import BaseModel
    from bot import Base_LLM
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


@app.get("/loadDB/{filename}")
async def loadFile(filename:str) -> List[dict]: #extracts db files into a class field
    db = []
    try: 
        path = HISTORY_PATH if filename == "history" else CHATLOG_PATH if filename == "chatlog" else None
        with sqlite3.connect(path) as conn: 
            cur = conn.cursor()
            cur.execute(f"select count(*) from {filename}")
            numRows = cur.fetchone()[0]
            if (numRows > 0):
                res = cur.execute(f"select * from {filename}")
                for entry in res:
                    # print("Printing History: " + str(entry[0]) + ": " + entry[1] + " " + entry[2])
                    db.append({'role': entry[1], 'content': entry[2]})
        return {"list": db}
    except Exception as e:            
        print(f"Error loading file: {e}")
        return None


@app.post("/dumpDB/{filename}")
async def saveFile(filename : str, data : dict): #saves summarized history to history.db
    try:
        path = HISTORY_PATH if filename == "history" else CHATLOG_PATH if filename == "chatlog" else None
        with sqlite3.connect(path) as conn:
            #print(type(data), data['list'])
            cur = conn.cursor()
            if (filename == "history"):
                cur.execute(f"delete from {filename}")
            for entry in data['list']:
                # print("saving to history: " + entry['role'] + " " + entry['content'])
                cur.execute(f"insert into {filename} values(null,?,?)", (entry['role'], entry['content']))
            conn.commit()
        return data
    except Exception as e:
        print(f"Error Saving File: {e}")
        return None

@app.post("/new")
async def run():
    Base_LLM._createtables_("history", HISTORY_PATH)
    Base_LLM._createtables_("chatlog", CHATLOG_PATH)
    return {}

@app.post("/reset")
async def clearDBFiles():
    Base_LLM._cleartable_(HISTORY_PATH, "history")
    Base_LLM._cleartable_(CHATLOG_PATH, "chatlog")
    return {}

@app.post("/chat")
async def chat(history: dict):
    print("Received history", history)
    reply_history = Base_LLM.chat(history) # {"list": [{}]}
    print("LLM reply:", reply_history)
    return reply_history


if __name__ == "__main__": 
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)