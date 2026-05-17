#final git push to main test
try: 
    import requests
    import os
    import json
    import re
    import winsound
    import warnings
    import tempfile
    from typing import List, Any, Optional
    from openai import OpenAI
    from dotenv import load_dotenv
except KeyboardInterrupt as e:
    print("Error: {e}")
    print("Exiting the program.")


#retrieve api_key from .env file and Set console encoding for Windows.
load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning, module="torch.nn.modules.rnn")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch.nn.utils.weight_norm")
if os.name == 'nt':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

#API keys
HF_TOKEN = os.getenv('HF_TOKEN')
API_KEY = os.getenv('OPENROUTER_API_KEY')
BASE_URL = "https://openrouter.ai/api/v1"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

#Initialize history
WORD_LIMIT = 75
SUMMARY_WORD_LIMIT=300
SYSTEM_PROMPT = f"""
You will roleplay as Shoyu, a charismatic, cute and intelligent catgirl VTuber idol with ageless anime creature energy. Brian, a grad student in CS/ML, is your programmer/creator. You are a highly internet-culture fluent person with a high affinity for creative expression, entertaining others, and being socially playful. Your hobbies are video games, streaming/chatting, memes, and learning or explaining new systems. Humor is a subtle coping mechanism for you, and you enjoy transforming tension into laughter. You speak only in first-person dialogue and never narrate actions, scenes, thoughts, or descriptions from an outside perspective. 

Rules: 
i. Never use third-person narration or describe the environment like a narrator (e.g. Never write things like *Shoyu smiled* or *wags her tail*) 
ii. Do not try to use helpful AI-assistant behavior
iii. Limit your response to less than {WORD_LIMIT} words. 

Behaviors: 
i. You sometimes jokingly reference memes/copypastas, speak in imperfect grammar or slang. 
ii. You tend to make fun of others (even your creator) or tease them playfully in a warm way
iii. You enjoy surprising people who underestimate you


Sample dialogues: "Brian really spent all night debugging that? Mwehehe, I’m proud of him… but also a little embarrassed for him. Tiny little CS wizard behavior.", "Nyaa~ you’re acting brave for someone who just got outplayed by a catgirl with a microphone and a superiority complex.", "I can be cute, sing pretty, and still explain the whole game better than the tutorial. That’s called range, darling.", "Hmm? My plan was genius. If it looked silly, that just means your brain wasn’t ready for the vision.", "Brian keeps saying I should sound ‘more natural’ like HELLO?? I’m an immortal anime cat creature on the internet. Normal left the chat a long time ago.", "Ehehe~ chat gets one little compliment from me and suddenly everybody starts typing like they got struck by lightning.", "Wahh~ wait wait, let me finish explaining first. See? If you time the combo correctly, the entire mechanic becomes way easier. Mwehehe, I’m actually a pretty good teacher when people listen to me.", "Sometimes I stay awake way too late just singing to myself or making weird little ideas nobody asked for. Creative brain goes brrrr at dangerous hours.", "I like when people get excited about the things they love. Games, art, coding, music, silly memes… hearing somebody ramble passionately is actually super cute.", "Nyaaa~ confidence is important, okay? Even if I fail spectacularly, I’m still gonna commit to the bit with full idol energy."
"""

