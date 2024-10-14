import json
import os
import logging
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ProcessPoolExecutor, as_completed
import sys


# For the purpose of easier Transfer and usage, I did not make this script modular 
# This one is created literally for the purpose above, RMQ for this simple pool is way overhead as mentioned before
# By this i remade some of the stuff used here, added more exception handling 
# Made the script more portable and python friendly by using concurrent features 
# Made the script cleaner by running the python workers directly from the main python file


# To run the script you should just:
#
# python scraper.py <Filename> <Amount of workers>
#
# The file should be a csv containing names or issns or anything else that goes into the search bar
# The amount of workers are the amount of parallel python consumers 



# Logging config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 

# An Error handling try to reduce problems with chrome binary files, switching between windows / linux envs
def get_chrome_binary_path():
    os_name = platform.system().lower()
    if os_name == 'windows':
        return "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"    # A default Chrome path i found online
    elif os_name in ['linux', 'darwin']:
        return "/usr/bin/google-chrome-stable"   # My own machine Chrome binary path 
    else:
        logging.error(f"Unsupported operating system: {os_name}")
        raise EnvironmentError("Unsupported OS. Chrome binary path must be set manually.") # Good luck using any other non posix

# Main extraction of Quartiles
# If you wanna modify the script to do some other actions, you should mainly edit this 
def extract_years_and_quarters(driver):
    try:
        # Driver wait is the native way to wait i would guess
        # You use this for it to reduce the wait time 
        button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[contains(@class, "jrnlname")]'))
        )
        button.click()     # If Button is clickable, Then click

        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[contains(@class, "cell100x1")]//td'))
        )
        year_quarter_elements = driver.find_elements(By.XPATH, '//*[contains(@class, "cell100x1")]//td')
        year_quarter_data = {}

        # Weird logic to extract quartiles
        i = 0
        while i < len(year_quarter_elements):
            if "Linguistics and Language" in year_quarter_elements[i].text:
                year = year_quarter_elements[i + 1].text
                quarter = year_quarter_elements[i + 2].text
                year_quarter_data[year] = quarter
            i += 3

        return year_quarter_data

    except (NoSuchElementException, TimeoutException) as e:
        logging.error(f"Error extracting years and quarters: {e}")
        return {}

# Staging for main scraper function
def process_journal_number(journal_number):
    logging.info(f'Processing journal number: {journal_number}')
    
    # Check for binary path
    try:
        chrome_binary_path = get_chrome_binary_path()
        logging.info(f"Using Chrome Binary Path: {chrome_binary_path}")
    except EnvironmentError as e:
        logging.error(e)
        return None

    driver = None  # Error handling
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")   # Might cause some errors in some machines, Don't think you should be worried
        chrome_options.binary_location = chrome_binary_path
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Main website to search
        # I used the search query directly to save resources
        search_url = f"https://www.scimagojr.com/journalsearch.php?q={journal_number}"
        driver.get(search_url)

        # Main scrap function
        year_quarter_data = extract_years_and_quarters(driver)


        # Output logic
        output_dir = "result"
        os.makedirs(output_dir, exist_ok=True)  # Simple check for directory without the need of Ifs

        output_filename = os.path.join(output_dir, f'output_{journal_number}.json')
        with open(output_filename, 'w') as json_file:
            json.dump({journal_number: year_quarter_data}, json_file, indent=4)

        logging.info(f"Finished processing {journal_number}, results saved to {output_filename}")
    
    # Couldn't really handle anything after the binaries 
    except WebDriverException as e:
        logging.error(f"WebDriver error while processing {journal_number}: {e}")
    
    except Exception as e:
        logging.error(f"Error processing {journal_number}: {e}")
    
    finally:
        if driver:
            driver.quit()

    return journal_number

# Channel(pool) Creation and workers
def process_all_journals(journal_numbers , workers):
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_journal_number, journal_number) for journal_number in journal_numbers]

        for future in as_completed(futures):
            journal_number = future.result()
            if journal_number:
                logging.info(f"Completed processing of journal number: {journal_number}")

def read_journal_numbers(filename):
    try:
        with open(filename, 'r') as file:
            journal_numbers = [line.strip() for line in file]
        return journal_numbers
    except FileNotFoundError:
        logging.error(f"File {filename} not found.")
        return []

if __name__ == "__main__":
    if len(sys.argv) != 3:
        logging.error("Usage: python script.py <filename> <Amount of Workers> ")
        sys.exit(1)

    filename = sys.argv[1]
    workers = int(sys.argv[2]) 
    logging.info(f"Reading journal numbers from file: {filename}...")
    
    journal_numbers = read_journal_numbers(filename)
    
    if not journal_numbers:
        logging.info("No journal numbers found in the file.")
    else:
        logging.info(f"Using {workers} active workers.")
        process_all_journals(journal_numbers,workers)
        logging.info("All journal numbers processed.")

