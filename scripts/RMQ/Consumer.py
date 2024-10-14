import json
import pika
import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Logger configs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('pika').setLevel(logging.WARNING) #Making logs less verbose

def extract_years_and_quarters(driver):  # Json format extract years and Quartiles
    try:
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[contains(@class, "jrnlname")]'))  # wait for web to laod 
        )
        button.click()  # Needed a click to get the data table ready

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[contains(@class, "cell100x1")]//td'))
        ) # wait for table to be ready

        year_quarter_elements = driver.find_elements(By.XPATH, '//*[contains(@class, "cell100x1")]//td') # Extract the years and quartiles
        year_quarter_data = {}

        # There are alot of different fields in the table, For today i only needed language part
        # So we check for the first part of the text to be linguistics
        # extarct the second and third as the Year and quartile
        i = 0
        while i < len(year_quarter_elements):  

            if "Linguistics and Language" in year_quarter_elements[i].text:
                year = year_quarter_elements[i + 1].text
                quarter = year_quarter_elements[i + 2].text
                year_quarter_data[year] = quarter
            i += 3

        return year_quarter_data

    except (NoSuchElementException, TimeoutException) as e:  # Simple Error handling
        logging.error(f"Error extracting years and quarters: {e}")
        return {}

def process_journal_number(ch, method, properties, body):   # function to open the url needed to fetch data
    journal_number = body.decode('utf-8')  # Body of the rmq message
    logging.info(f'Processing journal number: {journal_number}')

    chrome_binary_path = os.getenv('CHROME_BINARY_PATH')  # Binary path for chrome
    # sth lik exeport  CHROME_BINARY_PATH = "/usr/bin/google-chrome-stable"
    if not chrome_binary_path:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)  # Requeue the message
        raise EnvironmentError("CHROME_BINARY_PATH environment variable is not set.")
    
    logging.info(f"Chrome Binary Path : {chrome_binary_path}")
    driver = None # Error handling
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.binary_location = chrome_binary_path
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # simple way of searching utilizing the request instead of the search field on the website
        search_url = f"https://www.scimagojr.com/journalsearch.php?q={journal_number}"
        driver.get(search_url)

        year_quarter_data = extract_years_and_quarters(driver)

        output_dir = "result"
        os.makedirs(output_dir, exist_ok=True)  # Directory check

        output_filename = os.path.join(output_dir, f'output_{journal_number}.json')  # output every ISSN to a json file
        with open(output_filename, 'w') as json_file:
            json.dump({journal_number: year_quarter_data}, json_file, indent=4)

        logging.info(f"Finished processing {journal_number}, results saved to {output_filename}")
    
    except Exception as e:
        logging.error(f"Error processing {journal_number}: {e}")
    
    finally:
        if driver:
            driver.quit()

    ch.basic_ack(delivery_tag=method.delivery_tag)  # Ack for rmq 



def main():
    connection = None # Error Handling
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost')) # Simple rmq connecotin , its all local so i didnt consider any sec things
        queue_name = 'journal_queue'
        # If you wanna add username / password auth here
        #  remember to use gitignore 
        # or use env variables
        
        # Basic rmq consumer 
        channel = connection.channel()


        queue_status = channel.queue_declare(queue=queue_name, passive=True)
        if queue_status.method.message_count == 0:
            logging.info("Queue is empty. Shutting down...")
            return
            
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue_name, on_message_callback=process_journal_number)

        logging.info("Waiting for messages...")
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        logging.error(f"RabbitMQ connection failed: {e}")
    except KeyboardInterrupt:
        logging.info("Interrupted, shutting down...")
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    main()