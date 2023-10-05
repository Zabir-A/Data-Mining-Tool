import sqlite3
import pandas as pd

# Load data from the XLSX file into a DataFrame
xlsx_filename = "scraped_data.xlsx"
df = pd.read_excel(xlsx_filename)

# Create a database connection
db_filename = "vehicles.db"
conn = sqlite3.connect(db_filename)

# Use the DataFrame's to_sql method to insert data into the 'vehicles' table


# if table exits, drop it and create a new one
# Replace 'if_exists' with 'replace' if you want to replace the existing data
df.to_sql("vehicles", conn, if_exists="replace", index=False)


# Commit changes and close the database connection
conn.commit()
conn.close()

print("Data from XLSX file successfully inserted into the 'vehicles' table.")
