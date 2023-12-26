"""
Author: Zabir Ahasan
Usage: python3 or python.exe main.py
Notes:
    - Make & activate Python environment for Windows: python -m venv env && env\Scripts\activate.bat

    - Install packages with pip install -r requirements.txt

    - Requires the ChromeDriver to be installed: ChromeDriver 119.*.*
        - ChromeDriver executable must be in the same directory as this script or in the PATH environment variable

    - .env file must be in the same directory as this script for environment variables to be loaded

    - System Version: Windows 11, Python 3.11.6
        - macOS requires the macOS version of ChromeDriver
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import sys
import pandas as pd
import os
import time
import datetime
from dotenv import load_dotenv
import logging
import requests


# Load environment variables
load_dotenv()
BASE_URL = os.getenv("BASE_URL")
NUM_PAGES = int(os.getenv("NUM_PAGES"))
DELAY = int(os.getenv("DELAY"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES"))
LOG_DIRECTORY = os.getenv("LOG_DIRECTORY")
XLSX_FILENAME = os.getenv("XLSX_FILENAME")

# local variables
ROWS_PER_FILE = 1000000


# Logging setup
def setup_logging(LOG_DIRECTORY):
    """Setup logging configuration"""
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)
        logging.info(f"Directory {LOG_DIRECTORY} created.")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%I%M%p")
    log_filename = f"{LOG_DIRECTORY}/log_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,  # Log only INFO, WARNING, ERROR, and CRITICAL levels.
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(),
        ],
    )


# XLSX file check and deletion
def check_xlsx_file(XLSX_FILENAME):
    """Check if XLSX file exists and delete it if it does"""
    if os.path.isfile(XLSX_FILENAME):
        print(f"File {XLSX_FILENAME} already exists, deleting it...")
        os.remove(XLSX_FILENAME)
        logging.info("Previous XLSX deleted. Starting new script execution.")


# Start timer
def start_timer():
    """Start timer and return start time"""
    start_time = time.time()
    logging.info("Script started")
    return start_time


# Initialize Chrome WebDriver
def init_webdriver():
    """Initialize Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


# Function to extract vehicle data
def extract_vehicle_data(vehicle_element):
    """Extracts vehicle data"""
    ref_no = "Unknown"
    try:
        title_element = WebDriverWait(vehicle_element, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".make-model a"))
        )
        title = title_element.text.strip()

        # strip year from title
        title = title.split(" ")[1] + " " + title.split(" ")[2]
        title = title if title else ""

        # extract link
        link = title_element.get_attribute("href")
        link = link if link else ""

        ref_no_element = WebDriverWait(vehicle_element, 2).until(
            EC.presence_of_element_located((By.CLASS_NAME, "veh-stock-no"))
        )
        ref_no = ref_no_element.text.strip().replace("Ref No. ", "")[:8]

        mileage_element = vehicle_element.find_element(
            By.CSS_SELECTOR, ".mileage p.val"
        )
        mileage = mileage_element.text.strip()
        mileage = mileage.replace("km", "")
        mileage = mileage.replace(",", "")
        mileage = mileage if mileage else ""

        year_element = vehicle_element.find_element(By.CSS_SELECTOR, ".year p.val")
        year = year_element.text.strip()[:4].replace(",", "")
        year = year if year else ""

        # Skip vehicles with a year greater than 2010
        # if year.isdigit() and int(year) > 2010:
        #     return None

        engine_element = vehicle_element.find_element(By.CSS_SELECTOR, ".engine p.val")
        engine_size = engine_element.text.strip().replace("cc", "").replace(",", "")
        engine_size = int(engine_size) if engine_size.isdigit() else ""

        transmission_element = vehicle_element.find_element(
            By.CSS_SELECTOR, ".trans p.val"
        )
        transmission = transmission_element.text.strip()
        transmission = transmission if transmission else ""

        location_element = vehicle_element.find_element(
            By.CSS_SELECTOR, "p.val.stock-area"
        )

        location = location_element.text.strip()
        location = location if location else ""

        specs_table = vehicle_element.find_element(By.CLASS_NAME, "table-detailed-spec")
        table_rows = specs_table.find_elements(By.TAG_NAME, "tr")
        engine_code = (
            table_rows[1].find_elements(By.TAG_NAME, "td")[1].text.strip()
            if len(table_rows) >= 2
            else ""
        )
        if engine_code == "0":
            engine_code = ""

        colour = (
            table_rows[2].find_elements(By.TAG_NAME, "td")[3].text.strip()
            if len(table_rows) >= 4
            else ""
        )

        model_code = (
            table_rows[2].find_elements(By.TAG_NAME, "td")[1].text.strip()
            if len(table_rows) >= 3
            else ""
        )

        steering = (
            table_rows[1].find_elements(By.TAG_NAME, "td")[3].text.strip()
            if len(table_rows) >= 4
            else ""
        )

        seat_element = vehicle_element.find_element(
            By.CSS_SELECTOR, "td.td-4th"
        ).text.strip()

        seats = seat_element if seat_element else ""

        if seats == "ASK":
            seats = ""

        drive = (
            table_rows[2].find_elements(By.TAG_NAME, "td")[5].text.strip()
            if len(table_rows) >= 3
            else ""
        )

        doors = (
            table_rows[2].find_elements(By.TAG_NAME, "td")[7].text.strip()
            if len(table_rows) >= 3
            else ""
        )

        if doors == "ASK":
            doors = ""

        auc_table = vehicle_element.find_element(
            By.CSS_SELECTOR, ".table-detailed-spec"
        )
        auc_rows = auc_table.find_elements(By.TAG_NAME, "tr")

        auction_grade = (
            auc_rows[-1].find_elements(By.TAG_NAME, "td")[1].text.strip()
            if len(auc_rows) >= 4
            else ""
        )

        fuel_element = vehicle_element.find_element(
            By.CSS_SELECTOR, "td.td-3rd"
        ).text.strip()

        fuel = fuel_element if fuel_element else ""

        fuel_mapping = {
            "Hybrid(Petrol)": "Petrol",
            "Hybrid(Diesel)": "Diesel",
            "Electric": "Electric",
            "Other": "",
            "LPG": "Petrol",
            "CNG": "CNG",
        }

        fuel = fuel_mapping.get(fuel, fuel)

        price_element = WebDriverWait(vehicle_element, 1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "p.total-price"))
        )

        price_element = vehicle_element.find_element(By.CSS_SELECTOR, "p.total-price")
        price = price_element.text.strip()

        if "SOLD" in price.upper() or "UNDER OFFER" in price.upper():
            logging.info(
                f"Vehicle {ref_no} has been sold or is under offer, skipping..."
            )
            return None

        price = price.replace("$", "").replace(",", "")

        if price == "ASK":
            logging.info(f"Vehicle {ref_no} has no price, skipping...")
            return None

        price = round(float(price), 2)

        return {
            "Ref No": ref_no,
            "Year": year,
            "Title": title,
            "Mileage": mileage,
            "Engine Size": engine_size,
            "Engine Code": engine_code,
            "Model Code": model_code,
            "Transmission": transmission,
            "Drive": drive,
            "Steering": steering,
            "Doors": doors,
            "Seats": seats,
            "Fuel Type": fuel,
            "Auction Grade": auction_grade,
            "Total Price": price,
            "Link": link,
            "Colour": colour,
            "Location": location,
        }
    except Exception:
        return None


