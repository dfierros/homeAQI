# SPDX-FileCopyrightText: 2020 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import logging
import time
from typing import Dict, Optional, Tuple

import board
import busio
from Adafruit_IO import Client
from adafruit_pm25.i2c import PM25_I2C
from simpleio import map_range

from .config.secrets import secrets
from .resources.aqi_categories import AQISensorBreakpoints

_logger = logging.getLogger(__name__)

# Interval the sensor publishes to Adafruit IO, in minutes
PUBLISH_INTERVAL = 10
reset_pin = None


def create_pm25_sensor(reset_pin_value=None) -> PM25_I2C:
    """Create and return a PM2.5 sensor instance over I2C."""
    i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
    return PM25_I2C(i2c, reset_pin_value)


def calculate_aqi(pm_sensor_reading: float) -> Tuple[int, Optional[str]]:
    """Calculate an AQI value and category from a PM2.5 concentration."""
    if pm_sensor_reading in AQISensorBreakpoints.GOOD:
        aqi_val = round(map_range(pm_sensor_reading, 0.0, 12.0, 0, 50))
        aqi_cat = str(AQISensorBreakpoints.GOOD)
    elif pm_sensor_reading in AQISensorBreakpoints.MODERATE:
        aqi_val = round(map_range(pm_sensor_reading, 12.1, 35.4, 51, 100))
        aqi_cat = str(AQISensorBreakpoints.MODERATE)
    elif pm_sensor_reading in AQISensorBreakpoints.UNHEALTHY_SENSITIVE:
        aqi_val = round(map_range(pm_sensor_reading, 35.5, 55.4, 101, 150))
        aqi_cat = str(AQISensorBreakpoints.UNHEALTHY_SENSITIVE)
    elif pm_sensor_reading in AQISensorBreakpoints.UNHEALTHY:
        aqi_val = round(map_range(pm_sensor_reading, 55.5, 150.4, 151, 200))
        aqi_cat = str(AQISensorBreakpoints.UNHEALTHY)
    elif pm_sensor_reading in AQISensorBreakpoints.VERY_UNHEALTHY:
        aqi_val = round(map_range(pm_sensor_reading, 150.5, 250.4, 201, 300))
        aqi_cat = str(AQISensorBreakpoints.VERY_UNHEALTHY)
    elif pm_sensor_reading in AQISensorBreakpoints.LOW_HAZARDOUS:
        aqi_val = round(map_range(pm_sensor_reading, 250.5, 350.4, 301, 400))
        aqi_cat = str(AQISensorBreakpoints.LOW_HAZARDOUS)
    elif pm_sensor_reading in AQISensorBreakpoints.HIGH_HAZARDOUS:
        aqi_val = round(map_range(pm_sensor_reading, 350.5, 500.4, 401, 500))
        aqi_cat = str(AQISensorBreakpoints.HIGH_HAZARDOUS)
    else:
        _logger.warning("Invalid PM2.5 concentration: %s", pm_sensor_reading)
        return -1, None

    return int(aqi_val), aqi_cat


def sample_aq_sensor(pm25_sensor: PM25_I2C, duration: float = 2.3, sample_interval: float = 1.0) -> float:
    """Sample the PM2.5 sensor over a short period and return the average value."""
    samples = []
    start_time = time.monotonic()

    while time.monotonic() - start_time <= duration:
        try:
            data = pm25_sensor.read()
            samples.append(data["pm25 env"])
        except RuntimeError:
            _logger.warning("Unable to read from sensor, retrying...")
            time.sleep(sample_interval)
            continue

        time.sleep(sample_interval)

    if not samples:
        raise RuntimeError("No valid PM2.5 readings were collected.")

    return sum(samples) / len(samples)


def build_location_metadata() -> Dict[str, Optional[float]]:
    """Return metadata for publishing location to Adafruit IO."""
    return {
        "lat": secrets["latitude"],
        "lon": secrets["longitude"],
        "ele": secrets["elevation"],
        "created_at": time.time()
    }


