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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_years_and_quarters(driver):
    try:
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[contains(@class, "jrnlname")]'))
        )
        button.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[contains(@class, "cell100x1")]//td'))
        )

        year_quarter_elements = driver.find_elements(By.XPATH, '//*[contains(@class, "cell100x1")]//td')
        year_quarter_data = {}

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

def process_journal_number(ch, method, properties, body):
    journal_number = body.decode('utf-8')
    logging.info(f'Processing journal number: {journal_number}')

    try:

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        search_url = f"https://www.scimagojr.com/journalsearch.php?q={journal_number}"
        driver.get(search_url)


        year_quarter_data = extract_years_and_quarters(driver)


        output_dir = "result"
        os.makedirs(output_dir, exist_ok=True)

        output_filename = os.path.join(output_dir, f'output_{journal_number}.json')
        with open(output_filename, 'w') as json_file:
            json.dump({journal_number: year_quarter_data}, json_file, indent=4)

        logging.info(f"Finished processing {journal_number}, results saved to {output_filename}")
    except Exception as e:
        logging.error(f"Error processing {journal_number}: {e}")
    finally:
        driver.quit()

    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        channel.queue_declare(queue='journal_queue')
        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(queue='journal_queue', on_message_callback=process_journal_number)

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