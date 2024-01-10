#!/usr/bin/env python
"""
Unit tests for PM25 sensor dataclasses

"""
from homeaqi.resources.pm_25_dataclasses import PM25Data

EXAMPLE_PM25_DATA: dict = {
    "pm10 standard": 0,
    "pm25 standard": 0,
    "pm100 standard": 0,
    "pm10 env": 0,
    "pm25 env": 0,
    "pm100 env": 0,
    "particles 03um": 0,
    "particles 05um": 0,
    "particles 10um": 0,
    "particles 25um": 0,
    "particles 50um": 0,
    "particles 100um": 0,
}


class TestPM25DataClasses:
    def test_construction(self):
        """
        Verify that a PM25Data object can be instantiated with non-meaningful data

        """
        # Verify that a dataclass instantiated from the classmethod matches that from the constructor
        data = PM25Data(*([0] * 12))
        data_from_dict = PM25Data.from_dict(EXAMPLE_PM25_DATA)
        assert data == data_from_dict

        # Basic validation that values are passed in
        print(data_from_dict)
        assert data_from_dict.pm_10_standard == 0
