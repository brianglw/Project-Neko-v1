# cd backend; .venv/Scripts/activate; python -m uvicorn server:app --reload
# cd frontend; npm run dev
try: #imports 
    import json
    import os
    import sqlite3
    import time
    from dotenv import load_dotenv
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.exceptions import RequestValidationError
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    from bot import Base_LLM, Author, Message, MessageList, Part
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
DB_PATHS = {
    "history": HISTORY_PATH,
    "chatlog": CHATLOG_PATH,
}

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


#region agent log
def _agent_log(hypothesis_id: str, location: str, message: str, data: dict):
    with open("C:/Python/project_nekomimi/debug-9db512.log", "a", encoding="utf-8") as file:
        file.write(json.dumps({"sessionId": "9db512", "runId": "initial", "hypothesisId": hypothesis_id, "location": location, "message": message, "data": data, "timestamp": int(time.time() * 1000)}) + "\n")
#endregion


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.json()
    memo = body.get("memo") if isinstance(body, dict) else None
    last_message = memo[-1] if isinstance(memo, list) and memo else None
    #region agent log
    _agent_log("H6,H7,H8,H9", "backend/server.py:68", "request validation failed before route", {"path": request.url.path, "errors": exc.errors(), "bodyType": type(body).__name__, "memoLength": len(memo) if isinstance(memo, list) else None, "lastMessageKeys": list(last_message.keys()) if isinstance(last_message, dict) else None, "lastRole": last_message.get("role") if isinstance(last_message, dict) else None, "lastPartTypes": [part.get("type") for part in last_message.get("parts", [])] if isinstance(last_message, dict) and isinstance(last_message.get("parts"), list) else None})
    #endregion
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


def _get_db_path_(filename: str) -> str:
    path = DB_PATHS.get(filename)
    if path is None:
        raise HTTPException(status_code=400, detail="Invalid database filename")
    return path


def _createtables_(filename:str, path:str):
    try:
        with sqlite3.connect(f"{path}") as conn:
            cur = conn.cursor()
            required_columns = {
                "id",
                "conversationId",
                "role",
                "status",
                "createdAt",
                "author_id",
                "author_displayName",
                "author_avatarUrl",
                "author_isOnline",
                "author_role",
                "parts_type",
                "parts_text",
            }
            columns = {row[1] for row in cur.execute(f"pragma table_info({filename})")}
            if columns and not required_columns.issubset(columns):
                cur.execute(f"drop table if exists {filename}_legacy")
                cur.execute(f"alter table {filename} rename to {filename}_legacy")
            cur.execute(f"""create table if not exists {filename}(
                id text primary key,
                conversationId text,
                role text,
                status text,
                createdAt text,
                author_id text,
                author_displayName text,
                author_avatarUrl text,
                author_isOnline boolean,
                author_role text,
                parts_type text,
                parts_text text
            )""")
            conn.commit()
        return {}
    except Exception as e:
        print(f"server.py _createtables_(): {e}")

def _cleartable_(path:str, filename:str):
    try:
        with sqlite3.connect(f"{path}") as conn:
            cur = conn.cursor()
            cur.execute(f"delete from {filename}")
            cur.execute(f"select * from {filename}")
            print(f"fetching files from {filename}", cur.fetchall())
            conn.commit()
            return {}
    except Exception as e:
        print(f"server.py _cleartable_: {e}")


