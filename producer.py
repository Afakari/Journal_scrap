import pika
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def send_journal_numbers_to_queue(filename):
    try:
 
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        channel.queue_declare(queue='journal_queue')

        with open(filename, 'r') as file:
            for line in file:
                journal_number = line.strip()
                channel.basic_publish(exchange='', routing_key='journal_queue', body=journal_number)
                logging.info(f'Sent {journal_number} to queue')


        connection.close()
        logging.info("Connection to RabbitMQ closed successfully.")
    
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Usage: python producer.py <filename>")
        sys.exit(1)
    filename = sys.argv[1]
    logging.info(f"Starting producer with file: {filename}...")
    send_journal_numbers_to_queue(filename)
    logging.info("Producer finished execution.")
