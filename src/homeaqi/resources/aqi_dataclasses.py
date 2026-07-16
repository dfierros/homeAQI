#!/usr/bin/env python
"""
Dataclasses for storage and communication of AQ sensor data

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class AQConcentration:
    pm10: int
    pm25: int
    pm100: int


@dataclass(frozen=True)
class ParticleCounts:
    particles_03_um: int
    particles_05_um: int
    particles_10_um: int
    particles_25_um: int
    particles_50_um: int
    particles_100_um: int


@dataclass(frozen=True)
class AQData:
    standard: AQConcentration
    environmental: AQConcentration
    particles: ParticleCounts

    @classmethod
    def from_dict(cls, data: Mapping[str, int]) -> AQData:
        return cls(
            standard=AQConcentration(
                pm10=data["pm10 standard"],
                pm25=data["pm25 standard"],
                pm100=data["pm100 standard"],
            ),
            environmental=AQConcentration(
                pm10=data["pm10 env"],
                pm25=data["pm25 env"],
                pm100=data["pm100 env"],
            ),
            particles=ParticleCounts(
                particles_03_um=data["particles 03um"],
                particles_05_um=data["particles 05um"],
                particles_10_um=data["particles 10um"],
                particles_25_um=data["particles 25um"],
                particles_50_um=data["particles 50um"],
                particles_100_um=data["particles 100um"],
            ),
        )

    def __str__(self) -> str:
        return (
            "PM2.5 Data Frame\n"
            "Concentration Units (standard)\n"
            "---------------------------------------\n"
            f"PM 1.0: {self.standard.pm10}\tPM2.5:  {self.standard.pm25}\tPM10:  {self.standard.pm100}\n"
            "Concentration Units (environmental)\n"
            "---------------------------------------\n"
            f"PM 1.0: {self.environmental.pm10}\tPM2.5:  {self.environmental.pm25}\tPM10:  {self.environmental.pm100}\n"
            "---------------------------------------\n"
            f"Particles > 0.3um / 0.1L air: {self.particles.particles_03_um}\n"
            f"Particles > 0.5um / 0.1L air: {self.particles.particles_05_um}\n"
            f"Particles > 1.0um / 0.1L air: {self.particles.particles_10_um}\n"
            f"Particles > 2.5um / 0.1L air: {self.particles.particles_25_um}\n"
            f"Particles > 5.0um / 0.1L air: {self.particles.particles_50_um}\n"
            f"Particles > 10 um / 0.1L air: {self.particles.particles_100_um}\n"
            "---------------------------------------\n"
        )
