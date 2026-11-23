
import os
from dotenv import load_dotenv
from groq import Groq

# Load API key
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file!")

# Initialize Groq
client = Groq(api_key=api_key)

# Test API connection
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": "Introduce yourself in one sentence."
        }
    ],
    max_completion_tokens=150
)

print("Groq API Connected Successfully!")
print(response.choices[0].message.content)
