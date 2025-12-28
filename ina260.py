import smbus2

class INA260:
    """
    Simple INA260 Power Monitor Reader
    Address: 0x40
    """

    INA260_ADDR = 0x40

    REG_CURRENT = 0x01      # Current register (LSB = 1.25 mA)
    REG_VOLTAGE = 0x02      # Bus voltage register (LSB = 1.25 mV)
    REG_POWER = 0x03        # Power register (LSB = 10 mW)
    REG_MFG_ID = 0xFE       # Manufacturer ID (should be 0x5449 = "TI")
    REG_DIE_ID = 0xFF       # Die ID (should be 0x2270 for INA260)

    def __init__(self, bus=1):
        self.bus = smbus2.SMBus(bus)

    def _read_register(self, reg):
        """Read a 16-bit register (big-endian)"""
        data = self.bus.read_i2c_block_data(self.INA260_ADDR, reg, 2)
        return (data[0] << 8) | data[1]

    def _read_signed_register(self, reg):
        """Read a signed 16-bit register"""
        value = self._read_register(reg)
        if value >= 0x8000:
            value -= 0x10000
        return value

    def check_id(self):
        """Verify we're talking to an INA260"""
        mfg_id = self._read_register(self.REG_MFG_ID)
        die_id = self._read_register(self.REG_DIE_ID)
        if mfg_id != 0x5449 or die_id != 0x2270:
            raise RuntimeError("Failed to find INA260 chip")

    def read(self):
        """
        Reads the current, voltage and power from the INA260 sensor.
        """
        # Read raw values
        voltage_raw = self._read_register(self.REG_VOLTAGE)
        current_raw = self._read_signed_register(self.REG_CURRENT)
        power_raw = self._read_register(self.REG_POWER)

        # Convert to real units
        voltage = voltage_raw * 1.25 / 1000    # Convert to Volts
        current = current_raw * 1.25 / 1000   # Convert to Amps
        power = power_raw * 10 / 1000         # Convert to Watts

        return {
            "current": current,
            "voltage": voltage,
            "power": power
        }

    def close(self):
        self.bus.close()