@app.get("/loadDB/{filename}")
async def loadFile(filename:str) -> MessageList: #extracts db files into a class field
    db = []
    try: 
        # if (hasMsgLimit == False):
        #     return MessageList(list=[])
        path = _get_db_path_(filename)
        with sqlite3.connect(path) as conn: 
            cur = conn.cursor()
            cur.execute(f"select count(*) from {filename}")
            numRows = cur.fetchone()[0]
            if (numRows > 0):
                res = cur.execute(f"select * from {filename} order by rowid desc limit {MSG_LIMIT}")

                for entry in res:
                    print(res)
                    db.append(Message(
                        id=entry[0],
                        conversationId=entry[1],
                        role=entry[2],
                        status=entry[3],
                        createdAt=entry[4],
                        author=Author(
                            id=entry[5],
                            displayName=entry[6],
                            avatarUrl=entry[7],
                            isOnline=bool(entry[8]),
                            role=entry[9],
                        ),
                        parts=[Part(type=entry[10], text=entry[11])],
                    ))
            cur.execute(f"select * from {filename}")
            print(f"server.py loadFile() {filename}: ", cur.fetchall())
            conn.commit()
        out = MessageList(memo=db[::-1])
        MessageList.model_validate(out)
        return out
    except HTTPException:
        raise
    except Exception as e:            
        print(f"server.py loadFile(): {e}")
        raise HTTPException(status_code=500, detail="File loading failed")


@app.post("/dumpDB/{filename}")
async def saveFile(filename : str, data : MessageList) -> MessageList: #saves summarized history to history.db
    try:      
        path = _get_db_path_(filename)
        with sqlite3.connect(path) as conn:
            #print(type(data), data['list'])
            # print("Connected") 
            cur = conn.cursor()
            # if (filename == "history"):
                # cur.execute(f"delete from {filename}")
            # print("Inserting values from", data.memo)
            for entry in data.memo:
                print(entry)
                part = entry.parts[0]
                cur.execute(
                    f"""insert or replace into {filename} (
                        id, conversationId, role, status, createdAt,
                        author_id, author_displayName, author_avatarUrl, author_isOnline, author_role,
                        parts_type, parts_text
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        entry.id,
                        entry.conversationId,
                        entry.role,
                        entry.status,
                        entry.createdAt,
                        entry.author.id,
                        entry.author.displayName,
                        entry.author.avatarUrl,
                        int(entry.author.isOnline),
                        entry.author.role,
                        part.type,
                        part.text,
                    ),
                )
            # print("Dumped values")
            cur.execute(f"select * from {filename}")
            print(f"server.py saveFile() {filename}: ", cur.fetchall())
            conn.commit()
        # print("Testing Input Validation")
        MessageList.model_validate(data)
        # print("success!")
        return data
    except HTTPException:
        raise
    except Exception as e:
        print(f"server.py saveFile(): {e}")
        raise HTTPException(status_code=500, detail="File saving failed")

@app.post("/new")
async def run():
    _createtables_("history", HISTORY_PATH)
    _createtables_("chatlog", CHATLOG_PATH)
    return {}

@app.post("/reset")
async def clearDBFiles():
    _cleartable_(HISTORY_PATH, "history")
    _cleartable_(CHATLOG_PATH, "chatlog")
    return {}

@app.post("/chat")
async def chat(data: MessageList) -> MessageList:
    try:
        print("Received data", data)
        MessageList.model_validate(data)
        #region agent log
        _agent_log("H1,H2", "backend/server.py:229", "server accepted chat payload", {"memoLength": len(data.memo), "roles": [msg.role for msg in data.memo], "lastPartTypes": [part.type for part in data.memo[-1].parts] if data.memo else [], "lastTextLength": len(data.memo[-1].parts[0].text) if data.memo and data.memo[-1].parts else 0})
        #endregion
        reply_data = Base_LLM.chat(data) 
        # print("LLM reply:", reply_data)
        MessageList.model_validate(reply_data)
        return reply_data
    except HTTPException as e:
        #region agent log
        _agent_log("H2,H3,H4,H5", "backend/server.py:234", "server returning http exception from chat", {"statusCode": e.status_code, "detail": e.detail})
        #endregion
        raise
    except Exception as e:
        print(f"server.py chat(): {e}")
        raise HTTPException(status_code=500, detail="Chat generation failed")
    


if __name__ == "__main__": 
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)