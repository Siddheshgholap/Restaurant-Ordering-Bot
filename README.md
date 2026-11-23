# Restaurant Ordering Bot

An AI-powered restaurant ordering chatbot built using Python, Streamlit, and Groq LLM.

## Project Overview

The Restaurant Ordering Bot allows customers to place food orders using natural language. The system understands the customer's request, extracts food items and quantities using an LLM, calculates the bill using Python, and asks the customer to confirm the order.

## Features

- Displays the restaurant menu with prices.
- Understands orders written in natural language.
- Extracts food items and quantities using Groq LLM.
- Identifies unavailable menu items.
- Calculates item-wise prices and the total bill.
- Allows customers to confirm or cancel orders.
- Provides an interactive Streamlit interface.

## Technologies Used

- Python
- Streamlit
- Groq API
- Large Language Model (LLM)
- CSV
- JSON

## Project Structure

```text
Restaurant-Ordering-Bot/
│
├── app.py
├── menu.csv
├── requirements.txt
├── .gitignore
├── README.md
└── .env
```

**Note:** The `.env` file contains the API key and must not be uploaded to GitHub.

## Installation and Setup

1. Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_LINK
```

2. Navigate to the project folder:

```bash
cd Restaurant-Ordering-Bot
```

3. Create and activate a virtual environment (optional but recommended).

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Create a `.env` file in the project folder and add your Groq API key:

```text
GROQ_API_KEY=your_api_key_here
```

6. Run the application:

```bash
streamlit run app.py
```

## How It Works

1. The customer enters an order in natural language.
2. The Groq LLM extracts the requested food items and quantities in JSON format.
3. Python validates the extracted items against the restaurant menu.
4. Python calculates the item-wise subtotal and final bill.
5. The customer can confirm or cancel the order.

## Future Scope

- Database integration for storing orders.
- Order history and customer management.
- Payment gateway integration.
- Restaurant staff dashboard.

## Author

Developed as an academic mini-project.
