# main.py

from selenium import webdriver
import os
import chromedriver_binary  # Adds chromedriver binary to path
import pandas as pd
from sodapy import Socrata
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import smtplib
import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import gunicorn
import signal

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

if __name__ == '__main__':
    app.run_server()

# The following options are required to make headless Chrome
# work in a Docker container
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("window-size=1024,768")
chrome_options.add_argument("--no-sandbox")

client = Socrata("finances.worldbank.org", '4lAjROKl9GysVT07fl34yIlL4', username="achunet@worldbank.org", password="19920JOkeR19920")
results = client.get("3y7n-xmbj", limit=2000)
results_df = pd.DataFrame.from_records(results)

url = 'http://projects.worldbank.org/procurement/noticeoverview?id=OP00157448'
driver = webdriver.Chrome(chrome_options=chrome_options)
driver.get(url)
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
    send_email('Query found', 'query found')
else:
    send_email('No query found', 'no query found')

print("SUCCESS!")

os.kill(os.getpid(), signal.SIGTERM)
