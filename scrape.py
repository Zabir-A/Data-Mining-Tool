from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import os
import time
import datetime
from dotenv import load_dotenv
import logging
import requests
import sqlite3
from fake_useragent import UserAgent

# TODO:
# - Add cookie support & handling


# Load environment variables (Constants)
load_dotenv()
BASE_URL = os.getenv("BASE_URL")
NUM_PAGES = int(os.getenv("NUM_PAGES"))
DELAY = int(os.getenv("DELAY"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES"))
LOG_DIRECTORY = os.getenv("LOG_DIRECTORY")
BASE_YEAR = int(os.getenv("BASE_YEAR", 2009))  # Default to 2009 if BASE_YEAR is not set


def calculate_year_threshold(base_year, start_increment_year):
    """Calculate year threshold based on the current year and increment year threshold"""
    current_year = datetime.datetime.now().year
    if current_year >= start_increment_year:
        return base_year + (current_year - start_increment_year + 1)
    else:
        return base_year


START_INCREMENT_YEAR = (
    2024  # Change this to the year you want to start incrementing the year threshold
)

YEAR_THRESHOLD = calculate_year_threshold(BASE_YEAR, START_INCREMENT_YEAR)


# Logging setup
def setup_logging(LOG_DIRECTORY):
    """Setup logging configuration"""

    main_logs_dir = os.path.join(LOG_DIRECTORY, "main_logs")

    if not os.path.exists(main_logs_dir):
        os.makedirs(main_logs_dir, exist_ok=True)
        logging.info(f"Directory {main_logs_dir} created.")

    timestamp = datetime.datetime.now().strftime("%y-%m-%d_%I%M%p")

    log_filename = f"{main_logs_dir}/scraping_log_{timestamp}.log"  # Save logs in the main_logs subdirectory

    logging.basicConfig(
        level=logging.INFO,  # Log only INFO, WARNING, ERROR, and CRITICAL levels.
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(),
        ],
    )


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

    # chrome_options.add_argument(
    #     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
    # )

    ua = UserAgent()
    userAgent = ua.random
    chrome_options.add_argument(f"user-agent={userAgent}")

    return webdriver.Chrome(options=chrome_options)


# Database setup
def setup_database():
    """Create SQLite table if it doesn't exist"""
    conn = sqlite3.connect("vehicles.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicles (
            ref_no TEXT PRIMARY KEY,
            year INTEGER,
            title TEXT,
            mileage INTEGER,
            engine_size INTEGER,
            engine_code TEXT,
            model_code TEXT,
            transmission TEXT,
            drive TEXT,
            steering TEXT,
            doors INTEGER,
            seats INTEGER,
            fuel_type TEXT,
            auction_grade TEXT,
            total_price REAL,
            link TEXT,
            colour TEXT,
            location TEXT,
            sent_to_discord INTEGER DEFAULT 0

        )
    """
    )
    conn.commit()
    conn.close()


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

        #####################

        # Skip vehicles with a year greater than 2009
        # if year.isdigit() and int(year) > 2009:
        #     logging.info(f"Vehicle {ref_no} is from {year}, skipping...")
        #     return None

        if year.isdigit() and int(year) > YEAR_THRESHOLD:
            logging.info(f"Vehicle {ref_no} is from {year}, skipping...")
            return None

        #####################

        engine_element = vehicle_element.find_element(By.CSS_SELECTOR, ".engine p.val")
        engine_size = engine_element.text.strip().replace("cc", "").replace(",", "")

        # convert engine size to float
        engine_size = float(engine_size) if engine_size.isdigit() else ""

        # convert engine size to litres
        engine_size = engine_size / 1000

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

        # Map fuel types to standardised values
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


# Function to check if vehicle exists in database
def vehicle_exists(cursor, ref_no):
    """Check if a record with the given ref_no already exists in the database."""
    cursor.execute("SELECT 1 FROM vehicles WHERE ref_no = ?", (ref_no,))
    return cursor.fetchone() is not None


# Function to insert data into database
def insert_vehicle_data(cursor, vehicle_data):
    """Insert vehicle data into the database if it doesn't already exist."""
    if not vehicle_exists(cursor, vehicle_data["Ref No"]):
        try:
            cursor.execute(
                """
                INSERT INTO vehicles (
                    ref_no, year, title, mileage, engine_size, engine_code, 
                    model_code, transmission, drive, steering, doors, seats, 
                    fuel_type, auction_grade, total_price, link, colour, location
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    vehicle_data["Ref No"],
                    vehicle_data["Year"],
                    vehicle_data["Title"],
                    vehicle_data["Mileage"],
                    vehicle_data["Engine Size"],
                    vehicle_data["Engine Code"],
                    vehicle_data["Model Code"],
                    vehicle_data["Transmission"],
                    vehicle_data["Drive"],
                    vehicle_data["Steering"],
                    vehicle_data["Doors"],
                    vehicle_data["Seats"],
                    vehicle_data["Fuel Type"],
                    vehicle_data["Auction Grade"],
                    vehicle_data["Total Price"],
                    vehicle_data["Link"],
                    vehicle_data["Colour"],
                    vehicle_data["Location"],
                ),
            )
        except Exception as e:
            logging.error(f"Error inserting data for {vehicle_data['Ref No']}: {e}")
    else:
        logging.info(
            f"Record with Ref No {vehicle_data['Ref No']} already exists. Skipping insertion."
        )

    if vehicle_exists(cursor, vehicle_data["Ref No"]):
        logging.info(f"Vehicle {vehicle_data['Ref No']} added successfully.")


# Function to scrape pages
def scrape_pages(driver):
    """Loop through pages and scrape data"""
    successful_pages = 0
    pages_since_last_commit = 0  # Counter for pages processed since the last commit

    with sqlite3.connect("vehicles.db") as conn:
        cursor = conn.cursor()

        for page_number in range(1, NUM_PAGES + 1):
            retries = 0  # Initialize retries for each page
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

                        if vehicle_data:
                            insert_vehicle_data(cursor, vehicle_data)

                    successful_pages += 1
                    pages_since_last_commit += 1

                    if pages_since_last_commit >= 20:
                        conn.commit()
                        pages_since_last_commit = 0

                    logging.info(f"Page {page_number} processed successfully.")

                    break  # Break out of the retries loop, go to next page

                except (WebDriverException, requests.exceptions.RequestException) as e:
                    logging.error(f"Error on page {page_number}: {e}")
                    logging.info("Refreshing page...")
                    driver.refresh()
                    retries += 1

                except KeyboardInterrupt:
                    logging.info("Keyboard interrupt detected, exiting...")
                    return

                except Exception as e:
                    logging.error(f"Error on page {page_number}: {e}")
                    break  # Break out of the retries loop due to unexpected error

        logging.info(f"Total pages successfully scraped: {successful_pages}")

        conn.commit()


if __name__ == "__main__":
    setup_logging(LOG_DIRECTORY)
    start_time = start_timer()
    driver = init_webdriver()
    setup_database()

    try:
        scrape_pages(driver)

    finally:
        driver.quit()
        logging.info("Script finished, scraping complete!")

        elapsed_time_s = time.time() - start_time
        elapsed_time_m, elapsed_time_s = divmod(int(elapsed_time_s), 60)

        time_message = (
            f"{elapsed_time_m} minutes and {elapsed_time_s} seconds"
            if elapsed_time_m
            else f"{elapsed_time_s} seconds"
        )
        logging.info(f"Time taken: {time_message}")
