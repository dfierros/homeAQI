# AQI Categories enumerations
from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class StrMinMaxEnum(StrEnum):
    def __new__(cls, value: str, minimum: float, maximum: float):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.minimum = minimum
        obj.maximum = maximum
        return obj


class AQISensorBreakpoints(StrMinMaxEnum):
    GOOD = "Good", 0.0, 12.0
    MODERATE = "Moderate", 12.1, 35.4
    UNHEALTHY_SENSITIVE = "Unhealthy for Sensitive Groups (USG)", 35.5, 55.4
    UNHEALTHY = "Unhealthy", 55.5, 150.4
    VERY_UNHEALTHY = "Very Unhealthy", 150.5, 250.4
    LOW_HAZARDOUS = "Hazardous", 250.5, 350.4
    HIGH_HAZARDOUS = "Hazardous", 350.5, 500.4

    def __contains__(self, aqi: int) -> bool:
        if self.minimum <= aqi <= self.maximum:
            return True
        return False
