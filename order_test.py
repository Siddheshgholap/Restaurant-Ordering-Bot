
import os
import csv
import json
from dotenv import load_dotenv
from groq import Groq

# Load API key
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load restaurant menu
menu = {}

with open("menu.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)

    for row in reader:
        menu[row["item_name"]] = int(row["price"])

# System prompt
system_prompt = f"""
You are a restaurant ordering assistant.

Here is the restaurant menu with prices:

{json.dumps(menu, indent=2)}

Your task:
1. Understand the customer's food order.
2. Identify the food items and quantities.
3. Only select items available in the menu.
4. If quantity is not mentioned, assume quantity is 1.
5. Do not invent food items.
6. Return ONLY valid JSON in this format:

{{
    "items": [
        {{
            "item_name": "Margherita Pizza",
            "quantity": 2
        }}
    ]
}}
"""

# Get customer order
user_input = input("Enter your order: ")

# Call Groq API
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ],
    max_completion_tokens=300,
    response_format={"type": "json_object"}
)

# Extract JSON response
result = json.loads(response.choices[0].message.content)

print("\nExtracted Order:")
print(json.dumps(result, indent=4))
