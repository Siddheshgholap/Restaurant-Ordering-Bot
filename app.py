
import os
import csv
import json
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# =====================================
# 1. INITIALIZATION
# =====================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("Groq API key not found. Check your .env file.")
    st.stop()

client = Groq(api_key=api_key)

st.set_page_config(
    page_title="Restaurant Ordering Bot",
    page_icon="🍽️",
    layout="centered"
)


# =====================================
# 2. LOAD RESTAURANT MENU
# =====================================

menu = {}

try:
    with open("menu.csv", "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        required_columns = {"item_name", "price"}

        if not required_columns.issubset(reader.fieldnames or []):
            st.error("Invalid menu.csv headers.")
            st.stop()

        for row in reader:
            name = row["item_name"].strip()
            price = int(row["price"])

            if name and price >= 0:
                menu[name] = price

except (FileNotFoundError, ValueError, KeyError):
    st.error("Unable to load menu.csv. Check the file and prices.")
    st.stop()

if not menu:
    st.error("Restaurant menu is empty.")
    st.stop()


# =====================================
# 3. SESSION STATE
# =====================================

if "pending_order" not in st.session_state:
    st.session_state.pending_order = None

if "confirmed" not in st.session_state:
    st.session_state.confirmed = False


# =====================================
# 4. LLM ORDER EXTRACTION
# =====================================

def extract_order(user_input):

    system_prompt = f"""
    You are an intelligent restaurant ordering assistant.

    AVAILABLE RESTAURANT MENU:
    {json.dumps(menu, indent=2)}

    YOUR TASK:
    Understand customer messages and extract food orders.

    RULES:
    1. Identify available food items and quantities.
    2. Only use exact item names from the menu.
    3. Put unavailable requested items in unavailable_items.
    4. Never invent food items.
    5. If quantity is not mentioned, assume 1.
    6. If the customer is not placing an order,
       return empty arrays.
    7. Do not calculate prices.
    8. Return only valid JSON.

    REQUIRED JSON FORMAT:

    {{
        "items": [
            {{
                "item_name": "Margherita Pizza",
                "quantity": 2
            }}
        ],
        "unavailable_items": [
            "Chicken Burger"
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
        max_completion_tokens=400
    )

    return json.loads(response.choices[0].message.content)


# =====================================
# 5. BILL CALCULATION AND VALIDATION
# =====================================

def calculate_bill(order):

    if not isinstance(order, dict):
        raise ValueError("Invalid order response.")

    items = order.get("items")
    unavailable = order.get("unavailable_items", [])

    if not isinstance(items, list):
        raise ValueError("Invalid items format.")

    if not isinstance(unavailable, list):
        raise ValueError("Invalid unavailable items format.")

    if not items and not unavailable:
        raise ValueError("No food order detected. Please try again.")

    total = 0
    bill_items = []

    for item in items:

        if not isinstance(item, dict):
            raise ValueError("Invalid item format.")

        name = item.get("item_name")
        quantity = item.get("quantity")

        if not isinstance(name, str) or name not in menu:
            raise ValueError("An invalid menu item was detected.")

        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity < 1
            or quantity > 50
        ):
            raise ValueError(f"Invalid quantity for {name}.")

        price = menu[name]
        subtotal = price * quantity

        total += subtotal

        bill_items.append({
            "item_name": name,
            "quantity": quantity,
            "price": price,
            "subtotal": subtotal
        })

    return bill_items, total, unavailable


# =====================================
# 6. STREAMLIT USER INTERFACE
# =====================================

st.title("Restaurant Ordering Bot")

st.write(
    "Welcome! Order your favourite food "
    "using our AI-powered restaurant assistant."
)

st.divider()

# Display menu
st.header("Our Restaurant Menu")

for item, price in menu.items():
    st.write(f"**{item}** — Rs. {price}")

st.divider()


# =====================================
# 7. CUSTOMER ORDER INPUT
# =====================================

st.header("Place Your Order")

user_input = st.text_input(
    "What would you like to order?",
    placeholder="Example: 2 Margherita pizzas and 1 Veg Burger"
)

if st.button("Generate Bill", use_container_width=True):

    st.session_state.pending_order = None
    st.session_state.confirmed = False

    if not user_input.strip():

        st.warning("Please enter your order.")

    else:

        with st.spinner("Understanding your order..."):

            try:

                order = extract_order(user_input)

                bill_items, total, unavailable = calculate_bill(order)

                st.session_state.pending_order = {
                    "items": bill_items,
                    "total": total,
                    "unavailable": unavailable
                }

            except (ValueError, TypeError, KeyError) as e:

                st.error(str(e))

            except Exception as e:

                st.error(f"Unable to process your order: {e}")


# =====================================
# 8. DISPLAY GENERATED BILL
# =====================================

pending = st.session_state.pending_order

if pending:

    st.divider()

    st.header("Order Summary")

    if pending["unavailable"]:

        st.warning(
            "Unavailable items: "
            + ", ".join(str(x) for x in pending["unavailable"])
        )

    if pending["items"]:

        st.subheader("Your Bill")

        for item in pending["items"]:

            st.write(
                f'**{item["item_name"]}** '
                f'x {item["quantity"]} '
                f'= Rs. {item["subtotal"]}'
            )

        st.divider()

        st.subheader(f'Total Amount: Rs. {pending["total"]}')

        # =====================================
        # 9. ORDER CONFIRMATION
        # =====================================

        if not st.session_state.confirmed:

            st.write("Please confirm your order.")

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Confirm Order",
                    use_container_width=True
                ):

                    st.session_state.confirmed = True
                    st.rerun()

            with col2:

                if st.button(
                    "Cancel Order",
                    use_container_width=True
                ):

                    st.session_state.pending_order = None
                    st.session_state.confirmed = False
                    st.rerun()

        else:

            st.success("Your order has been confirmed!")

            st.write("Thank you for ordering with us.")

            st.write(
                f'Final Amount: Rs. {pending["total"]}'
            )

            if st.button("Place New Order"):

                st.session_state.pending_order = None
                st.session_state.confirmed = False
                st.rerun()

    else:

        st.info("No available items to bill. Please try another order.")