def create_io_client() -> Client:
    """Create an Adafruit IO HTTP client using configured secrets."""
    if not secrets.get("aio_username") or not secrets.get("aio_key"):
        raise ValueError("Adafruit IO credentials are not configured in secrets.py")
    return Client(secrets["aio_username"], secrets["aio_key"])


def create_feeds(aio: Client) -> Dict[str, object]:
    """Create and return Adafruit IO feed objects used by this module."""
    _logger.debug("Obtaining user's feeds...")
    feeds = aio.feeds()
    _logger.debug('Feeds: %s', feeds)
    return {
        "aqi": aio.feeds("air-quality-sensor.aqi"),
        "category": aio.feeds("air-quality-sensor.category"),
    }


def publish_data(
    aio: Client,
    feeds: Dict[str, object],
    aqi_value: int,
    aqi_category: Optional[str],
    location_metadata: Dict[str, Optional[float]],
) -> None:
    """Publish AQI and category to Adafruit IO."""
    if aqi_category is None:
        raise ValueError("AQI category is required for publishing")
    _logger.debug("Sending data to Adafruit IO: AQI=%s, Category=%s", aqi_value, aqi_category)
    aio.send_data(feeds["aqi"].key, str(aqi_value))
    aio.send_data(feeds["category"].key, aqi_category)

def run(
    publish_interval: int = PUBLISH_INTERVAL,
    reset_pin_value=None,
) -> None:
    """Run the listen-and-publish loop until interrupted."""
    pm25_sensor = create_pm25_sensor(reset_pin_value)
    io_client = create_io_client()
    feeds = create_feeds(io_client)
    location_metadata = build_location_metadata()

    elapsed_minutes = 0
    previous_minute = 0

    _logger.info("Sampling AQI...")
    aqi_reading = sample_aq_sensor(pm25_sensor)
    aqi_value, aqi_category = calculate_aqi(aqi_reading)
    _logger.info("AQI: %s", aqi_value)
    _logger.info("Category: %s", aqi_category)

    _logger.info("Publishing to Adafruit IO...")
    try:
        publish_data(
            io_client,
            feeds,
            aqi_value,
            aqi_category,
            location_metadata,
        )
        _logger.info("Published successfully")
    except (ValueError, RuntimeError, ConnectionError, OSError) as exc:
        _logger.warning("Failed to send data to Adafruit IO: %s", exc)

    while True:
        try:
            _logger.debug("Fetching time from Adafruit IO...")
            current_time = io_client.receive_time()
            _logger.debug("Time fetched: %s", current_time)
            if current_time.tm_min == 0:
                previous_minute = 0
        except (ValueError, RuntimeError, ConnectionError, OSError) as exc:
            _logger.warning("Failed to fetch time: %s", exc)
            time.sleep(1)
            continue

        if current_time.tm_min >= previous_minute:
            _logger.info("%d minute(s) elapsed", elapsed_minutes)
            previous_minute = current_time.tm_min
            elapsed_minutes += 1

        if elapsed_minutes >= publish_interval:
            _logger.info("Sampling AQI...")
            aqi_reading = sample_aq_sensor(pm25_sensor)
            aqi_value, aqi_category = calculate_aqi(aqi_reading)
            _logger.info("AQI: %s", aqi_value)
            _logger.info("Category: %s", aqi_category)

            _logger.info("Publishing to Adafruit IO...")
            try:
                publish_data(
                    io_client,
                    feeds,
                    aqi_value,
                    aqi_category,
                    location_metadata,
                )
                _logger.info("Published successfully")
            except (ValueError, RuntimeError, ConnectionError, OSError) as exc:
                _logger.warning("Failed to send data to Adafruit IO, reconnecting: %s", exc)
                time.sleep(1)
                continue

            elapsed_minutes = 0

        time.sleep(30)
