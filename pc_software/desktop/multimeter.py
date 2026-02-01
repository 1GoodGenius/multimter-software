import numpy as np
import random
import time
from enum import Enum

class MeasurementMode(Enum):
    DC_VOLTAGE = "DC Voltage"
    AC_VOLTAGE = "AC Voltage"
    DC_CURRENT = "DC Current"
    AC_CURRENT = "AC Current"
    RESISTANCE = "Resistance"
    CAPACITANCE = "Capacitance"
    CONTINUITY = "Continuity"
    DIODE = "Diode Test"
    FREQUENCY = "Frequency"
    TEMPERATURE = "Temperature"

# (rest of file copied verbatim into new location)
