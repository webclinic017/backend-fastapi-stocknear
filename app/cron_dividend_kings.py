import os
import pandas as pd
import ujson
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import sqlite3

def save_json(data, file_path):
    with open(file_path, 'w') as file:
        ujson.dump(data, file)

query_template = """
    SELECT 
        name, sector
    FROM 
        stocks 
    WHERE
        symbol = ?
"""

def main():
    # Load environment variables
    con = sqlite3.connect('stocks.db')
    load_dotenv()
    url = os.getenv('DIVIDEND_KINGS')

    # Set up the WebDriver options
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Initialize the WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=options)

    try:
        # Fetch the website
        driver.get(url)
        # Find the table element
        table = driver.find_element(By.TAG_NAME, 'table')
        # Extract the table HTML
        table_html = table.get_attribute('outerHTML')
        # Use pandas to read the HTML table
        df = pd.read_html(table_html)[0]
        # Rename the columns
        df = df.rename(columns={
            'Symbol': 'symbol',
            'Company Name': 'name',
            'Stock Price': 'price',
            '% Change': 'changesPercentage',
            'Div. Yield': 'dividiendYield',
            'Years': 'years'
        })
        df = df.drop(columns=['No.'])
        # Convert the DataFrame to JSON
        data = ujson.loads(df.to_json(orient='records'))
        res = []
        for item in data:
            symbol = item['symbol']
            try:
                item['changesPercentage'] = round(float(item['changesPercentage'].replace('%','')),2)
                item['dividiendYield'] = round(float(item['dividiendYield'].replace('%','')),2)
                db_data = pd.read_sql_query(query_template, con, params=(symbol,))
                res.append({**item,'sector': db_data['sector'].iloc[0]})
            except Exception as e:
                pass

        # Save the JSON data
        if len(res) > 0:
            save_json(res, 'json/stocks-list/dividend-kings.json')
    
    finally:
        # Ensure the WebDriver is closed
        driver.quit()
        con.close()

if __name__ == '__main__':
    main()