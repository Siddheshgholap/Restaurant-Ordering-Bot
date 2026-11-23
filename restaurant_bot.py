
import os
import csv
import json
from dotenv import load_dotenv
from groq import Groq

# Initialize Groq
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load restaurant menu
menu = {}

with open("menu.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)

    for row in reader:
        menu[row["item_name"]] = int(row["price"])


# Display menu
def show_menu():
    print("\n========== RESTAURANT MENU ==========")

    for item, price in menu.items():
        print(f"{item}: Rs. {price}")

    print("====================================")


# Extract customer order using LLM
def extract_order(user_input):

    system_prompt = f"""
    You are a restaurant ordering assistant.

    Available menu:
    {json.dumps(menu, indent=2)}

    Extract food items and quantities from the customer's message.

    Rules:
    1. Only select items from the menu.
    2. Default quantity is 1.
    3. Never invent items.
    4. Return only valid JSON.

    Format:
    {{
        "items": [
            {{
                "item_name": "Margherita Pizza",
                "quantity": 2
            }}
        ]
    }}
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        response_format={"type": "json_object"},
        max_completion_tokens=300
    )

    return json.loads(response.choices[0].message.content)


# Calculate bill
def calculate_bill(order):

    total = 0
    valid_items = []

    print("\n========== YOUR BILL ==========")

    for item in order["items"]:

        name = item["item_name"]
        quantity = item["quantity"]

        if name in menu and isinstance(quantity, int) and not isinstance(quantity, bool) and 1 <= quantity <= 50:

            price = menu[name]
            subtotal = price * quantity
            total += subtotal

            valid_items.append(item)

            print(f"{name} x {quantity} = Rs. {subtotal}")

        else:
            print(f"Invalid item or quantity: {name}")

    print("--------------------------------")
    print(f"TOTAL: Rs. {total}")
    print("================================")

    return total, valid_items


# Main application
print("\nWELCOME TO OUR RESTAURANT!")

show_menu()

customer_order = input("\nWhat would you like to order? ")

try:
    order = extract_order(customer_order)

    total, valid_items = calculate_bill(order)

    if valid_items:
        confirmation = input("\nConfirm your order? (yes/no): ")

        if confirmation.lower() == "yes":
            print("\nYour order has been confirmed!")
            print(f"Amount to pay: Rs. {total}")
        else:
            print("\nYour order has been cancelled.")

    else:
        print("\nNo valid items found. Please try again.")

except (ValueError, KeyError, TypeError):
    print("\nSorry, we couldn't process your order. Please try again.")
