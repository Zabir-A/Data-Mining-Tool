import schedule
import time
import subprocess


def run_scraper():
    subprocess.run(["python", "scrape.py"])


def run_check_db():
    subprocess.run(["python", "check_db.py"])


def run_to_discord():
    subprocess.run(["python", "to_discord.py"])


# Task Scheduling
schedule.every().day.at("10:00").do(run_scraper)  # Runs daily at 10:00 AM
schedule.every().sunday.at("20:00").do(run_check_db)  # Runs every Sunday at 8:00 PM
schedule.every().day.at("15:00").do(run_to_discord)  # Runs daily at 3:00 PM


while True:
    schedule.run_pending()
    time.sleep(1)  # Wait one second before checking again
