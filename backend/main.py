#dev branch

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

class Bot: 
    def __init__(self : "Bot", history: List[dict[str,str]], chatlog: List[dict[str,str]]) -> None: 
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
        # global SYSTEM_PROMPT
        global ASSISTANT_PROMPT
        try:
            # with open(f'{PATH}prompts/SYSTEM_PROMPT.txt', 'r', encoding='utf-8') as file:
            #     SYSTEM_PROMPT = f"""${file.read()}"""
            with open(f'{PATH}/prompts/ASSISTANT_PROMPT.txt', 'r', encoding='utf-8') as file:
                ASSISTANT_PROMPT = f"""{file.read().format(SUMMARY_WORD_LIMIT=SUMMARY_WORD_LIMIT)}"""
        except Exception as e: 
            print(f"Error loading prompt: {e}")
            

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

    def getPipeline(self : "OpenAIConnection") -> Any: #runs KokoroTTS imports locally 
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

            response = self.client.chat(
                model=self.model,
                messages=self.bot.history+ [entry],
                stream=True
            )
            
            for chunk in response:
                content = chunk['message']['content']
                complete_response += content
                print(content, end='', flush=True)
                
            print()  # Add final newline
            self.bot.history.append(entry)
            self.bot.chatlog.append(entry)
            self.bot.history.append({"role": "assistant", "content": complete_response})# adds ai output to history
            self.bot.chatlog.append({"role": "assistant", "content": complete_response})
            #complete_response = self.removeUnwantedChars(complete_response)
            #self.text_to_speech(complete_response, 'af_bella,af_heart')
            return
        
        except Exception as e:
            print(f"Error during chat: {e}")

    def generate_audio(
            self : "OpenAIConnection",
            silence_timeout=2.0,   # stop after 2s of silence
            threshold=500,          # RMS volume threshold (tune this)
            samplerate=16000,
            chunk=1024,
            output_file=f"{PATH}/user_input.wav"
            ) -> None: #uses pyaudio
        # the file name output you want to record into
        try:
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=samplerate,
                input=True,
                frames_per_buffer=chunk
            )

            print("Listening...")
            frames = []
            last_sound_time = time.time()
            started = False

            while True:
                data = stream.read(chunk, exception_on_overflow=False)
                frames.append(data)

                # Calculate RMS volume of this chunk
                audio_np = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.maximum(0, np.mean(audio_np.astype(np.float32)**2)))

                if rms > threshold:
                    last_sound_time = time.time()
                    if not started:
                        print("Recording...")
                        started = True

                # Only stop after silence if we've heard something first
                if started and (time.time() - last_sound_time > silence_timeout):
                    print("Silence detected, stopping.")
                    break

            stream.stop_stream()
            stream.close()
            p.terminate()

            with wave.open(output_file, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(samplerate)
                wf.writeframes(b''.join(frames))

            print(f"Saved to {output_file}")
        except Exception as e:
            print(e)
    
    def speech_to_text(self : "OpenAIConnection") -> str: #uses faster whisper
        try:
            model_size = "small.en"
            text = ""

            # Run on GPU with FP16
            # model = WhisperModel(model_size, device="cuda", compute_type="float16")

            # or run on GPU with INT8
            # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
            # or run on CPU with INT8
            model = WhisperModel(model_size, device="cpu", compute_type="int8")

            segments, info = model.transcribe(f"{PATH}/user_input.wav", beam_size=5)

            print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

            for segment in segments:
                text += segment.text + " "
                print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

            if (os.path.exists("C:/Python/project_nekomimi/backend/user_input.wav")):
                os.remove("C:/Python/project_nekomimi/backend/user_input.wav")

            return text
        except Exception as e:
            print(e)

    def run(self : "OpenAIConnection") -> None: #master function for loading, chatting, saving db
        try:
            self.loadFile() # loads JSON into history class attribute
            #self.getPipeline()
            while True: #conversation loop
                user_input = ""
                try:
                    print("Press Enter to voice record...")
                    user_input = input("You: ")
                    # waits until Enter is pressed
                    if (user_input == ""): 
                        self.generate_audio(silence_timeout=SILENCE_TIMEOUT, threshold=MIC_THRESHOLD)
                        user_input = self.speech_to_text()
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
                elif (user_input in ["/reset"]): # resets file
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

    def loadFile(self : "OpenAIConnection") -> None: #extracts db files into a class field
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
        except Exception as e:            
            print(f"Error loading file: {e}")
            print("Starting a new conversation.")
            print()
        return

    def trim_history(self : "OpenAIConnection", msg_limit : int = MSG_LIMIT) -> None: # cuts down chat history attribute to recent x messages
        if len(self.bot.history) > msg_limit:
            self.bot.history = self.bot.history[-(msg_limit-1):]
        return self.bot.history
        
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

    def saveChatLog(self : "OpenAIConnection") -> None: #inserts conversations history to chatlog.db
        try: 
            with sqlite3.connect(f"{CHATLOG_PATH}") as conn:
                cur = conn.cursor()
                data = [(msg['role'], msg['content']) for i, msg in enumerate(self.bot.chatlog)]
                print("Saving chat log: ")
                for entry in data:
                    print("saving to chatlog: " + entry[0] + " " + entry[1])
                    cur.execute(f"insert into chatlog values(null,?,?)", (entry[0], entry[1]))
                cur.execute("select * from chatlog")
                conn.commit()
        except Exception as e:
            print(f"Error Saving Chatlog: {e}")

    def saveFile(self : "OpenAIConnection") -> None: #saves summarized history to history.db
        try:
            with sqlite3.connect(f"{HISTORY_PATH}") as conn:
                cur = conn.cursor()
                cur.execute(f"delete from history")
                data = [(msg['role'], msg['content']) for i, msg in enumerate(self.bot.history)]
                for entry in self.bot.history:
                    print("saving to history: " + entry['role'] + " " + entry['content'])
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
    print(f"Running on port: {PORT}")
    bot : Bot = Bot(CHAT_HISTORY, NEW_MSG)
    ai_connection = OpenAIConnection(bot, "shoyu_v1", "shoyu_stm", 0.7, 10)
    print("Starting the program...")
    ai_connection.run()
    

