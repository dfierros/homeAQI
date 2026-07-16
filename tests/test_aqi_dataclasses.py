#!/usr/bin/env python
"""
Unit tests for AQ sensor dataclasses

"""

import pytest

from homeaqi.resources.aqi_dataclasses import AQConcentration, AQData, ParticleCounts

EXAMPLE_AQDATA: dict = {
    "pm10 standard": 1,
    "pm25 standard": 2,
    "pm100 standard": 3,
    "pm10 env": 4,
    "pm25 env": 5,
    "pm100 env": 6,
    "particles 03um": 7,
    "particles 05um": 8,
    "particles 10um": 9,
    "particles 25um": 10,
    "particles 50um": 11,
    "particles 100um": 12,
}


def test_aqdata_from_dict_constructs_nested_dataclasses():
    expected = AQData(
        standard=AQConcentration(pm10=1, pm25=2, pm100=3),
        environmental=AQConcentration(pm10=4, pm25=5, pm100=6),
        particles=ParticleCounts(
            particles_03_um=7,
            particles_05_um=8,
            particles_10_um=9,
            particles_25_um=10,
            particles_50_um=11,
            particles_100_um=12,
        ),
    )

    actual = AQData.from_dict(EXAMPLE_AQDATA)

    assert actual == expected
    assert actual.standard.pm25 == 2
    assert actual.environmental.pm10 == 4
    assert actual.particles.particles_100_um == 12


def test_aqdata_str_includes_expected_values():
    aqdata = AQData.from_dict(EXAMPLE_AQDATA)
    text = str(aqdata)

    assert "Concentration Units (standard)" in text
    assert "PM 1.0: 1" in text
    assert "PM2.5:  2" in text
    assert "PM10:  3" in text
    assert "PM 1.0: 4" in text
    assert "Particles > 10 um / 0.1L air: 12" in text


def test_nested_dataclasses_are_frozen():
    aqdata = AQData.from_dict(EXAMPLE_AQDATA)

    with pytest.raises(AttributeError):
        aqdata.standard.pm10 = 100


def test_from_dict_raises_key_error_for_missing_fields():
    incomplete_data = EXAMPLE_AQDATA.copy()
    incomplete_data.pop("pm25 env")

    with pytest.raises(KeyError):
        AQData.from_dict(incomplete_data)
