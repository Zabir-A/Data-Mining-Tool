import sqlite3
import logging
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import os
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from dotenv import load_dotenv
import datetime
import time

# import json
from fake_useragent import UserAgent


load_dotenv()
LOG_DIRECTORY = os.getenv("LOG_DIRECTORY")

# TODO:
# - Add cookie support & handling


# # Function to save cookies to a file
# def save_cookies(driver, location):
#     with open(location, "w") as file:
#         json.dump(driver.get_cookies(), file)


# # Function to load cookies from a file
# def load_cookies(driver, location, url=None):
#     with open(location, "r") as file:
#         cookies = json.load(file)
#     if url:
#         driver.get(url)
#     for cookie in cookies:
#         driver.add_cookie(cookie)


def init_webdriver():
    """Initialize Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")

    # chrome_options.add_argument(
    #     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
    # )

    ua = UserAgent()
    userAgent = ua.random
    chrome_options.add_argument(f"user-agent={userAgent}")

    return webdriver.Chrome(options=chrome_options)


def setup_logging(LOG_DIRECTORY):
    """Setup logging configuration"""

    db_logs_dir = os.path.join(LOG_DIRECTORY, "db_logs")

    if not os.path.exists(db_logs_dir):
        os.makedirs(db_logs_dir, exist_ok=True)
        logging.info(f"Directory {db_logs_dir} created.")

    timestamp = datetime.datetime.now().strftime("%y-%m-%d_%I%M%p")

    log_filename = (
        f"{db_logs_dir}/db_log_{timestamp}.log"  # Save logs in the db_logs subdirectory
    )

    logging.basicConfig(
        level=logging.INFO,  # Log only INFO, WARNING, ERROR, and CRITICAL levels.
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(),
        ],
    )


def fetch_page(driver, link):
    """Fetch the page and return the status of the operation."""
    try:
        time.sleep(1)
        driver.get(link)
        return True

    except WebDriverException as e:
        logging.error(f"Error accessing {link}: {e}")
        return False


def check_vehicle_status(driver, link):
    """Check the current status of the vehicle on the website."""
    if not fetch_page(driver, link):
        return None  # Unable to determine status

    try:
        price_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "p.total-price"))
        )
        price = price_element.text.strip().upper()

        return "SOLD" not in price and "UNDER OFFER" not in price and price != "ASK"

    except TimeoutException:
        logging.info(f"No price information found for {link}")

        return True  # Vehicle is still available


def update_db(driver):
    """Update database to remove vehicles that are no longer available or have been sold"""
    conn = sqlite3.connect("vehicles.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ref_no, link FROM vehicles")

    for ref_no, link in cursor.fetchall():
        if not check_vehicle_status(driver, link):
            logging.info(
                f"Vehicle {ref_no} has been sold or is under offer. Removing from database."
            )
            cursor.execute("DELETE FROM vehicles WHERE ref_no = ?", (ref_no,))
        else:
            logging.info(f"Vehicle {ref_no} is still available.")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    setup_logging(LOG_DIRECTORY)
    driver = init_webdriver()

    try:
        update_db(driver)
    finally:
        driver.quit()
