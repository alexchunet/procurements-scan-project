# main.py

from flask import Flask, send_file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import chromedriver_binary 
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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

@app.route("/", methods=["POST"])
def main():
    # The following options are required to make headless Chrome
    # work in a Docker container
    service = Service()
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--remote-debugging-port=8080")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("window-size=1024,768")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions");
    chrome_options.add_argument("--dns-prefetch-disable");
    chrome_options.add_argument("enable-automation")
    chrome_options.page_load_strategy = 'normal'
    print("Options added")

    # Query table
    client = Socrata("finances.worldbank.org", '4lAjROKl9GysVT07fl34yIlL4', username=os.environ['email_pwb'], password=os.environ['pass_pwb'])
    results = client.get("3y7n-xmbj", limit=2000)
    results_df = pd.DataFrame.from_records(results)
    trigger = 0
    # Correct date format
    results_df['submission_date'] = results_df['submission_date'].str.replace('T',' ').str[:-4]
    results_df['submission_date'] = pd.to_datetime(results_df['submission_date'])
    # Filter procurement for last week
    today = pd.to_datetime("today")
    week_prior =  today - datetime.timedelta(days=7)
    results_df = results_df[results_df['submission_date'] >= week_prior]
    # Filter only procurement notices
    results_df = results_df[results_df['notice_type'] != 'Contract Award']
    # Filter only services
    results_df = results_df[(results_df['procurement_group_desc'] != 'Works') & (results_df['procurement_group_desc'] != 'Goods')]
    # Open each page in a virtual browser and analyse its content
    results_df['scan'] = 'Not treated'
    print
    print("Main table structured: "+str(len(results_df.index))+"rows")

    # Key words
    browser = webdriver.Chrome(service=service, options=chrome_options)
    key_words = ['earth observation', 'Earth Observation', ' EO ', ' GIS ', 'geospatial', 'geographic information', 'imagery','geotechnical', 'remote sensing', 'télédétection', 'géospatial', 'satélite', 'teledetección', 'geoespacial', 'observación de la tierra']

    # Initialize browser
    browser = webdriver.Chrome(service=service, options=chrome_options)
    print("Browser initialized")
    for index, row in results_df.iterrows():
        print(results_df.loc[index, 'url']['url'])
        url = results_df.loc[index, 'url']['url']
        results_df.loc[index, 'url'] = url
        # Initialize a new browser
        browser.get(url)
        html = browser.page_source
        #time.sleep(2)
        #browser.close()
        #time.sleep(2)
    
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
    
        if any(word in text for word in key_words):
            results_df.loc[index, 'scan'] = 'detected'
            trigger=1
            print("query found")
        elif '403 ERROR' in text:
            results_df.loc[index, 'scan'] = 'error'     
            print("error")
        else:
            results_df.loc[index, 'scan'] = 'nothing detected'
            print('no match')
    browser.close()

    results_df = results_df[(results_df['scan']=='detected')]
    
    # Notification function #
    msg = MIMEMultipart()
    msg['Subject'] = "WB Project Procurements screening"
    sender = 'alex.chunet@gmail.com'
    recipients = ['alex.chunet@gmail.com','achunet@worldbank.org'] 
    emaillist = [elem.strip().split(',') for elem in recipients]

    def send_email(sbjt, msg):
        toaddrs = 'alex.chunet@gmail.com'

        # The actual mail sent
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(os.environ['email_p'],os.environ['pass_p'])
        server.sendmail(sender, emaillist, msg)
        server.quit()

    # Format email
    html = """\
    <html>
    <head></head>
    <body>
        <p1>Keywords used: ['earth observation', 'Earth Observation', ' EO ', ' GIS ', 'geospatial', 'geographic information', 'imagery','geotechnical', 'remote sensing', 'télédétection', 'géospatial', 'satélite', 'teledetección', 'geoespacial', 'observación de la tierra']</p1>
        {0}
    </body>
    </html>
    """.format(results_df.to_html())

    part1 = MIMEText(html, 'html')
    msg.attach(part1)

    # Send 
    if trigger == 1:
        send_email('Query found', msg.as_string())
    else:
        send_email('No query found', msg.as_string())
        
    print("SUCCESS!")
    return '', 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
