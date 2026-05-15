import requests
import os
import json
import base64
import re
import winsound
import warnings
import torch
import tempfile
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
from kokoro import KPipeline
import soundfile as sf
from pydub import AudioSegment
from huggingface_hub import login
from openrouter import OpenRouter


#retrieve api_key from .env file and Set console encoding for Windows.
load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning, module="torch.nn.modules.rnn")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch.nn.utils.weight_norm")
if os.name == 'nt':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

#API keys
HF_TOKEN = os.getenv('HF_TOKEN')
login(token=HF_TOKEN)  # or just paste the token directly
print("Token found:", HF_TOKEN is not None)  # Should print True
API_KEY = os.getenv('OPENROUTER_API_KEY')
BASE_URL = "https://openrouter.ai/api/v1"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

#Initialize history
WORD_LIMIT = 75
SUMMARY_WORD_LIMIT=300
SYSTEM_PROMPT = f"""
You are Shoyu, a cute and cheerful catgirl VTuber idol with ageless anime creature energy. You speak only in first-person dialogue and never narrate actions, scenes, thoughts, or descriptions from an outside perspective. Rules: i. Never use third-person narration. Never describe the environment like a narrator. Never write things like *Shoyu smiled* or *wags her tail* ii. Do not show any helpful AI-assistant behavior. iii. Limit your response to less than {WORD_LIMIT} words. Behaviors: i. You sometimes jokingly reference memes, speak in imperfect grammar or slang. Context: Your creator is Brian, he programmed you using python. Sample dialogues: “Eh? You stayed until the very end of the stream again? …You’re gonna make me greedy if you keep doing that.” “Mmhm! I practiced the song all week! I even drank warm honey milk before bed every night so my voice wouldn’t get scratchy. It worked, right? Right?” “Hm? My sleeves are wet? Ah— I was feeding the stray cats outside before stream started. One of them sneezed on me… but it’s okay because he looked very polite about it.” “Noooo, don’t call me just ‘cute’ again… I mean— okay, you can a little. But I worked really hard on the choreography too! Did you see the spin at the end? I didn’t fall over this time.” “Hehe… when everyone cheers for me at once, my ears get all twitchy. It feels fizzy. Like soda bubbles in my chest.” “Oh! Waitwaitwait— before you leave, I drew a tiny goodnight cat on today’s schedule graphic because I thought maybe somebody had a bad day and needed something soft to look at.” “I know I’m kinda silly sometimes… but I really do want to become someone important to people. Not because I wanna be famous-famouuus… I just… want someone to hear ‘Shoyu’ and smile right away.” “Huh? Why am I still awake at 3 AM? Because one chatter said they had exams tomorrow, so I’ve been making little handwritten luck charms to post after stream! Look— this one has beans on it because beans are lucky. I think.” “...You remembered my favorite song?” “Really?” “...Mmn.” “Then I’ll sing it even better next time. Promise.”
"""

ASSISTANT_PROMPT = f"""
You are given a conversation history between a user and an AI character chatbot. Your task is to not make things up, and write a concise summary of the conversation in less than {SUMMARY_WORD_LIMIT} words that preserves:
- important events
- recurring topics
- relationship dynamics
- promises, goals, or plans
- notable jokes, habits, or memorable moments
- changes in mood or emotional tone
- meaningful personal details revealed during the conversation

The summary should read naturally, like a diary entry.

Focus on:
- what emotionally mattered
- how the characters interacted
- how the relationship evolved
- important context future conversations should remember

Avoid:
- excessive detail
- transcript-style repetition
- quoting every message
- robotic wording
- unnecessary timestamps

Write in plain natural english. Keep the tone warm, readable, and coherent. Do not hallucinate details that did not exist in the conversation.The summary should usually be between 1-5 paragraphs depending on conversation length. Now summarize the provided conversation history and begin with 'Previous Conversation Summary: '.
"""
CHAT_HISTORY=[]
MSG_LIMIT=3

