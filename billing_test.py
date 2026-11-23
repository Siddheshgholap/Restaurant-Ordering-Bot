
import csv
import json

# Load menu
menu = {}

with open("menu.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)

    for row in reader:
        menu[row["item_name"]] = int(row["price"])


# Sample LLM JSON response
order_json = {
    "items": [
        {
            "item_name": "Margherita Pizza",
            "quantity": 2
        },
        {
            "item_name": "Veg Burger",
            "quantity": 1
        }
    ]
}

# Calculate bill
total = 0

print("\n========== RESTAURANT BILL ==========")

for item in order_json["items"]:

    name = item["item_name"]
    quantity = item["quantity"]

    if name in menu:
        price = menu[name]
        subtotal = price * quantity
        total += subtotal

        print(f"{name} x {quantity} = Rs. {subtotal}")

    else:
        print(f"{name} is not available!")

print("------------------------------------")
print(f"TOTAL BILL: Rs. {total}")
print("====================================")