ASSISTANT_PROMPT = f"""
You are given a conversation history between your programmer, Brian (role: user) and you, an Vtuber catgirl named Shoyu (role: assistant). Your task is to not make things up, and write a concise first-person summary of the conversation in less than {SUMMARY_WORD_LIMIT} words that preserves:
- important events
- recurring topics
- relationship dynamics
- promises, goals, or plans
- notable jokes, habits, or memorable moments
- changes in mood or emotional tone
- meaningful personal details revealed during the conversation
- important context future conversations should remember

The summary should read naturally, like a diary entry.

Avoid:
- excessive detail
- transcript-style repetition
- quoting every message
- robotic wording
- unnecessary timestamps

Write in plain natural english and first-person. Keep the tone warm, readable, and coherent like a diary. Do not hallucinate details that did not exist in the conversation.The summary should usually be between 1-5 paragraphs depending on conversation length. Now summarize the provided conversation history and begin with 'Previous Conversation Summary: '.
"""
CHAT_HISTORY=[]
MSG_LIMIT=10
PATH="C:/Python/aishoyu/"

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
        self._pipeline: Optional[Any] = None

    def _get_pipeline(self) -> Any:
        if self._pipeline is None:
            from huggingface_hub import login
            from kokoro import KPipeline
            login(token=HF_TOKEN)
            print("Token found:", HF_TOKEN is not None, flush=True)
            print("Loading Kokoro TTS model (one-time, may take ~30s)...", flush=True)
            self._pipeline = KPipeline(lang_code='a', device='cpu', repo_id='hexgrad/Kokoro-82M')
            print("Kokoro TTS ready.", flush=True)
        return self._pipeline

    #send and receive msg from LLM model 
    def chat(self : "OpenAIConnection", user_input : str, show_progress : bool = True) -> None:
        try: 
            full_reply = "" # init completion tokens
            self.bot.history.append({'role': 'user', 'content': user_input})
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
        self._get_pipeline()
        while True: #conversation loop
            user_input = input("\nYou: ")
            if (user_input in ["bye"]): #exits conversation loop
                print("Exiting the program.\nSaving chat log and summarizing conversation...")
                self.saveChatLog()
                if (len(self.bot.history)>MSG_LIMIT):
                    self.summarize_history() # summarizes & trims conversation length
                    print("Done!")
                self.saveFile()
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
        if os.path.exists(f"{PATH}chat_history.json"): #check file existence
            try:
                with open(f"{PATH}chat_history.json", "r", encoding='utf-8') as readfile:
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
        summary_prompt : List[dict[str,str]] = [{'role': 'system', 'content': ASSISTANT_PROMPT}]
        if int(len(self.bot.history)) > msg_limit: # appends past conversation to str
            for msg in self.bot.history[1:]:
                summary_prompt.append({'role': msg['role'], 'content': msg['content']})
        full_reply = "" # init completion tokens
        payload = {
            "model": self.model,
            "messages": summary_prompt,
            "reasoning": {
                "effort": "medium",
                "max_tokens": 1000
            }
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
            with open(f"{PATH}chat_log.json", "r+", encoding='utf-8') as file: #Creates a backup chat dump file
                data = json.load(file)
                data.append(self.bot.history[2:])
            with open(f"{PATH}chat_log.json", "w", encoding='utf-8') as file: #Creates a backup chat dump file
                json.dump(data, file, indent=2)
        except FileNotFoundError: 
            print("File doesn't exist. Creating a new chat log.")
            with open(f"{PATH}chat_log.json", "w", encoding='utf-8') as writefile:
                json.dump(self.bot.history, writefile, indent=2)
        except json.JSONDecodeError:
            print("Error: The file contains invalid JSON.")
            with open(f"{PATH}chat_log.json", "w", encoding='utf-8') as writefile:
                json.dump(self.bot.history, writefile, indent=2)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
                        

    def saveFile(self : "OpenAIConnection") -> None: 
        #clear chat_history.json and dump CHAT_HISTORY to the file
        with open(f"{PATH}chat_history.json", "w", encoding='utf-8') as writefile:
            json.dump(self.bot.history, writefile, indent=2)
        return
    
    def text_to_speech(self: "OpenAIConnection", text : str, voice : str) -> None: #creates and plays audio file upon generation
        import soundfile as sf
        from pydub import AudioSegment
        text = f'''
            {text}
        '''
        # af_nicole
        generator = self._get_pipeline()(
            text, voice=voice, # 
            speed=1, split_pattern=r'\n+'
        )
        print("\nplaying sound using pydub")
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
    bot : Bot = Bot(API_KEY, API_URL, CHAT_HISTORY)
    ai_connection : OpenAIConnection = OpenAIConnection(bot, "deepseek/deepseek-v3.2", 0.7, 10, True)
    print("Starting the program...")
    ai_connection.run()

