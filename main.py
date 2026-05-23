#testing branch
try: 
    import requests
    import os
    import json
    import re
    import winsound
    import warnings
    import sqlite3
    from typing import List, Any, Optional
    from openai import OpenAI
    from dotenv import load_dotenv
except KeyboardInterrupt as e:
    print("Error: {e}")
    print("Exiting the program.")


#retrieve api_key from .env file
load_dotenv()
if os.name == 'nt':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

#API keys
HF_TOKEN = os.getenv('HF_TOKEN')
API_KEY = os.getenv('OPENROUTER_API_KEY')
#PATHS
BASE_URL = "https://openrouter.ai/api/v1"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
PATH="C:/Python/aishoyu/" 
HISTORY_PATH = f"{PATH}/db/history.db"
CHATLOG_PATH = f"{PATH}/db/chatlog.db"

#LIMIT VARS
WORD_LIMIT = 120
SUMMARY_WORD_LIMIT=500
MSG_LIMIT=10

#GLOBAL VARS
CHAT_HISTORY=[]
NEW_MSG=[]

SYSTEM_PROMPT = ""
ASSISTANT_PROMPT = ""

class Bot: 
    def __init__(self : "Bot", api_key : str, api_url : str, history: List[dict[str,str]], chatlog: List[dict[str,str]]) -> None: 
        self.api_key : str = api_key
        self.api_url : str = api_url
        self.history : List[dict[str,str]] = history
        self.chatlog :List[dict[str,str]] = chatlog
        self.run()
        self.loadPrompt()

    def run(self: "Bot") -> None:
        with sqlite3.connect(f"{HISTORY_PATH}") as conn: 
            cur = conn.cursor()
            cur.execute("create table if not exists history(id integer primary key autoincrement, role text, msg text)")
        with sqlite3.connect(f"{CHATLOG_PATH}") as conn:
            cur = conn.cursor()
            cur.execute("create table if not exists chatlog(id integer primary key autoincrement, role text, msg text)")
    
    def loadPrompt(self: "Bot") -> None: 
        global SYSTEM_PROMPT
        global ASSISTANT_PROMPT
        try:
            with open(f'{PATH}prompts/SYSTEM_PROMPT.txt', 'r', encoding='utf-8') as file:
                SYSTEM_PROMPT = f"""${file.read()}"""
            with open(f'{PATH}prompts/ASSISTANT_PROMPT.txt', 'r', encoding='utf-8') as file:
                ASSISTANT_PROMPT = f"""${file.read()}"""
        except Exception as e: 
            print("Error loading prompt: " + e)
            

