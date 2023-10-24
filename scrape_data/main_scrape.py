from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
import pandas as pd
import os
import re
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
# Base URL
base_url = os.getenv("BASE_URL")

# headless mode Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")

driver = webdriver.Chrome(options=chrome_options)


def scrape_vehicle_data(
    driver: webdriver.Chrome, num_pages_to_scarpe: int
) -> List[Dict[str, str]]:
    # scraped vehicle data
    all_vehicle_data = []

    for page_number in range(1, num_pages_to_scarpe + 1):
        url = base_url.format(page_number)

        # Open the URL in the browser
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        # Initialize list to store the scraped vehicle data for current page
        vehicle_data = []

        try:
            vehicle_elements = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".stocklist-row"))
            )

            for vehicle_element in vehicle_elements:
                # Extract data for each vehicle
                try:
                    title_element = vehicle_element.find_element(
                        By.CSS_SELECTOR, ".make-model a"
                    )
                    title = title_element.text.strip()

                    # extract hyperlink from title element
                    link = title_element.get_attribute("href")

                    # strip year from title
                    title = title.split(" ")[1] + " " + title.split(" ")[2]

                except:
                    title = "N/A"
                    link = "N/A"

                try:
                    mileage_element = vehicle_element.find_element(
                        By.CSS_SELECTOR, ".mileage p.val"
                    )
                    mileage = mileage_element.text.strip()

                    # For Scatter Plot Purposes, str -> int
                    # (KM could be Miles LOL)

                    # remove "km" from mileage column
                    mileage = mileage.replace("km", "")
                    # convert mileage to int
                    mileage = int(mileage.replace(",", ""))

                except:
                    mileage = "N/A"

                try:
                    year_element = vehicle_element.find_element(
                        By.CSS_SELECTOR, ".year p.val"
                    )
                    year = year_element.text.strip()

                    # Formatting consraints

                    # slice year column from 2004/4 -> 2004
                    year = year[:4]

                    # convert year to have no commas
                    year = year.replace(",", "")

                    # convert year to int
                    year = int(year)

                except:
                    year = "N/A"

                try:
                    engine_element = vehicle_element.find_element(
                        By.CSS_SELECTOR, ".engine p.val"
                    )
                    engine = engine_element.text.strip()
                except:
                    engine = "N/A"

                try:
                    trans_element = vehicle_element.find_element(
                        By.CSS_SELECTOR, ".trans p.val"
                    )
                    trans = trans_element.text.strip()
                except:
                    trans = "N/A"

                # Engine Code

                try:
                    table_element = vehicle_element.find_element(
                        By.CLASS_NAME, "table-detailed-spec"
                    )

                    # Find all rows within the table
                    table_rows = table_element.find_elements(By.TAG_NAME, "tr")

                    # Check if there are at least two rows (0-based indexing)
                    if len(table_rows) >= 2:
                        # Get the second <td> element (0-based indexing) from the second <tr>
                        engine_code_element = table_rows[1].find_elements(
                            By.TAG_NAME, "td"
                        )[1]
                        engine_code = engine_code_element.text.strip()
                    else:
                        engine_code = "N/A"
                except:
                    engine_code = "N/A"

                # Drive
                try:
                    # Locate the element with class "table-detailed-spec"
                    table_element = vehicle_element.find_element(
                        By.CLASS_NAME, "table-detailed-spec"
                    )

                    # Find all rows within the table
                    table_rows = table_element.find_elements(By.TAG_NAME, "tr")

                    # Check if there are at least three rows (0-based indexing)
                    if len(table_rows) >= 3:
                        # Get the sixth <td> element (0-based indexing) from the third <tr>
                        drive_element = table_rows[2].find_elements(By.TAG_NAME, "td")[
                            5
                        ]
                        drive = drive_element.text.strip()
                    else:
                        drive = "N/A"

                except:
                    drive = "N/A"

                # Auction grade
                try:
                    # Find the detailed specs table
                    specs_table = vehicle_element.find_element(
                        By.CSS_SELECTOR, ".table-detailed-spec"
                    )

                    # Find all rows in the table
                    table_rows = table_element.find_elements(By.TAG_NAME, "tr")

                    # Check if there are at least 4 rows (0-based indexing)
                    if len(table_rows) >= 4:
                        # Get the last row (0-based indexing)
                        auction_grade_element = table_rows[-1].find_elements(
                            By.TAG_NAME, "td"
                        )[1]
                        auction_grade = auction_grade_element.text.strip()
                    else:
                        auction_grade = "N/A"
                except:
                    auction_grade = "N/A"

                try:
                    fuel_element = vehicle_element.find_element(
                        By.CSS_SELECTOR, "td.td-3rd"
                    )
                    fuel = fuel_element.text.strip()
                except:
                    fuel = "N/A"

                try:
                    model_code_element = vehicle_element.find_element(
                        By.CSS_SELECTOR, "td.td-1st"
                    )
                    model_code = model_code_element.text.strip()
                except:
                    model_code = "N/A"

                try:
                    price_element = vehicle_element.find_element(
                        By.CSS_SELECTOR, "p.total-price"
                    )
                    price = price_element.text.strip()

                    # remove $ from Price column
                    # price = price.replace("$", "")
                    price = price.replace("$", "").replace(",", "")

                    # convert Price to float with 2 decimal places
                    # price = float(price.replace(",", ""))
                    # price = round(price, 2)
                    price = round(float(price), 2)

                except:
                    price = (
                        "SOLD"  # Set the price to "SOLD" if the element is not found
                    )

                    # Skip the current vehicle if the price is "SOLD"
                    continue

                # Store extracted data in a dict
                vehicle_info = {
                    "Title": title,
                    "Mileage": mileage,
                    "Year": year,
                    "Engine": engine,
                    "Trans": trans,
                    "Model Code": model_code,
                    "Fuel": fuel,
                    "Engine code": engine_code,
                    "Drive": drive,
                    "Auction grade": auction_grade,
                    "Total Price": price,
                    "Link": link,
                }

                # Append  vehicle data to list
                vehicle_data.append(vehicle_info)

            # Extend list of all scraped data with the data from current page
            all_vehicle_data.extend(vehicle_data)

        except Exception as e:
            print("An error occurred:", str(e))

    return all_vehicle_data
