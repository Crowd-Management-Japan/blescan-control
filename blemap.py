import logging
logging.basicConfig(level=logging.DEBUG, format=('%(levelname)s %(filename)s: %(lineno)d:\t%(message)s'))
import requests
import pandas as pd
import json
from io import StringIO
from folium import Map, CircleMarker
import matplotlib.pyplot as plt
import matplotlib.colors
import branca
import numpy as np
from datetime import datetime, timedelta
import time
import pytz
from flask import Flask, request, redirect, url_for, flash
from config import Config
import threading

app = Flask('blemap')
app.logger.setLevel('DEBUG')

# Write username and password here
users = {
    'user': 'password'
}

# Simple read HTML page
def read_html(page):
    with open(page, 'r') as file:
        html_content = file.read()
    return html_content

# On landing send user to login page
@app.route('/')
def home():
    return read_html('templates/login.html')

# Login page for security reasons
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in users and users[username] == password:
        return redirect(url_for('index'))
    else:
        return read_html('templates/error.html')

# Return simply the main page
@app.route('/index')
def index():
    return read_html('templates/index.html')

# Return page showing the map
@app.route('/map')
def update_map():
    return read_html('map/map.html')

# Fetches data from the server for specified device IDs and time range, returns a DataFrame
def fetch_data(ble_server_address, device_id, after_time, before_time):
    try:
        endpoint = f"/database/export_data?id={device_id}&after={after_time}&before={before_time}"
        response = requests.get(f"{ble_server_address}{endpoint}")
        json_response = response.json()
        json_str = json.dumps(json_response)
        json_io = StringIO(json_str)
        df = pd.read_json(json_io)
        return df
    except Exception as e:
        logging.debug(f"error {e} occurred while fetching data")
    return pd.DataFrame()

# Compute zoom level to fit all points in the map
def calculate_zoom_level(min_lat, max_lat, min_lon, max_lon):
    # Approximate factor to adjust zoom level based on latitude and longitude range
    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon

    # Simple heuristic to calculate zoom level based on latitude and longitude range
    max_range = max(lat_range, lon_range) / 2
    if max_range < 0.00025:
        return 20
    elif max_range < 0.0005:
        return 19
    elif max_range < 0.001:
        return 18
    elif max_range < 0.003:
        return 17
    elif max_range < 0.005:
        return 16
    elif max_range < 0.011:
        return 15
    elif max_range < 0.022:
        return 14
    elif max_range < 0.044:
        return 13
    elif max_range < 0.088:
        return 12
    elif max_range < 0.176:
        return 11
    elif max_range < 0.352:
        return 10
    else:
        return 9  # Default zoom level for wider ranges

# Initializes the map, adds CircleMarkers based on data points
def create_map(center_lat, center_lon, data_points):
    # Find the bounds of all data points
    min_lat = min(y for _, y, _, _ in data_points)
    max_lat = max(y for _, y, _, _ in data_points)
    min_lon = min(x for x, _, _, _ in data_points)
    max_lon = max(x for x, _, _, _ in data_points)
    
    # Calculate appropriate zoom level based on data bounds
    zoom_level = calculate_zoom_level(min_lat, max_lat, min_lon, max_lon)
    
    map_obj = Map(location=[center_lat, center_lon], zoom_start=zoom_level, 
                  scrollWheelZoom=False, dragging=False, zoomControl=False, tiles='CartoDB positron')
    cmap = plt.get_cmap('coolwarm')
    for x, y, count, device_id in data_points:
        rgba = cmap(count / Config.SCALE_MAX)
        hex_color = matplotlib.colors.rgb2hex(rgba)
        CircleMarker(location=[y, x], radius=Config.CIRCLE_SIZE, tooltip=str(device_id), color=hex_color, fill=True,
                     fill_color=hex_color, fill_opacity=0.85).add_to(map_obj)
    return map_obj

# Adds head content
def add_head(map_obj):
    html_head = '''
    <title>BLE sensors map</title>
    <meta http-equiv="refresh" content="10" />
    '''
    map_obj.get_root().html.add_child(branca.element.Element(html_head))

# Adds a legend to the map
def add_legend(map_obj):
    legend_html = '''
    <div style="position: fixed; 
    bottom: 30px; left: 30px; width: 125px; height: 95px; 
    border:2px solid grey; background-color: white; z-index:9999; font-size:14px;
    ">&nbsp; Color Legend <br>
    &nbsp; High (100):&nbsp; <i class="fa fa-circle fa-1x" style="color:red"></i><br>
    &nbsp; Med (  50):&nbsp; <i class="fa fa-circle fa-1x" style="color:#800080"></i><br>
    &nbsp; Low (   0):&nbsp; <i class="fa fa-circle fa-1x" style="color:blue"></i>
    </div>
    '''
    map_obj.get_root().html.add_child(branca.element.Element(legend_html))
    
# Adds text for latest update
def add_info(map_obj, current_time):
    time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
    info_html = f'''
    <div style="position: fixed; 
    top: 30px; right: 30px; width: 160px; height: 25px; 
    border:2px solid grey; background-color: white; z-index:9999; font-size:14px;
    ">&nbsp; {time_str} <br>
    </div>
    '''
    map_obj.get_root().html.add_child(branca.element.Element(info_html))

# Main script preparing page with map
def main():
    running = True
    japan_timezone = pytz.timezone('Asia/Tokyo')
    ble_server_address = "http://127.0.0.1:5000"
    while running:
        current_time = datetime.now(japan_timezone)
        past_time = current_time - timedelta(minutes=10)
        after_time = past_time.strftime('%Y-%m-%d %H:%M:%S')
        before_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        logging.debug(f"started map update at {before_time}")
        data_points = []
    
        try:
            for device_id in Config.ID_LIST:
                df = fetch_data(ble_server_address, device_id, after_time, before_time)
                if not df.empty:
                    x, y, count = df['longitude'].mean(), df['latitude'].mean(), df[Config.VALUE_TYPE].mean()
                    data_points.append((x, y, count, device_id))
            
            if data_points:
                center_lat = np.mean([y for _, y, _, _ in data_points])
                center_lon = np.mean([x for x, _, _, _ in data_points])
                map_obj = create_map(center_lat, center_lon, data_points)
                add_head(map_obj)
                add_legend(map_obj)
                add_info(map_obj, current_time)
                map_obj.save("map/map.html")
                update_map()
        except Exception as e:
            logging.debug(f"error {e} occurred while preparing the map")

        logging.debug(f"map for session {before_time} updated")
        time.sleep(10)
        
if __name__ == "__main__":
    map_thread = threading.Thread(target=main)
    map_thread.daemon = True
    map_thread.start()

    app.run(debug=False, host=Config.HOSTNAME, port=Config.PORT)