# Function to loop through pages
def scrape_pages(
    NUM_PAGES, DELAY, MAX_RETRIES, driver, BASE_URL, XLSX_FILENAME, extract_vehicle_data
):
    """Loop through pages and scrape data"""
    all_vehicle_data = []
    seen_ref_no = set()
    successful_pages = 0

    for page_number in range(1, NUM_PAGES + 1):
        retries = 0
        time.sleep(DELAY)

        while retries < MAX_RETRIES:
            try:
                driver.get(BASE_URL.format(page_number))
                wait = WebDriverWait(driver, 120, poll_frequency=5)

                vehicle_elements = wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".stocklist-row")
                    )
                )
                for vehicle_element in vehicle_elements:
                    vehicle_data = extract_vehicle_data(vehicle_element)

                    # prevent duplicate ref_no
                    if vehicle_data and vehicle_data["Ref No"] not in seen_ref_no:
                        seen_ref_no.add(vehicle_data["Ref No"])
                        all_vehicle_data.append(vehicle_data)

                    # check if number of rows exceeds ROWS_PER_FILE
                    if len(all_vehicle_data) >= ROWS_PER_FILE:
                        df = pd.DataFrame(all_vehicle_data)
                        df.to_excel(XLSX_FILENAME, index=False)
                        logging.info(
                            f"Data saved to {XLSX_FILENAME} due to exceeding {ROWS_PER_FILE} rows per file."
                        )
                        sys.exit(0)

                successful_pages += 1
                logging.info(f"Page {page_number} processed successfully.")
                break

            except (WebDriverException, requests.exceptions.RequestException) as e:
                logging.error(f"Error on page {page_number}: {e}")
                logging.info("Refreshing page...")
                driver.refresh()
                retries += 1
                if retries == MAX_RETRIES:
                    logging.info(
                        f"Page {page_number} failed to process after {MAX_RETRIES} retries."
                    )
                    df = pd.DataFrame(all_vehicle_data)
                    df.to_excel(XLSX_FILENAME, index=False)
                    logging.info(
                        f"Data saved to {XLSX_FILENAME} due to too many failed retries."
                    )
                    sys.exit(0)

            except KeyboardInterrupt:
                df = pd.DataFrame(all_vehicle_data)
                df.to_excel(XLSX_FILENAME, index=False)
                logging.info(f"Data saved to {XLSX_FILENAME} due to KeyboardInterrupt.")
                sys.exit(0)

            except Exception as e:
                logging.error(f"Unexpected error on page {page_number}: {e}")

    logging.info("All pages have been processed.")

    # Save data to XLSX file
    if all_vehicle_data:
        df = pd.DataFrame(all_vehicle_data)
        df.reset_index(drop=True, inplace=True)
        df.to_excel(XLSX_FILENAME, index=False)

    logging.info(f"Total number of vehicles scraped: {len(all_vehicle_data)}")
    logging.info(f"Total pages to be scraped: {NUM_PAGES}")
    logging.info(f"Total pages successfully scraped: {successful_pages}")

    # Clean up
    driver.quit()
    logging.info("Script finished, scraping complete!")


if __name__ == "__main__":
    setup_logging(LOG_DIRECTORY)
    check_xlsx_file(XLSX_FILENAME)
    start_time = start_timer()
    driver = init_webdriver()
    scrape_pages(
        NUM_PAGES,
        DELAY,
        MAX_RETRIES,
        driver,
        BASE_URL,
        XLSX_FILENAME,
        extract_vehicle_data,
    )

    elapsed_time_s = time.time() - start_time
    elapsed_time_m, elapsed_time_s = divmod(int(elapsed_time_s), 60)

    time_message = (
        f"{elapsed_time_m} minutes and {elapsed_time_s} seconds"
        if elapsed_time_m
        else f"{elapsed_time_s} seconds"
    )
    logging.info(f"Time taken: {time_message}")
