from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import List
import requests
import json

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

@app.post("/dumpDB")
async def addChatHistory():

@app.post("/dumpLog")
async def addChatLog():

if __name__ == "__main__": # python -m uvicorn main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)