import sqlite3
import logging
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import os
from main import setup_logging, init_webdriver
from dotenv import load_dotenv


load_dotenv()
LOG_DIRECTORY = os.getenv("LOG_DIRECTORY")


def check_vehicle_status(driver, link):
    """Check the current status of the vehicle on the website."""
    try:
        driver.get(link)

        try:
            price_element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p.total-price"))
            )
            price = price_element.text.strip().upper()

            if "SOLD" in price or "UNDER OFFER" in price or price == "ASK":
                return False  # Vehicle is no longer available

        except TimeoutException:
            logging.info(f"No price information found for {link}")

        return True  # Vehicle is still available

    except WebDriverException as e:
        logging.error(f"Error accessing {link}: {e}")

        return None  # Unable to determine status


def update_db(driver):
    """Update database to remove vehicles that are no longer available or have been sold"""
    conn = sqlite3.connect("vehicles.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicles")
    vehicles = cursor.fetchall()

    for vehicle in vehicles:
        ref_no = vehicle[0]
        link = vehicle[15]

        is_available = check_vehicle_status(driver, link)

        if is_available is False:
            logging.info(
                f"Vehicle {ref_no} has been sold or is under offer. Removing from database."
            )
            cursor.execute("DELETE FROM vehicles WHERE ref_no = ?", (ref_no,))

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
