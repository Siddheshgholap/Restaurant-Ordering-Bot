import csv

menu = {}

with open("menu.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)

    for row in reader:
        item_name = row["item_name"].strip()
        price = int(row["price"])

        menu[item_name] = price

print("RESTAURANT MENU")
print("-------------------------")

for item, price in menu.items():
    print(f"{item}: Rs. {price}")