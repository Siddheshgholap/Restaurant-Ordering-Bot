
import os
import csv
import json
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="The Urban Spoon",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown("""
<style>
.stApp {
    background-color: #F8F7F4;
}

[data-testid="stSidebar"] {
    background-color: #242424;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.main .block-container {
    max-width: 1150px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    background: linear-gradient(120deg, #252525, #45403B);
    padding: 38px;
    border-radius: 16px;
    margin-bottom: 25px;
}

.hero .welcome {
    color: #D88760 !important;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 2px;
}

.hero h1 {
    color: white !important;
    font-size: 40px;
}

.hero p {
    color: #E5DED5 !important;
}

.section-heading {
    color: #292929 !important;
    font-size: 25px;
    font-weight: bold;
    margin-top: 25px;
    margin-bottom: 15px;
}

[data-testid="stMetric"] {
    background: white;
    border: 1px solid #EAE6DF;
    border-radius: 12px;
    padding: 16px;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricLabel"] *,
[data-testid="stMetricValue"] * {
    color: #292929 !important;
}

.menu-card {
    background: white;
    border: 1px solid #EAE6DF;
    border-radius: 12px;
    padding: 20px;
    min-height: 130px;
    margin-bottom: 15px;
}

.menu-card h4 {
    color: #292929 !important;
}

.menu-card p {
    color: #666666 !important;
}

.menu-card .price {
    color: #B45B36 !important;
    font-weight: bold;
    font-size: 18px;
}

[data-testid="stChatMessage"] {
    background-color: white;
    border: 1px solid #EAE6DF;
    border-radius: 12px;
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li {
    color: #292929 !important;
}

.stChatInput textarea {
    color: #292929 !important;
    background: white !important;
}

.stButton button {
    border-radius: 9px;
    min-height: 42px;
    border: 1px solid #B45B36;
}

.stButton button[kind="primary"] {
    background: #B45B36;
    color: white;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# GROQ INITIALIZATION
# =====================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("Groq API key not found. Check your .env file.")
    st.stop()

client = Groq(api_key=api_key)


# =====================================================
# LOAD MENU
# =====================================================

menu = {}
menu_categories = {}

try:
    with open("menu.csv", "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not {"item_name", "price"}.issubset(reader.fieldnames or []):
            st.error("Invalid menu.csv headers.")
            st.stop()

        for row in reader:
            name = row["item_name"].strip()
            price = int(row["price"])
            category = row.get("category", "Other").strip()

            if name and price >= 0:
                menu[name] = price
                menu_categories[name] = category

except (FileNotFoundError, ValueError, KeyError):
    st.error("Unable to load menu.csv. Check the file.")
    st.stop()

if not menu:
    st.error("Restaurant menu is empty.")
    st.stop()


# =====================================================
# SESSION STATE
# =====================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_order" not in st.session_state:
    st.session_state.pending_order = None

if "confirmed" not in st.session_state:
    st.session_state.confirmed = False


# =====================================================
# AI CHATBOT
# =====================================================

def get_ai_response(user_input):

    system_prompt = f"""
You are the friendly AI restaurant assistant for The Urban Spoon.

AVAILABLE MENU AND PRICES:
{json.dumps(menu, indent=2)}

MENU CATEGORIES:
{json.dumps(menu_categories, indent=2)}

You must understand normal customer conversations as well as
food orders.

YOUR TASKS:

1. GREETINGS:
If the customer says hello, hi, good morning, etc.,
respond politely and ask how you can help.

2. MENU QUESTIONS:
Answer questions about available food items, categories
and prices using ONLY the provided menu.

3. FOOD ORDERS:
Identify food items and quantities from the customer's message.
Only use exact item names from the available menu.

4. UNAVAILABLE ITEMS:
If the customer requests food that is not in the menu,
put it in unavailable_items.

5. FOLLOW-UP ORDERS:
Use recent conversation history to understand messages
such as "add one burger" or "make it two".

6. GENERAL QUESTIONS:
Politely answer simple restaurant-related questions.
Do not invent restaurant details.

7. PRICES:
Never calculate the bill. Python will calculate it.

8. If the message is not an order, return empty items
and unavailable_items.

IMPORTANT:
- Never invent menu items or prices.
- Never claim an order is confirmed.
- Do not treat a greeting as a food order.
- Keep your response friendly and concise.
- Return valid JSON only.

REQUIRED JSON FORMAT:

{{
    "reply": "Your conversational response",
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

    # Include recent conversation for follow-up understanding.
    conversation = [
        {"role": "system", "content": system_prompt}
    ]

    for message in st.session_state.messages[-6:]:
        if message["role"] in ["user", "assistant"]:
            conversation.append({
                "role": message["role"],
                "content": message["content"]
            })

    conversation.append({
        "role": "user",
        "content": user_input
    })

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=conversation,
        response_format={"type": "json_object"},
        max_completion_tokens=500
    )

    return json.loads(response.choices[0].message.content)


# =====================================================
# BILL CALCULATION
# =====================================================

def calculate_bill(items, unavailable):

    if not isinstance(items, list):
        raise ValueError("Invalid item response.")

    if not isinstance(unavailable, list):
        raise ValueError("Invalid unavailable item response.")

    if not all(isinstance(x, str) for x in unavailable):
        raise ValueError("Invalid unavailable item.")

    bill_items = []
    total = 0

    for item in items:

        if not isinstance(item, dict):
            raise ValueError("Invalid item format.")

        name = item.get("item_name")
        quantity = item.get("quantity")

        if not isinstance(name, str) or name not in menu:
            raise ValueError("Invalid menu item detected.")

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

    return bill_items, total


# =====================================================
# ORDER SUMMARY
# =====================================================

def create_order_summary(items, total, unavailable):

    message = "Here is your order summary:\n\n"

    for item in items:
        message += (
            f"- {item['item_name']} x {item['quantity']} "
            f"= Rs. {item['subtotal']}\n"
        )

    if unavailable:
        message += (
            "\nUnavailable items: "
            + ", ".join(unavailable)
            + "\n"
        )

    message += f"\n**Total Amount: Rs. {total}**"
    message += "\n\nWould you like to confirm your order?"

    return message


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.markdown("# THE URBAN SPOON")
    st.caption("RESTAURANT & CAFE")

    st.divider()

    st.markdown("### Navigation")
    st.markdown("Home")
    st.markdown("Our Menu")
    st.markdown("AI Order Assistant")

    st.divider()

    st.markdown("### Restaurant")
    st.write("Fresh food. Simple ordering.")
    st.write("AI-powered ordering assistant")

    st.divider()

    st.caption("Powered by Python, Streamlit & Groq")


# =====================================================
# HERO SECTION
# =====================================================

st.markdown("""
<div class="hero">
    <p class="welcome">WELCOME TO</p>
    <h1>The Urban Spoon</h1>
    <p>
        Delicious food, simple ordering.
        Chat with our AI assistant and get your bill instantly.
    </p>
</div>
""", unsafe_allow_html=True)


# =====================================================
# STATISTICS
# =====================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Menu Items", len(menu))

with col2:
    st.metric("Food Categories", len(set(menu_categories.values())))

with col3:
    st.metric("Ordering", "AI Powered")


# =====================================================
# MENU DISPLAY
# =====================================================

st.markdown(
    '<div class="section-heading">Explore Our Menu</div>',
    unsafe_allow_html=True
)

categories = ["All"] + sorted(set(menu_categories.values()))

selected_category = st.selectbox(
    "Filter menu by category",
    categories
)

filtered_items = [
    (name, price)
    for name, price in menu.items()
    if selected_category == "All"
    or menu_categories[name] == selected_category
]

menu_columns = st.columns(3)

for index, (name, price) in enumerate(filtered_items):

    with menu_columns[index % 3]:

        st.markdown(f"""
        <div class="menu-card">
            <p>{menu_categories[name]}</p>
            <h4>{name}</h4>
            <p class="price">Rs. {price}</p>
        </div>
        """, unsafe_allow_html=True)


# =====================================================
# CHATBOT INTERFACE
# =====================================================

st.divider()

st.markdown(
    '<div class="section-heading">Chat With Our AI Assistant</div>',
    unsafe_allow_html=True
)

st.write(
    "Ask about our menu, food prices or place your order below."
)

if not st.session_state.messages:

    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "Welcome to The Urban Spoon! "
            "How can I help you today? "
            "You can ask about our menu or place an order."
        )
    })


