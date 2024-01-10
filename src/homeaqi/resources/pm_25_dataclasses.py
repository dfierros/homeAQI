#!/usr/bin/env python
"""
Dataclasses for storage and communication of PM25 sensor data

"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PM25Data:
    # Standard concentration units
    pm_10_standard: int
    pm_25_standard: int
    pm_100_standard: int

    # Environmental concentration units
    pm_10_environment: int
    pm_25_environment: int
    pm_100_environment: int

    # Particles per 0.1L of air
    particles_03_um: int
    particles_05_um: int
    particles_10_um: int
    particles_25_um: int
    particles_50_um: int
    particles_100_um: int

    @classmethod
    def from_dict(cls, input_dict: dict) -> PM25Data:
        return cls(
            pm_10_standard=input_dict["pm10 standard"],
            pm_25_standard=input_dict["pm25 standard"],
            pm_100_standard=input_dict["pm100 standard"],
            pm_10_environment=input_dict["pm10 env"],
            pm_25_environment=input_dict["pm25 env"],
            pm_100_environment=input_dict["pm100 env"],
            particles_03_um=input_dict["particles 03um"],
            particles_05_um=input_dict["particles 05um"],
            particles_10_um=input_dict["particles 10um"],
            particles_25_um=input_dict["particles 25um"],
            particles_50_um=input_dict["particles 50um"],
            particles_100_um=input_dict["particles 100um"],
        )

    def __str__(self) -> str:
        return (
            "PM2.5 Data Frame\n"
            "Concentration Units (standard)\n"
            "---------------------------------------\n"
            f"PM 1.0: {self.pm_10_standard}\tPM2.5:  {self.pm_25_standard}\tPM10:  {self.pm_100_standard}\n"
            "Concentration Units (environmental)\n"
            "---------------------------------------\n"
            f"PM 1.0: {self.pm_10_environment}\tPM2.5:  {self.pm_25_environment}\tPM10:  {self.pm_100_environment}\n"
            "---------------------------------------\n"
            f"Particles > 0.3um / 0.1L air: {self.particles_03_um}\n"
            f"Particles > 0.5um / 0.1L air: {self.particles_05_um}\n"
            f"Particles > 1.0um / 0.1L air: {self.particles_10_um}\n"
            f"Particles > 2.5um / 0.1L air: {self.particles_25_um}\n"
            f"Particles > 5.0um / 0.1L air: {self.particles_50_um}\n"
            f"Particles > 10 um / 0.1L air: {self.particles_100_um}\n"
            "---------------------------------------\n"
        )
