# SPDX-FileCopyrightText: 2020 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import time
import board
import busio
import logging

from adafruit_io.adafruit_io import IO_HTTP
from simpleio import map_range
from typing import Tuple
from adafruit_pm25.i2c import PM25_I2C
from ...resources.aqi_categories import AQIValDescription

try:
    from config.secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

_logger = logging.getLogger(__name__)


# ------- Configure Sensor ------------------------------

# Return environmental sensor readings in degrees Celsius
USE_CELSIUS = False
# Interval the sensor publishes to Adafruit IO, in minutes
PUBLISH_INTERVAL = 10

reset_pin = None

# -------------------------------------------------------

# Create i2c object
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)

# Connect to a PM2.5 sensor over I2C
pm25 = PM25_I2C(i2c, reset_pin)


# ------- Sensor Functions ------------------------------
def calculate_aqi(pm_sensor_reading: float) -> Tuple[int, str]:
    """
    Returns a calculated air quality index (AQI) and category as a tuple.

    Notes:
        The AQI returned by this function should ideally be measured using the 24-hour
            concentration average. Calculating a AQI without averaging will result in
            higher AQI values than expected.

    Args:
        pm_sensor_reading (float): Particulate matter sensor value.


    Returns:
        (int): calculated air quality index (AQI)
        (str): AQI category plaintext    
    """
    # Check sensor reading using EPA breakpoint (Clow-Chigh)
    if pm_sensor_reading in AQIValDescription.GOOD.range:
        # AQI calculation using EPA breakpoints (Ilow-IHigh)
        aqi_val = map_range(int(pm_sensor_reading), 0, 12, 0, 50)
        aqi_cat = AQIValDescription.GOOD
    elif pm_sensor_reading in AQIValDescription.MODERATE.range:
        aqi_val = map_range(int(pm_sensor_reading), 12, 35, 51, 100)
        aqi_cat = AQIValDescription.MODERATE
    elif pm_sensor_reading in AQIValDescription.UNHEALTHY_SENSITIVE.range:
        aqi_val = map_range(int(pm_sensor_reading), 36, 55, 101, 150)
        aqi_cat = AQIValDescription.UNHEALTHY_SENSITIVE
    elif pm_sensor_reading in AQIValDescription.UNHEALTHY.range:
        aqi_val = map_range(int(pm_sensor_reading), 56, 150, 151, 200)
        aqi_cat = AQIValDescription.UNHEALTHY
    elif pm_sensor_reading in AQIValDescription.VERY_UNHEALTHY.range:
        aqi_val = map_range(int(pm_sensor_reading), 151, 250, 201, 300)
        aqi_cat = AQIValDescription.VERY_UNHEALTHY
    elif pm_sensor_reading in AQIValDescription.LOW_HAZARDOUS.range:
        aqi_val = map_range(int(pm_sensor_reading), 251, 350, 301, 400)
        aqi_cat = AQIValDescription.LOW_HAZARDOUS
    elif pm_sensor_reading in AQIValDescription.HIGH_HAZARDOUS.range:
        aqi_val = map_range(int(pm_sensor_reading), 351, 500, 401, 500)
        aqi_cat = AQIValDescription.HIGH_HAZARDOUS
    else:
        _logger.warning("Invalid PM2.5 concentration")
        aqi_val = -1
        aqi_cat = None
    return aqi_val, aqi_cat


def sample_aq_sensor():
    """Samples PM2.5 sensor
    over a 2.3 second sample rate.

    """
    aq_reading = 0
    aq_samples = []

    # initial timestamp
    time_start = time.monotonic()
    # sample pm2.5 sensor over 2.3 sec sample rate
    while time.monotonic() - time_start <= 2.3:
        try:
            aqdata = pm25.read()
            aq_samples.append(aqdata["pm25 env"])
        except RuntimeError:
            _logger.warning("Unable to read from sensor, retrying...")
            continue
        # pm sensor output rate of 1s
        time.sleep(1)
    # average sample reading / # samples
    for sample in range(len(aq_samples)):
        aq_reading += aq_samples[sample]
    aq_reading = aq_reading / len(aq_samples)
    aq_samples.clear()
    return aq_reading


# Create an instance of the Adafruit IO HTTP client
io = IO_HTTP(secrets["aio_user"], secrets["aio_key"], wifi)

# Describes feeds used to hold Adafruit IO data
feed_aqi = io.get_feed("air-quality-sensor.aqi")
feed_aqi_category = io.get_feed("air-quality-sensor.category")
feed_humidity = io.get_feed("air-quality-sensor.humidity")
feed_temperature = io.get_feed("air-quality-sensor.temperature")

# Set up location metadata from secrets.py file
location_metadata = {
    "lat": secrets["latitude"],
    "lon": secrets["longitude"],
    "ele": secrets["elevation"],
}

elapsed_minutes = 0
prv_mins = 0

while True:
    try:
        print("Fetching time...")
        cur_time = io.receive_time()
        print("Time fetched OK!")
        # Hourly reset
        if cur_time.tm_min == 0:
            prv_mins = 0
    except (ValueError, RuntimeError, ConnectionError, OSError) as e:
        print("Failed to fetch time, retrying\n", e)
        wifi.reset()
        wifi.connect()
        continue

    if cur_time.tm_min >= prv_mins:
        print("%d min elapsed.." % elapsed_minutes)
        prv_mins = cur_time.tm_min
        elapsed_minutes += 1

    if elapsed_minutes >= PUBLISH_INTERVAL:
        print("Sampling AQI...")
        aqi_reading = sample_aq_sensor()
        aqi, aqi_category = calculate_aqi(aqi_reading)
        print("AQI: %d" % aqi)
        print("Category: %s" % aqi_category)

        # temp and humidity
        print("Sampling environmental sensor...")
        temperature, humidity = read_bme(USE_CELSIUS)
        print("Temperature: %0.1f F" % temperature)
        print("Humidity: %0.1f %%" % humidity)

        # Publish all values to Adafruit IO
        print("Publishing to Adafruit IO...")
        try:
            io.send_data(feed_aqi["key"], str(aqi), location_metadata)
            io.send_data(feed_aqi_category["key"], aqi_category)
            io.send_data(feed_temperature["key"], str(temperature))
            io.send_data(feed_humidity["key"], str(humidity))
            print("Published!")
        except (ValueError, RuntimeError, ConnectionError, OSError) as e:
            print("Failed to send data to IO, retrying\n", e)
            wifi.reset()
            wifi.connect()
            continue
        # Reset timer
        elapsed_minutes = 0
    time.sleep(30)