# Display chat history

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Customer input

user_input = st.chat_input("Type your message here...")


# =====================================================
# PROCESS CUSTOMER MESSAGE
# =====================================================

if user_input:

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.spinner("Assistant is thinking..."):

        try:

            result = get_ai_response(user_input)

            if not isinstance(result, dict):
                raise ValueError("Invalid AI response.")

            items = result.get("items", [])
            unavailable = result.get("unavailable_items", [])
            reply = result.get("reply", "How else can I help you?")

            if not isinstance(reply, str):
                raise ValueError("Invalid assistant response.")

            bill_items, total = calculate_bill(items, unavailable)

            if bill_items:

                st.session_state.pending_order = {
                    "items": bill_items,
                    "total": total,
                    "unavailable": unavailable
                }

                st.session_state.confirmed = False

                assistant_message = create_order_summary(
                    bill_items,
                    total,
                    unavailable
                )

            elif unavailable:

                assistant_message = (
                    reply
                    + "\n\nUnavailable items: "
                    + ", ".join(unavailable)
                )

            else:

                assistant_message = reply

            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_message
            })

        except Exception as e:

            st.session_state.messages.append({
                "role": "assistant",
                "content": (
                    "Sorry, I couldn't process that message. "
                    "Please try again. Error: " + str(e)
                )
            })

    st.rerun()


