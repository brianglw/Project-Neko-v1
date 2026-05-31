from typing import List, Any, Optional
from ollama import Client
from dotenv import load_dotenv
import os

load_dotenv()
PORT = os.getenv('PORT')

#LIMIT VARS
WORD_LIMIT = 120
SUMMARY_WORD_LIMIT=500
MSG_LIMIT=8
SILENCE_TIMEOUT = 3.0
MIC_THRESHOLD = 500

class Bot: 
    def __init__(self : "Bot", model : str, assistant_model : str):
        self.model : str = model
        self.assistant_model = assistant_model
        self.client = Client(
            host=PORT,
        )

    def chat(self : "Bot", history : dict):
        try: 
            complete_response = "" 
            # if (len(history['list']) > MSG_LIMIT):
            #     self.summarize_history()
            # entry = {'role': 'user', 'content': history}

            response = self.client.chat(
                model=self.model,
                messages=history['list'][:-MSG_LIMIT],
                stream=True
            )
            for chunk in response:
                content = chunk['message']['content']
                complete_response += content
                print(content, end='', flush=True)
                
            complete_response = {"role": "assistant", "content": complete_response}
            print(complete_response)  # Add final newline
            #complete_response = self.removeUnwantedChars(complete_response)
            #self.text_to_speech(complete_response, 'af_bella,af_heart')
            return complete_response
        
        except Exception as e:
            print(f"Error during chat: {e}")

Base_LLM = Bot( "shoyu_v1", "shoyu_stm")