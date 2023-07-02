# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Example sketch to connect to PM2.5 sensor with either I2C or UART.
"""

import logging
import time

import board
import busio
from adafruit_pm25.i2c import PM25_I2C

# from digitalio import DigitalInOut, Direction, Pull

_logger = logging.getLogger(__name__)


reset_pin = None
# If you have a GPIO, its not a bad idea to connect it to the RESET pin
# reset_pin = DigitalInOut(board.G0)
# reset_pin.direction = Direction.OUTPUT
# reset_pin.value = False


# For use with a computer running Windows:
# import serial
# uart = serial.Serial("COM30", baudrate=9600, timeout=1)

# For use with microcontroller board:
# (Connect the sensor TX pin to the board/computer RX pin)
# uart = busio.UART(board.TX, board.RX, baudrate=9600)

# For use with Raspberry Pi/Linux:
# import serial
# uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=0.25)

# For use with USB-to-serial cable:
# import serial
# uart = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=0.25)

# Connect to a PM2.5 sensor over UART
# from adafruit_pm25.uart import PM25_UART
# pm25 = PM25_UART(uart, reset_pin)


def listen_loop():
    # Create library object, use 'slow' 100KHz frequency!
    i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
    # Connect to a PM2.5 sensor over I2C
    pm25 = PM25_I2C(i2c, reset_pin)

    _logger.info("Found PM2.5 sensor, reading data...")

    while True:
        time.sleep(1)

        try:
            aqdata = pm25.read()
            # _logger.info(aqdata)
        except RuntimeError:
            _logger.info("Unable to read from sensor, retrying...")
            continue

        _logger.info()
        _logger.info("Concentration Units (standard)")
        _logger.info("---------------------------------------")
        _logger.info(
            "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
            % (
                aqdata["pm10 standard"],
                aqdata["pm25 standard"],
                aqdata["pm100 standard"],
            )
        )
        _logger.info("Concentration Units (environmental)")
        _logger.info("---------------------------------------")
        _logger.info(
            "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
            % (aqdata["pm10 env"], aqdata["pm25 env"], aqdata["pm100 env"])
        )
        _logger.info("---------------------------------------")
        _logger.info("Particles > 0.3um / 0.1L air:", aqdata["particles 03um"])
        _logger.info("Particles > 0.5um / 0.1L air:", aqdata["particles 05um"])
        _logger.info("Particles > 1.0um / 0.1L air:", aqdata["particles 10um"])
        _logger.info("Particles > 2.5um / 0.1L air:", aqdata["particles 25um"])
        _logger.info("Particles > 5.0um / 0.1L air:", aqdata["particles 50um"])
        _logger.info("Particles > 10 um / 0.1L air:", aqdata["particles 100um"])
        _logger.info("---------------------------------------")
