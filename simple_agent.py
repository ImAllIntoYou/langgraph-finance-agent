import os 
from dotenv import load_dotenv

from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")


llm_name = "gpt-3.5-turbo"

client = OpenAI(api_key=openai_key)

response = client.chat.completions.create(
    model=llm_name,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "who is Nelson Mandela?"},
    ],
)
print(response.choices[0].message.content)

# Create our own agent
class Agent:
    def __init__(self, system=""):
        self.system = system
        self.messages = []
        if system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result
    
    def execute(self):
        response = client.chat.completions.create(
            model=llm_name,
            temperature=0.0,
            messages=self.messages,
        )
        return response.choices[0].message.content