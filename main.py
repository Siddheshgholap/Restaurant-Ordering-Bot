
import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=api_key)

# Restaurant chatbot system prompt
system_prompt = """
You are a helpful Restaurant Ordering Assistant.

Your responsibilities:
1. Greet customers politely.
2. Show the restaurant menu when requested.
3. Help customers choose food.
4. Answer questions about food items.
5. Help customers place orders.
6. Confirm order details before completing an order.

Keep your responses simple, friendly and conversational.
"""

messages = [
    {"role": "system", "content": system_prompt}
]

print("\n===== RESTAURANT ORDERING BOT =====")
print("Bot: Hello! Welcome to our restaurant.")
print("Bot: How can I help you today?")
print("Type 'exit' to stop.\n")

while True:

    user_input = input("You: ")

    if user_input.lower() == "exit":
        print("Bot: Thank you for visiting!")
        break

    messages.append({
        "role": "user",
        "content": user_input
    })

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        max_completion_tokens=300
    )

    bot_reply = response.choices[0].message.content

    print("\nBot:", bot_reply, "\n")

    messages.append({
        "role": "assistant",
        "content": bot_reply
    })
