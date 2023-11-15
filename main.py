# main.py

from flask import Flask, send_file
from selenium import webdriver
import chromedriver_binary  # Adds chromedriver binary to path
from webdriver_manager.chrome import ChromeDriverManager
import datetime
import os
import pandas as pd
from sodapy import Socrata
import time
import requests
from bs4 import BeautifulSoup
import smtplib
import dash
import dash_bootstrap_components as dbc
from dash import html
import gunicorn
import signal

app = Flask(__name__)

# The following options are required to make headless Chrome
# work in a Docker container
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--remote-debugging-port=8080")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("window-size=1024,768")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

print("Options added")

# Initialize a new browser
browser = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)

print("Browser initialized")

@app.route("/")
def hello_world():
    client = Socrata("finances.worldbank.org", '4lAjROKl9GysVT07fl34yIlL4', username="achunet@worldbank.org", password="19920JOkeR19920")
    results = client.get("3y7n-xmbj", limit=2000)
    results_df = pd.DataFrame.from_records(results)
    results_df['scan'] = 'Not treated'
    
    # Correct date format
    results_df['submission_date'] = results_df['submission_date'].str.replace('T',' ').str[:-4]
    results_df['submission_date'] = pd.to_datetime(results_df['submission_date'])
    
    # Filter procurement for last week
    today = pd.to_datetime("today")
    week_prior =  today - datetime.timedelta(weeks=1)
    results_df = results_df[results_df['submission_date'] >= week_prior]
    
    
    # Open each page in a virtual browser and analyse its content
    
    results_df['scan'] = 'Not treated'
    
    for index, row in results_df.iterrows():
        print(results_df.loc[index, 'url']['url'])
        url = results_df.loc[index, 'url']['url']
    
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(5)
        html = driver.page_source
        driver.close()
    
        soup = BeautifulSoup(html, features="html.parser")
    
        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()    # rip it out
    
        # get text
        text = soup.get_text()
    
        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = ' '.join(chunk for chunk in chunks if chunk)
    
        key_words = ['earth observation', 'Earth Observation', ' EO ', 'GIS', 'geospatial', 'geographic information', 'imagery']
    
        if any(word in text for word in key_words):
            results_df.loc[index, 'scan'] = 'detected'      
            print("query found")
        elif '403 ERROR' in text:
            results_df.loc[index, 'scan'] = 'error'     
            print("error")
        else:
            print('no match')
    
    results_df = results_df[(results_df['scan']=='detected')]
    
    # SEND FUNCTIONS #
    def send_email(sbjt, msg):
        fromaddr = 'alex.chunet@gmail.com'
        toaddrs = 'alex.chunet@gmail.com'
        bodytext = 'From: %s\nTo: %s\nSubject: %s\n\n%s' %(fromaddr, toaddrs, sbjt, msg)
    
        # The actual mail sent
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(os.environ['email_p'],os.environ['pass_p'])
        server.sendmail(fromaddr, toaddrs, bodytext)
        server.quit()
    
    if "Contract" in text:
        send_email('Query found', print(results_df))
    else:
        send_email('No query found', 'no query found')
    
    print("SUCCESS!")
    return send_file(print("SUCCESS!"))
