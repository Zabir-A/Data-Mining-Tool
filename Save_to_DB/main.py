import subprocess


scraping_script = "scraper.py"
db_insertion_script = "save_db.py"


# Function to run a script as a separate process
def run_script(script_path):
    try:
        subprocess.run(["python", script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path}: {e}")


if __name__ == "__main__":
    run_script(scraping_script)
    run_script(db_insertion_script)
