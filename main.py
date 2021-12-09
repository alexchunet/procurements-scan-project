# main.py

from selenium import webdriver
import chromedriver_binary  # Adds chromedriver binary to path
import pandas as pd
from sodapy import Socrata
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

####################
import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import gunicorn
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server
#html_string = '''<link rel="stylesheet" href="https://aladin.u-strasbg.fr/AladinLite/api/v2/latest/aladin.min.css" /> <script type="text/javascript" src="https://code.jquery.com/jquery-1.9.1.min.js" charset="utf-8"></script> <div id="aladin-lite-div" style="width:100%;height:100%;"></div> <input id="DSS" type="radio" name="survey" value="P/DSS2/color" checked><label for="DSS">DSS color<label> <input id="DSS-blue" type="radio" name="survey" value="P/DSS2/blue"><label for="DSS-blue">DSS blue<label> <input id="2MASS" type="radio" name="survey" value="P/2MASS/color"><label for="2MASS">2MASS<label> <input id="allwise" type="radio" name="survey" value="P/allWISE/color"><label for="allwise">AllWISE<label> <input id="glimpse" type="radio" name="survey" value="P/GLIMPSE360"><label for="glimpse">GLIMPSE 360<label> <script type="text/javascript" src="https://aladin.u-strasbg.fr/AladinLite/api/v2/latest/aladin.min.js" charset="utf-8"></script> <script type="text/javascript"> var aladin = A.aladin('#aladin-lite-div', {survey: "P/DSS2/color", fov:1.5, target: '05 37 5.698 -01 36 54.50', showReticle: false});$('input[name=survey]').change(function() {aladin.setImageSurvey($(this).val());});var marker1 = A.marker(84.3950446, -1.4222331, {popupTitle: 'LOG_003', popupDesc: "<div style='vertical-align:middle; display:inline;'> I must hold on ... we are soon arriving. I can see it between the clouds. </div> <img src='log03.jpg' style='width:100%;height:100%;'>"});var marker2 = A.marker(84.4547634, -1.5856669, {popupTitle: 'LOG_036', popupDesc: "<div style='vertical-align:middle; display:inline;'> It is breathtaking...sadly my Rhoecos is getting more and more agitated. </div> <img src='log036.jpg' style='width:100%;height:100%;'>"});var marker3 = A.marker(84.3104199, -1.6674441, {popupTitle: 'LOG_027', popupDesc: "<div style='vertical-align:middle; display:inline;'> I would never dare ask //?/.? the question. I'm too afraid to be right... </div> <img src='log027.jpg' style='width:100%;height:100%;'>"});var marker4 = A.marker(84.0742596, -1.6353706, {popupTitle: 'LOG_06', popupDesc: "<div style='vertical-align:middle; display:inline;'> We are advancing at a good pace even if Camer and Sigur have already been through the door for 2 days by now. </div> <img src='log06.jpg' style='width:100%;height:100%;'>"});var markerLayer = A.catalog({color: 'blue', sourceSize: 15});aladin.addCatalog(markerLayer);markerLayer.addSources([marker1, marker2, marker3, marker4]);var drawFunction = function(source, canvasCtx, viewParams) {canvasCtx.beginPath();canvasCtx.arc(source.x, source.y, source.data['size'] * 2, 0, 2 * Math.PI, false);canvasCtx.closePath();canvasCtx.strokeStyle = '#c38';canvasCtx.lineWidth = 3;canvasCtx.globalAlpha = 0.7,canvasCtx.stroke();var fov = Math.max(viewParams['fov'][0], viewParams['fov'][1]);if (fov>10) {    return;}canvasCtx.globalAlpha = 0.9;canvasCtx.globalAlpha = 1;var xShift = 20;canvasCtx.font = '15px Arial';canvasCtx.fillStyle = '#eee';canvasCtx.fillText(source.data['name'], source.x + xShift, source.y -4);            if (fov>2) {    return;}canvasCtx.font = '12px Arial';canvasCtx.fillStyle = '#abc';    canvasCtx.fillText(source.data['otype'], source.x + 2 + xShift, source.y + 10);};var M01 = A.source(84.3950446, -1.4222331, {name: 'LOG_03', size: 0, otype: 'Rebirth'});var M02 = A.source(84.4547634, -1.5856669, {name: 'LOG_036', size: 0, otype: 'Exodus'});var M03 = A.source(84.3104199, -1.6674441, {name: 'LOG_027', size: 0, otype: 'Freedom'});var M04 = A.source(84.0742596, -1.6353706, {name: 'LOG_06', size: 0, otype: 'Revelation'});var cat = A.catalog({name: 'Virgo cluster', shape: drawFunction});cat.addSources([M01,M02,M03,M04]);aladin.addCatalog(cat);var overlay = A.graphicOverlay({lineWidth: 2});aladin.addOverlay(overlay);overlay.add(A.polyline([[84.3950446, -1.4222331], [84.4547634, -1.5856669], [84.3104199, -1.6674441], [84.0742596, -1.6353706]], {color: '#1751ff'}));   </script>'''
app.layout = html.Div(children=[html.Iframe(id = 'map', src = 'assets/index.html', width='100%', height='900')])

if __name__ == '__main__':
    app.run_server()
####################

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

if "Contract" in text:
    print("query found")
else:
    print("no match")
