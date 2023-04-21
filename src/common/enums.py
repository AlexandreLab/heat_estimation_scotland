from enum import Enum, auto


class dwelling_types(Enum):
    SEMIDETACHED = "semi-detached"
    TERRACED = "terraced"
    DETACHED = "detached"
    FLAT = "flat"


class heating_systems(Enum):
    RESISTANCE = "resistance"
    HP = "heat pump"
    GASBOILER = "gas boiler"
    SOLIDFUELBOILER = "solid fuel boiler"
    OILBOILER = "oil boiler"
    UNCATEGORIZED = "uncategorized"
    DH = "district heating"


class heating_fuels(Enum):
    ELECTRICITY = auto()
    NATURALGAS = auto()
    OIL = auto()
    SOLIDFUEL = auto()
    UNCATEGORIZED = auto()