
import os
import csv
import json
import html
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="The Urban Spoon",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================================================
# CUSTOM CSS
# ==================================================

st.markdown("""
<style>

/* MAIN BACKGROUND */

.stApp,
[data-testid="stAppViewContainer"] {
    background-color: #F8F7F4;
}

/* FORCE DARK TEXT THROUGHOUT MAIN CONTENT */

[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] p,
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] h1,
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] h2,
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] h3,
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] h4,
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] li,
[data-testid="stAppViewContainer"] .main label,
[data-testid="stAppViewContainer"] .main [data-testid="stWidgetLabel"] {
    color: #292929 !important;
}

/* PAGE WIDTH */

.main .block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background-color: #242424;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

/* HERO SECTION */

.hero {
    background: linear-gradient(120deg, #252525, #45403B);
    padding: 42px;
    border-radius: 18px;
    margin-bottom: 28px;
}

.hero .welcome {
    color: #D88760 !important;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 2px;
}

.hero h1 {
    color: #FFFFFF !important;
    font-size: 42px;
    margin: 15px 0;
}

.hero p {
    color: #E5DED5 !important;
    font-size: 16px;
}

/* SECTION HEADINGS */

.section-heading {
    font-size: 27px;
    font-weight: 700;
    color: #292929 !important;
    margin: 28px 0 15px;
}

/* METRIC CARDS */

[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #EAE6DF;
    border-radius: 13px;
    padding: 18px;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] *,
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] * {
    color: #292929 !important;
}

/* MENU CARDS */

.menu-card {
    background: #FFFFFF;
    border: 1px solid #EAE6DF;
    border-radius: 14px;
    padding: 22px;
    min-height: 135px;
    margin-bottom: 15px;
}

.menu-card h4 {
    color: #292929 !important;
    font-size: 17px;
    margin: 8px 0;
}

.menu-card .category {
    color: #777777 !important;
    font-size: 13px;
}

.menu-card .price {
    color: #B45B36 !important;
    font-size: 18px;
    font-weight: bold;
}

/* INPUTS */

.stSelectbox label,
.stTextArea label {
    color: #292929 !important;
}

.stTextArea textarea {
    background-color: #FFFFFF !important;
    color: #292929 !important;
    border: 1px solid #D9D3CA !important;
}

.stTextArea textarea::placeholder {
    color: #888888 !important;
}

.stSelectbox div[data-baseweb="select"] {
    background-color: #FFFFFF;
}

/* ORDER SUMMARY CONTAINER */

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border-color: #EAE6DF !important;
    border-radius: 14px;
}

/* BILL TEXT - HIGH CONTRAST */

[data-testid="stAppViewContainer"] .main [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] p,
[data-testid="stAppViewContainer"] .main [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stAppViewContainer"] .main [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stAppViewContainer"] .main [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h3,
[data-testid="stAppViewContainer"] .main [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] strong {
    color: #292929 !important;
}

/* ORDER ITEM TEXT */

[data-testid="stAppViewContainer"] .main [data-testid="stVerticalBlockBorderWrapper"] p {
    color: #292929 !important;
}

/* SUCCESS MESSAGE */

[data-testid="stAlert"] p {
    color: inherit !important;
}

/* BUTTONS */

div.stButton > button {
    border-radius: 9px;
    min-height: 44px;
    font-weight: 600;
    border: 1px solid #B45B36;
}

div.stButton > button[kind="primary"] {
    background-color: #B45B36;
    color: #FFFFFF;
}

/* FOOTER */

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# GROQ INITIALIZATION
# ==================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("Groq API key not found. Check your .env file.")
    st.stop()

client = Groq(api_key=api_key)


# ==================================================
# LOAD RESTAURANT MENU
# ==================================================

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
    st.error("Unable to load menu.csv. Check your menu file.")
    st.stop()

if not menu:
    st.error("Restaurant menu is empty.")
    st.stop()


# ==================================================
# SESSION STATE
# ==================================================

if "pending_order" not in st.session_state:
    st.session_state.pending_order = None

if "confirmed" not in st.session_state:
    st.session_state.confirmed = False


# ==================================================
# AI ORDER EXTRACTION
# ==================================================

def extract_order(user_input):

    system_prompt = f"""
You are an intelligent restaurant ordering assistant.

AVAILABLE MENU:
{json.dumps(menu, indent=2)}

RULES:
1. Identify food items and quantities.
2. Only use exact menu item names.
3. Put unavailable items in unavailable_items.
4. Never invent food items.
5. Assume quantity 1 if not mentioned.
6. If no order is detected, return empty arrays.
7. Do not calculate prices.
8. Return valid JSON only.

FORMAT:
{{
    "items": [
        {{
            "item_name": "Margherita Pizza",
            "quantity": 2
        }}
    ],
    "unavailable_items": ["Chicken Burger"]
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


# ==================================================
# BILL CALCULATION
# ==================================================

def calculate_bill(order):

    if not isinstance(order, dict):
        raise ValueError("Invalid order response.")

    items = order.get("items")
    unavailable = order.get("unavailable_items", [])

    if not isinstance(items, list) or not isinstance(unavailable, list):
        raise ValueError("Invalid order format.")

    if not all(isinstance(x, str) for x in unavailable):
        raise ValueError("Invalid unavailable item response.")

    total = 0
    bill_items = []

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

    if not bill_items and not unavailable:
        raise ValueError("No food order detected. Please try again.")

    return bill_items, total, unavailable


# ==================================================
# SIDEBAR
# ==================================================

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
    st.markdown("Fresh food. Simple ordering.")
    st.markdown("AI-powered ordering assistant")

    st.divider()

    st.caption("Powered by Python, Streamlit & Groq")


# ==================================================
# HERO SECTION
# ==================================================

st.markdown("""
<div class="hero">
    <p class="welcome">WELCOME TO</p>
    <h1>The Urban Spoon</h1>
    <p>
        Delicious food, simple ordering.
        Tell our AI assistant what you would like to eat
        and get your bill instantly.
    </p>
</div>
""", unsafe_allow_html=True)


# ==================================================
# RESTAURANT STATISTICS
# ==================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Menu Items", len(menu))

with col2:
    st.metric("Food Categories", len(set(menu_categories.values())))

with col3:
    st.metric("Ordering", "AI Powered")


# ==================================================
# MENU SECTION
# ==================================================

st.markdown(
    '<div class="section-heading">Explore Our Menu</div>',
    unsafe_allow_html=True
)

st.write("Explore our dishes and choose what you would like to order.")

categories = ["All"] + sorted(set(menu_categories.values()))

selected_category = st.selectbox(
    "Filter by category",
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

        safe_name = html.escape(name)
        safe_category = html.escape(menu_categories[name])

        st.markdown(f"""
        <div class="menu-card">
            <p class="category">{safe_category}</p>
            <h4>{safe_name}</h4>
            <p class="price">Rs. {price}</p>
        </div>
        """, unsafe_allow_html=True)


# ==================================================
# AI ORDER ASSISTANT
# ==================================================

st.divider()

st.markdown(
    '<div class="section-heading">AI Order Assistant</div>',
    unsafe_allow_html=True
)

st.write(
    "Tell us what you would like to order. "
    "You can mention multiple items in one sentence."
)

with st.container(border=True):

    st.markdown("### Place Your Order")

    user_input = st.text_area(
        "Your order",
        placeholder="Example: I want 2 Margherita pizzas and 1 Veg Burger.",
        height=100,
        key="order_input"
    )

    if st.button("Generate My Bill", use_container_width=True):

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


# ==================================================
# ORDER SUMMARY
# ==================================================

pending = st.session_state.pending_order

if pending:

    st.divider()

    st.markdown(
        '<div class="section-heading">Your Order Summary</div>',
        unsafe_allow_html=True
    )

    if pending["unavailable"]:

        st.warning(
            "Unavailable items: "
            + ", ".join(pending["unavailable"])
        )

    if pending["items"]:

        with st.container(border=True):

            st.markdown("### Bill Details")

            headers = st.columns(4)

            for col, label in zip(
                headers,
                ["Item", "Quantity", "Price", "Subtotal"]
            ):
                col.markdown(f"**{label}**")

            for item in pending["items"]:

                cols = st.columns(4)

                cols[0].write(item["item_name"])
                cols[1].write(item["quantity"])
                cols[2].write(f'Rs. {item["price"]}')
                cols[3].write(f'Rs. {item["subtotal"]}')

            st.divider()

            st.markdown(
                f"""
                <h2 style="
                    text-align:right;
                    color:#B45B36 !important;
                ">
                    Total: Rs. {pending['total']}
                </h2>
                """,
                unsafe_allow_html=True
            )

        if not st.session_state.confirmed:

            st.info("Please review your bill before confirming.")

            confirm_col, cancel_col = st.columns(2)

            with confirm_col:

                if st.button(
                    "Confirm Order",
                    type="primary",
                    use_container_width=True
                ):

                    st.session_state.confirmed = True
                    st.rerun()

            with cancel_col:

                if st.button(
                    "Cancel Order",
                    use_container_width=True
                ):

                    st.session_state.pending_order = None
                    st.session_state.confirmed = False
                    st.rerun()

        else:

            st.success("Your order has been confirmed!")

            st.markdown(
                """
                <p style="color:#292929 !important;">
                    Thank you for ordering with The Urban Spoon.
                </p>
                """,
                unsafe_allow_html=True
            )

            st.metric(
                "Final Amount",
                f"Rs. {pending['total']}"
            )

            if st.button("Place New Order", use_container_width=True):

                st.session_state.pending_order = None
                st.session_state.confirmed = False
                st.rerun()

    else:

        st.info("No available items to bill. Please try another order.")


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.markdown("""
<p style="text-align:center;color:#777777 !important;">
    The Urban Spoon | AI-Powered Restaurant Ordering System
</p>
""", unsafe_allow_html=True)
