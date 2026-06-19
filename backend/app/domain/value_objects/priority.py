from enum import StrEnum


class PriorityLevel(StrEnum):
    COLD = "COLD"
    WARM = "WARM"
    HOT = "HOT"
    IMMEDIATE = "IMMEDIATE"
