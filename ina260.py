
import board
import adafruit_ina260

class INA260:
    def __init__(self, i2c_address=0x40):
        self._i2c = board.I2C()
        self._ina260 = adafruit_ina260.INA260(self._i2c, i2c_address)

    def read(self):
        """
        Reads the current, voltage and power from the INA260 sensor.
        """
        return {
            "current": self._ina260.current,
            "voltage": self._ina260.voltage,
            "power": self._ina260.power
        }