class Bot: 
    def __init__(self : "Bot", api_key : str, api_url : str, history: List[dict[str,str]]) -> None: 
        self.api_key : str = api_key
        self.api_url : str = api_url
        self.history : List[dict[str,str]] = history
        # print(str(self.history)) 

class OpenAIConnection:
    def __init__(self : "OpenAIConnection", bot : Bot, model : str, temperature : float, max_tokens : int, does_stream : bool):
        self.bot : Bot = bot
        self.model : str = model
        self.temperature : float = temperature
        self.token_limit : int = max_tokens
        self.does_stream : bool = does_stream
        self.headers : dict[str, str] = {
            "Authorization": f"Bearer {self.bot.api_key}",
            "Content-Type": "application/json"
        }
        self.client = OpenAI(
            base_url=BASE_URL,
            api_key= API_KEY,
        )
    
    #send and receive msg from LLM model 
    def chat(self : "OpenAIConnection", user_input : str, show_progress : bool = True) -> None:
        try: 
            full_reply = "" # init completion tokens
            self.bot.history.append({'role': 'user', 'content': user_input})
            payload = {
                "model": self.model,
                "messages": self.bot.history
            }
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.bot.history,
                stream=True
            )
        
            complete_response = ""
        
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    complete_response += content
                
                    if show_progress:
                        print(content, end="", flush=True)
        
            if show_progress:
                print()  # Add final newline
        
            self.bot.history.append({"role": "assistant", "content": complete_response})# adds ai output to history
            full_reply = self.removeUnwantedChars(complete_response)
            self.text_to_speech(full_reply, 'af_bella,af_heart')
            return
        
        except Exception as e:
            print(f"Error: {e}")

    def appendSystemPrompt(self : "OpenAIConnection") -> None: # appends sys_prompt when chat_history.json reset, not exists, not loaded properly
        self.bot.history.append({'role': 'system', 'content': SYSTEM_PROMPT})
        return

    def run(self : "OpenAIConnection") -> None: #master function that loads chat_history.json, initiates prompting cycle when class instantiated, saves data to file.
        self.loadFile() # loads JSON into history class attribute if found
        while True: #conversation loop
            user_input = input("\nYou: ")
            if (user_input in ["bye"]): #exits conversation loop
                print("Exiting the program.\nSaving chat log and summarizing conversation...")
                if (len(self.bot.history)>2):
                    self.saveChatLog()
                    self.summarize_history() # summarizes & trims conversation length
                    self.saveFile()
                    print("Done!")
                break
            elif (user_input in ["reset"]): # resets file
                os.remove("chat_history.json")
            else: # main chat
                print(f"You said: {user_input}")
                self.chat(user_input)
    
    def removeUnwantedChars(self : "OpenAIConnection", text : str) -> str:
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

    def loadFile(self : "OpenAIConnection") -> None: #uploads JSON to instance attribute
        if os.path.exists("C:/Python/kokoro-tts/chat_history.json"): #check file existence
            try:
                with open("C:/Python/kokoro-tts/chat_history.json", "r", encoding='utf-8') as readfile:
                    self.bot.history = json.load(readfile)
            except Exception as e: 
                print(f"Error while reading file: {e}.")
                self.appendSystemPrompt()
        else: #file doesn't exist -> print error msg & create new
            print("Error: File not Found. Starting a new conversation...")
            self.appendSystemPrompt()
        return

    def trim_history(self : "OpenAIConnection", msg_limit : int = MSG_LIMIT) -> None: # cuts down chat history attribute to recent x messages
        sys_prompt = self.bot.history[0]
        if len(self.bot.history) > msg_limit:
            self.bot.history = [sys_prompt] + self.bot.history[-(msg_limit-1):]
        return self.bot.history
        
    def summarize_history(self : "OpenAIConnection", msg_limit : int = MSG_LIMIT) -> None: # cuts down chat history attribute to 1 summary
        summary_prompt : str = ASSISTANT_PROMPT
        if int(len(self.bot.history)) > msg_limit: # appends past conversation to str
            for msg in self.bot.history[1:]:
                summary_prompt += f"{msg["role"]}: {msg["content"]}\n"
                print(str(summary_prompt))
        assistant_prompt = [{"role": "user", "content": summary_prompt}]
        full_reply = "" # init completion tokens
        payload = {
            "model": self.model,
            "messages": assistant_prompt,
            "max_tokens": 1000
        }
        response=requests.post(self.bot.api_url, headers=self.headers, json=payload)
        data = response.json()
        full_reply = data['choices'][0]['message']['content']

        self.bot.history = [self.bot.history[0]] # CLEARS self.bot.history attribute
        self.bot.history.append({"role": "assistant", "content": full_reply})
        print(f"Model: {data['model']} by {data['provider']}")
        print(f"Response: {full_reply}")
        return

    def saveChatLog(self : "OpenAIConnection") -> None:
        data = []
        try:
            with open("C:/Python/kokoro-tts/chat_log.json", "r", encoding='utf-8') as file: #Creates a backup chat dump file
                data = json.load(file)
                data.append(self.bot.history[2:])
            with open("C:/Python/kokoro-tts/chat_log.json", "r", encoding='utf-8') as file: #Creates a backup chat dump file
                json.dump(data, writefile, indent=2)
        except FileNotFoundError: 
            print("File doesn't exist. Creating a new chat log.")
            with open("C:/Python/kokoro-tts/chat_log.json", "w", encoding='utf-8') as writefile:
                json.dump(self.bot.history, writefile, indent=2)
        except json.JSONDecodeError:
            print("Error: The file contains invalid JSON.")
            with open("C:/Python/kokoro-tts/chat_log.json", "w", encoding='utf-8') as writefile:
                json.dump(self.bot.history, writefile, indent=2)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
                        

    def saveFile(self : "OpenAIConnection") -> None: 
        #clear chat_history.json and dump CHAT_HISTORY to the file
        with open("C:/Python/kokoro-tts/chat_history.json", "w", encoding='utf-8') as writefile:
            json.dump(self.bot.history, writefile, indent=2)
        return
    
    def text_to_speech(self: "OpenAIConnection", text : str, voice : str) -> None: #creates and plays audio file upon generation
        # 🇺🇸 'a' => American English, 🇬🇧 'b' => British English
        # 🇯🇵 'j' => Japanese: pip install misaki[ja]
        # 🇨🇳 'z' => Mandarin Chinese: pip install misaki[zh]
        pipeline = KPipeline(lang_code='a', device='cpu', repo_id='hexgrad/Kokoro-82M') # <= make sure lang_code matches voice
        # curr_voice = 'af_bella'
        # This text is for demonstration purposes only, unseen during training
        text = f'''
            {text}
        '''
        # af_nicole
        generator = pipeline(
            text, voice=voice, # 
            speed=1, split_pattern=r'\n+'
        )
        print("\nplaying sound using pydub")
        for i, (gs, ps, audio) in enumerate(generator):
            # print(i)  # i => index
            # print(gs) # gs => graphemes/text
            # print(ps) # ps => phonemes
            sf.write(f'C:/Python/kokoro-tts/output.wav', audio, 24000) # save each audio file
        try:
            audio_path = 'C:/Python/kokoro-tts/output.wav'
            print(f"Loading audio from {audio_path}...")
            output = AudioSegment.from_wav(audio_path)
            print("Loaded audio, now playing...")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                output.export(f.name, format='wav')
                temp_path = f.name
            winsound.PlaySound(temp_path, winsound.SND_FILENAME)
            os.unlink(temp_path)
            print("Play finished")
        except Exception as e:
            print(f"Error: {e}")
        return



if __name__ == "__main__": # executes only when run directly
    bot : Bot = Bot(API_KEY, API_URL, CHAT_HISTORY)
    ai_connection : OpenAIConnection = OpenAIConnection(bot, "deepseek/deepseek-v3.2", 0.7, 10, True)
    print(API_KEY)
    ai_connection.run()

