import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from main_scrape import scrape_vehicle_data
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class TestScraper(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.quit()

    def test_scrape_vehicle_data(self):
        url = os.getenv("BASE_URL")
        self.driver.get(url)

        vehicle_data = scrape_vehicle_data(self.driver, num_pages_to_scarpe=1)

        # vehicle_data = scrape_vehicle_data(self.driver)

        # Check that the vehicle data is a list
        self.assertIsInstance(vehicle_data, list)

        # Check that each vehicle is a dictionary
        for vehicle in vehicle_data:
            self.assertIsInstance(vehicle, dict)

        # Check that each vehicle has the expected keys
        expected_keys = [
            "Title",
            "Mileage",
            "Year",
            "Engine",
            "Trans",
            "Model Code",
            "Fuel",
            "Engine code",
            "Drive",
            "Auction grade",
            "Total Price",
            "Link",
        ]
        for vehicle in vehicle_data:
            self.assertCountEqual(vehicle.keys(), expected_keys)

        # Check that the year is an integer
        for vehicle in vehicle_data:
            self.assertIsInstance(vehicle["Year"], int)

        # Check that the engine code is a string
        for vehicle in vehicle_data:
            self.assertIsInstance(vehicle["Engine code"], str)


if __name__ == "__main__":
    unittest.main()
