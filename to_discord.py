from dotenv import load_dotenv
import os
import requests
import json

# import pandas as pd
import time
import sqlite3


# Load environment variables
load_dotenv()
# XLSX_FILENAME = os.getenv("XLSX_FILENAME")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
# DB_FILE = "vehicles.db"
DB_FILE = os.getenv("DB_FILE")


# df = pd.read_excel(XLSX_FILENAME)


def meets_requirements(vehicle):
    titles = ["TOYOTA", "LEXUS", "HONDA", "NISSAN", "SUBARU"]
    # max_year = 2009
    max_year = 2020
    max_mileage = 180000
    max_price = 20000
    transmission = ["AT", "CVT"]
    fuel_type = ["Petrol"]
    auction_grade = ["3", "3.5", "4"]
    location_jpn = ["Kobe", "Osaka", "Tokyo", "Nagoya", "Yokohama", "Fukuoka"]

    result = (
        any(title in vehicle["Title"] for title in titles)
        and int(vehicle["Mileage"]) <= max_mileage  # Convert to int
        and int(vehicle["Year"]) <= max_year  # Convert to int
        and vehicle["Transmission"] in transmission
        and vehicle["Fuel Type"] in fuel_type
        and vehicle["Auction Grade"] in auction_grade
        and vehicle["Location"] in location_jpn
        and int(vehicle["Year"]) <= max_year  # Convert to int
        and int(vehicle["Total Price"]) <= max_price  # Convert to int
    )
    return result


def send_to_discord(content, message):
    # data = {"content": f"{message} \U0001F473\n{content}"}
    data = {"content": f"{message}\n{content}"}
    response = requests.post(
        DISCORD_WEBHOOK_URL,
        data=json.dumps(data),
        headers={"Content-Type": "application/json"},
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print("Payload delivered successfully, code {}.".format(response.status_code))


# Remove this line if you want to send more than one link
# link_sent = 0
# delay = 3


# Establish a connection to the database
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Query the database for vehicle data
# cursor.execute("SELECT * FROM vehicles")  # Adjust the query as needed
cursor.execute("SELECT * FROM vehicles WHERE sent_to_discord = 0")
vehicles = cursor.fetchall()

links = []


# for _, vehicle in df.iterrows():
#     if meets_requirements(vehicle):
#         # send_to_discord(vehicle["Link"], "Helo Sir, I found a car you might like")
#         # Remove these 3 lines if you want to send more than one link
#         # link_sent += 1
#         # time.sleep(delay)
#         # if link_sent >= 5:
#         #     break
#         links.append(vehicle["Link"])
#         if len(links) >= 6:
#             break


# links_str = "\n".join(links)
# send_to_discord(links_str, "Helo Sir, I found some cars you might like:")

for vehicle in vehicles:
    vehicle_dict = {
        "Title": vehicle[2],
        "Mileage": vehicle[3],
        "Year": vehicle[1],
        "Transmission": vehicle[7],
        "Fuel Type": vehicle[12],
        "Auction Grade": vehicle[13],
        "Total Price": vehicle[14],
        "Location": vehicle[17],
        "Link": vehicle[15],
    }

    if meets_requirements(vehicle_dict):
        links.append(vehicle_dict["Link"])
        if len(links) >= 6:
            break

# conn.close()

if links:
    links_str = "\n".join(links)
    send_to_discord(links_str, "Helo Sir, I found some cars you might like:")

    # Update the sent_to_discord flag
    for link in links:
        cursor.execute(
            "UPDATE vehicles SET sent_to_discord = 1 WHERE link = ?", (link,)
        )

    conn.commit()

else:
    # If no links are found, send a different message to Discord
    send_to_discord(
        "There are no more links to send that meet the requirements.", "Update:"
    )

conn.close()
