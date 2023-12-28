# Data Mining Tool & Analytic Project

## Overview

This project involves a data mining tool that scrapes vehicle data from a specific auction website. Initially inspired by Peter Kim's R-based project for scraping data from the Steam client, this tool has evolved significantly since its inception in 2019. 

After undergoing various iterations and exploring different languages and frameworks, the project has been revitalized using Python, offering enhanced performance and functionality.

### Features

- Data Mining: The core script (`main.py`) is designed to mine data from a selected vehicle auction site. It extracts detailed information about each vehicle. 
    
- Database Integration: Scraped data is stored efficiently in an SQLite database.

- Discord Integration: The tool integrates with the Discord API to enable automated messaging. A Discord bot sends notifications about new vehicle listings that meet predefined criteria.

- Dynamic Configuration: The script supports dynamic year threshold for vehicle selection, allowing it to automatically adjust the criteria based on the current year.

### Usage

Refer to `main.py` for the main script. 

$${\color{lightblue}To run the main project (scraper)}$$:

- Ensure Python 3.11.6 or later is installed.

- Install required dependencies: <i>`pip install -r requirements.txt`</i>.
    
- Configure environment variables for database and Discord API credentials.

- Run <i>`python main.py`</i> to start the data mining process.

To Update Database:

- Run <i>`python check_db.py`</i>

It will check the database with the site and remove any records of vehicles that's no longer available (sold or under offer)

To send listing to Discord:

- Run <i>`python to_discord.py`</i>

It will send listings that meet the current criteria, it is defined in the script.


### Requirements

- Python 3.11.6+
- Selenium WebDriver for web scraping.
- SQLite for database management.
- Discord API token for bot integration.
- ChromeDriver 119.x.x (compatible with Chrome version).

### Notes

- The script requires ChromeDriver to be either in the script's directory or included in the system's PATH. For Windows users, a specific version of ChromeDriver is necessary, while macOS users will need the macOS-compatible version.
    
- A `.env` file must be placed in the same directory as the script for loading environment variables.

### Future Enhancements

<!-- - Implementing advanced data analysis techniques on the scraped data for insights and trends. -->
    
- Extending the tool's functionality to support multiple auction sites.

- Improving modularity and script organization for scheduled jobs / tasks (Cron Jobs); ensures full automation

- Enhancing the Discord bot to interactively respond to user queries about vehicle listings.