# =====================================================
# ORDER CONFIRMATION
# =====================================================

pending = st.session_state.pending_order

if pending:

    st.divider()

    st.markdown(
        '<div class="section-heading">Your Order Summary</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):

        st.markdown("### Bill Details")

        for item in pending["items"]:

            col1, col2, col3 = st.columns([3, 1, 2])

            col1.write(item["item_name"])
            col2.write(item["quantity"])
            col3.write(f"Rs. {item['subtotal']}")

        if pending["unavailable"]:
            st.warning(
                "Unavailable: "
                + ", ".join(pending["unavailable"])
            )

        st.divider()

        st.markdown(f"## Total: Rs. {pending['total']}")

    if not st.session_state.confirmed:

        st.info("Please confirm or cancel your order.")

        confirm_col, cancel_col = st.columns(2)

        with confirm_col:

            if st.button(
                "Confirm Order",
                type="primary",
                use_container_width=True
            ):

                st.session_state.confirmed = True

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": (
                        "Your order has been confirmed! "
                        "Thank you for ordering with The Urban Spoon."
                    )
                })

                st.rerun()

        with cancel_col:

            if st.button(
                "Cancel Order",
                use_container_width=True
            ):

                st.session_state.pending_order = None
                st.session_state.confirmed = False

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": (
                        "Your order has been cancelled. "
                        "You can place another order whenever you like."
                    )
                })

                st.rerun()

    else:

        st.success("Your order has been confirmed!")

        st.metric("Final Amount", f"Rs. {pending['total']}")

        if st.button("Place New Order", use_container_width=True):

            st.session_state.pending_order = None
            st.session_state.confirmed = False

            st.session_state.messages.append({
                "role": "assistant",
                "content": "What would you like to order next?"
            })

            st.rerun()


# =====================================================
# FOOTER
# =====================================================

st.divider()

st.markdown("""
<p style="text-align:center;color:#777777;">
The Urban Spoon | AI-Powered Restaurant Ordering System
</p>
""", unsafe_allow_html=True)
