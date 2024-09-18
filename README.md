# Journal Web Scraper with RabbitMQ

This project is a **web scraping** tool built using **Selenium** to extract journal data from the **SCImago Journal Rank (SJR)** website. It employs **RabbitMQ** to handle asynchronous tasks, with a producer that sends journal numbers to a queue and a consumer that processes these journal numbers by scraping the website.

> One of the main reasons that this project uses **RabbitMQ** instead of a simple multiprocessing python pool is mainly because at the time i had **RMQ** set up on my machine. So... we use it.
>It's overhead...

## Features
- **Asynchronous processing**: Uses RabbitMQ to queue and process journal numbers.
- **Selenium Web Scraper**: Extracts journal information (years and quarters) based on the journal number.
- **Headless Chrome**: Uses a headless **Chrome** browser for scraping to run without a visible browser window.
- **Logging**: Provides logs for the scraping and queuing processes.
- **Error Handling**: Catches common web scraping and message queue exceptions.

## Technologies
- **Python 3.6+**
- **Selenium** (with Chrome WebDriver)
- **RabbitMQ** (pika library)
- **JSON** (for output)
- **WebDriverManager** (automatically handles ChromeDriver installations)

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/journal-web-scraper.git
cd journal-web-scraper
```

### 2. Install dependencies
Make sure you have Python 3 installed. You can install all necessary dependencies using `pip`:
```bash
pip install -r requirements.txt
```

The `requirements.txt` file should include:
```plaintext
selenium
pika
webdriver-manager
```

### 3. Install RabbitMQ
Ensure that RabbitMQ is installed and running on your system. You can follow the [official installation guide](https://www.rabbitmq.com/download.html) for your OS.

### 4. Setup ChromeDriver
`webdriver-manager` is used to automatically manage ChromeDriver, so there's no need for manual setup. This will be handled when you run the scraper.

## Usage

### 1. Prepare the Input Data
Create a text file containing journal ISSN numbers (one per line):
```
1234-5678
0001-9593
0002-9475
```

### 2. Run the Producer
The producer script reads the journal numbers from a simple text file and sends them to the **RabbitMQ** queue.
```bash
python producer.py <Filename>
```

### 3. Run the Consumer (Web Scraper)
The consumer script will retrieve journal numbers from the RabbitMQ queue and scrape the SJR website for year and quarter data. The results are saved as JSON files in the `result/` directory.
```bash
python scraper.py
```

### 4. Output
For each journal number, a corresponding JSON file is created in the `result/` folder. Example file: `output_12345.json`.
```json
{
    "1234-5678": {
        "2020": "Q1",
        "2019": "Q2"
    }
}
```

## Error Handling and Logging
The system uses Python's `logging` module for detailed logging. Logs will indicate errors, successful tasks, and processing status. Common errors are logged to help with debugging.

## Contributing
Feel free to contribute to the project by submitting pull requests or reporting issues.

## License
This project is licensed under the MIT License.