class OpenAIConnection:
    def __init__(self : "OpenAIConnection", bot : Bot, model : str, temperature : float, max_tokens : int):
        self.bot : Bot = bot
        self.model : str = model
        self.temperature : float = temperature
        self.token_limit : int = max_tokens
        self.headers : dict[str, str] = {
            "Authorization": f"Bearer {self.bot.api_key}",
            "Content-Type": "application/json"
        }
        # Use bot.api_key to initialize client
        self.client = OpenAI(
            base_url=BASE_URL,
            api_key= self.bot.api_key,
        )
        self.pipeline: Optional[Any] = None

    def _close_(self : "OpenAIConnection") -> None: 
        self.bot.con.close()
        return

    def getPipeline(self : "OpenAIConnection") -> Any: #runs imports locally for KeyboardError
        if self.pipeline is None:
            from huggingface_hub import login
            from kokoro import KPipeline
            warnings.filterwarnings("ignore", category=UserWarning, module="torch.nn.modules.rnn")
            warnings.filterwarnings("ignore", category=FutureWarning, module="torch.nn.utils.weight_norm")
            # only attempt login when HF_TOKEN is present
            if HF_TOKEN:
                login(token=HF_TOKEN)
                print("Token found:", HF_TOKEN is not None, flush=True)
            else:
                print("No HF_TOKEN provided; skipping HF login.", flush=True)
            print("Loading Kokoro TTS model (one-time, may take ~30s)...", flush=True)
            self.pipeline = KPipeline(lang_code='a', device='cpu', repo_id='hexgrad/Kokoro-82M')
            print("Kokoro TTS ready.", flush=True)
        return self.pipeline

    #send and receive msg from LLM model 
    def chat(self : "OpenAIConnection", user_input : str) -> None:
        try: 
            complete_response = "" # init completion tokens
            if (len(self.bot.history) > MSG_LIMIT):
                self.summarize_history()
            entry = {'role': 'user', 'content': user_input}
            self.bot.history.append(entry)
            self.bot.chatlog.append(entry)
            payload = {
                "model": self.model,
                "messages": self.bot.history, 
                "reasoning": {
                    "effort": "low",
                    "max_tokens": self.token_limit
                },
                "provider": {
                    "order": ['Alibaba'],
                    "allow_fallbacks": True
                }
            }
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.bot.history,
                stream=True
            )
        
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    complete_response += content
        
                    print(content, end="", flush=True)
                
            print()  # Add final newline
            self.bot.history.append({"role": "assistant", "content": complete_response})# adds ai output to history
            self.bot.chatlog.append({"role": "assistant", "content": complete_response})
            #complete_response = self.removeUnwantedChars(complete_response)
            #self.text_to_speech(complete_response, 'af_bella,af_heart')
            return
        
        except Exception as e:
            print(f"Error: {e}")

    def appendSystemPrompt(self : "OpenAIConnection") -> None: # appends sys_prompt when chat_history.json reset, not exists, not loaded properly
        self.bot.history.append({'role': 'system', 'content': SYSTEM_PROMPT})
        return

    def run(self : "OpenAIConnection") -> None: #master function for loading, chatting, saving db
        try:
            self.loadFile() # loads JSON into history class attribute
            #self.getPipeline()
            while True: #conversation loop
                try:
                    user_input = input("You: ")
                except EOFError:
                    print(
                        "No interactive input (stdin returned EOF). "
                        "In VS Code/Cursor, start with the launch config that uses the integrated terminal, "
                        "or run: python main.py in a terminal."
                    )
                    break
                if (user_input in ["/bye"]): #exits conversation loop
                    print("Exiting the program.\nSaving chat log and summarizing conversation...")
                    self.saveChatLog()
                    if (len(self.bot.history)>MSG_LIMIT):
                        self.summarize_history() # summarizes & trims conversation length
                        print("Done!")
                    self.saveFile()
                    break
                elif (user_input in ["reset"]): # resets file
                    if os.path.exists(f"{HISTORY_PATH}"):
                        os.remove(f"{HISTORY_PATH}")
                    else:
                        print("No history DB to remove.")
                    if os.path.exists(f"{CHATLOG_PATH}"):
                        os.remove(f"{CHATLOG_PATH}")
                    else:
                        print("No chatlog DB to remove.")
                else: # main chat
                    self.chat(user_input)
        except Exception as e:
            print(e)
    
    def removeUnwantedChars(self : "OpenAIConnection", text : str) -> str: #preprocesses text for tts
        # remove emoji's
        emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r' ', text)
        text = re.sub("@[A-Za-z0-9_]+"," ", text)
        # remove URLS
        text = re.sub(r'http\S+', ' ', text)
        # remove hashtags
        text = re.sub("#[A-Za-z0-9_]+","", text)
        # remove punctuation
        text = re.sub("[^0-9A-Za-z ]", "" , text)
        # remove double spaces
        text = text.replace('  ',"")  
        return text          

    def loadFile(self : "OpenAIConnection") -> None: #loads from db
        try: 
            with sqlite3.connect(f"{HISTORY_PATH}") as conn: 
                cur = conn.cursor()
                cur.execute("select count(*) from history")
                numRows = cur.fetchone()[0]
                if (numRows > 0):
                    res = cur.execute("select * from history")
                    for entry in res:
                        print("Printing History: " + str(entry[0]) + ": " + entry[1] + " " + entry[2])
                        self.bot.history.append({'role': entry[1], 'content': entry[2]})
                else: 
                    self.appendSystemPrompt()
                self.bot.history[0] = {'role': 'system', 'content': SYSTEM_PROMPT}
            # with sqlite3.connect(f"{CHATLOG_PATH}") as conn:
            #     cur = conn.cursor()
            #     res = cur.execute("select * from chatlog")
            #     for entry in res:
            #         print("Printing Chatlog: " + str(entry[0]) + ": " + entry[1] + " " + entry[2])
        except Exception as e:            
            print(f"Error loading file: {e}")
            print("Starting a new conversation.")
            print()
            self.appendSystemPrompt()
            # <--- delete when done --->
            # if os.path.exists(f"{PATH}chat_history.json"): #check file existence
            #     try:
            #         with open(f"{PATH}chat_history.json", "r", encoding='utf-8') as readfile:
            #             self.bot.history = json.load(readfile)
            #     except Exception as e: 
            #         print(f"Error while reading file: {e}.")
            #         self.appendSystemPrompt()
            # else: #file doesn't exist -> print error msg & create new
            #     print("Error: File not Found. Starting a new conversation...")
            #     self.appendSystemPrompt()
        return

    def trim_history(self : "OpenAIConnection", msg_limit : int = MSG_LIMIT) -> None: # cuts down chat history attribute to recent x messages
        sys_prompt = self.bot.history[0]
        if len(self.bot.history) > msg_limit:
            self.bot.history = [sys_prompt] + self.bot.history[-(msg_limit-1):]
        return self.bot.history
        
    def summarize_history(self : "OpenAIConnection", msg_limit : int = MSG_LIMIT) -> None: # cuts down chat history attribute to 1 summary when history exceeds context length
        try: 
            summary_prompt : List[dict[str,str]] = [{'role': 'system', 'content': ASSISTANT_PROMPT}]
            if int(len(self.bot.history)) > msg_limit: # appends past conversation to str
                for msg in self.bot.history[1:]:
                    summary_prompt.append({'role': msg['role'], 'content': msg['content']})
            full_reply = "" # init completion tokens
            payload = {
                "model": self.model,
                "messages": summary_prompt,
                "reasoning": {
                    "max_tokens": 1000
                }
            }
            response=requests.post(self.bot.api_url, headers=self.headers, json=payload)
            data = response.json()
            full_reply = data['choices'][0]['message']['content']
            self.bot.history = [self.bot.history[0]] # CLEARS self.bot.history attribute
            self.bot.history.append({'role': 'assistant', 'content': full_reply})
            print(f"Model: {data['model']} by {data['provider']}")
            print(f"Response: {full_reply}")
        except Exception as e:
            print(f"Error while summarizing: {e}")
        return

    def saveChatLog(self : "OpenAIConnection") -> None:
        try: 
            with sqlite3.connect(f"{CHATLOG_PATH}") as conn:
                cur = conn.cursor()
                data = [(msg['role'], msg['content']) for i, msg in enumerate(self.bot.chatlog)]
                print("Saving chat log: ")
                for entry in data:
                    print("saving: " + entry[0] + " " + entry[1])
                    cur.execute(f"insert into chatlog values(null,?,?)", (entry[0], entry[1]))
                cur.execute("select * from chatlog")
                print(str(cur.fetchall()))
                conn.commit()
        except Exception as e:
            print(f"Error Saving Chatlog: {e}")

    def saveFile(self : "OpenAIConnection") -> None: #saves summarized history to db
        try:
            with sqlite3.connect(f"{HISTORY_PATH}") as conn:
                cur = conn.cursor()
                cur.execute(f"delete from history")
                data = [(msg['role'], msg['content']) for i, msg in enumerate(self.bot.history)]
                for entry in self.bot.history:
                    print("saving: " + entry['role'] + " " + entry['content'])
                    cur.execute(f"insert into history values(null,?,?)", (entry['role'], entry['content']))
                conn.commit()
            return
        except Exception as e:
            print(f"Error Saving File: {e}")
    
    def text_to_speech(self: "OpenAIConnection", text : str, voice : str) -> None: #creates and plays audio file upon generation
        import soundfile as sf
        from pydub import AudioSegment
        text = f'''
            {text}
        '''
        generator = self.getPipeline()(
            text, voice=voice,  
            speed=1, split_pattern=r'\n+'
        )
        print("Generating audio file from text...")
        for result in generator:
            sf.write(f'{PATH}output.wav', result.audio, 24000) # save each audio file
        try:
            audio_path = f'{PATH}output.wav'
            print(f"Loading audio from {audio_path}...")
            output = AudioSegment.from_wav(audio_path)
            print("Loaded audio, now playing...")
            winsound.PlaySound(audio_path, winsound.SND_FILENAME)
            os.unlink(audio_path)
            print("Play finished")
        except Exception as e:
            print(f"Error: {e}")
        return

if __name__ == "__main__": # executes only when run directly
    bot : Bot = Bot(API_KEY, API_URL, CHAT_HISTORY, NEW_MSG)
    ai_connection : OpenAIConnection = OpenAIConnection(bot, "deepseek/deepseek-v3.2", 0.7, 10)
    print("Starting the program...")
    ai_connection.run()
    

