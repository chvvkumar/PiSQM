# TSL2591 light sensor interface for Raspberry Pi
# Updated with robust Auto-Ranging for high dynamic range (Daylight to ~22 MPSAS)

import time
import smbus2

VISIBLE = 2
INFRARED = 1
FULLSPECTRUM = 0

SENSOR_ADDRESS = 0x29
READBIT = 0x01
COMMAND_BIT = 0xA0
CLEAR_BIT = 0x40
WORD_BIT = 0x20
BLOCK_BIT = 0x10

ENABLE_POWERON = 0x01
ENABLE_POWEROFF = 0x00
ENABLE_AEN = 0x02
ENABLE_AIEN = 0x10
CONTROL_RESET = 0x80

# Lux Coefficients
LUX_DF = 408.0
LUX_COEFB = 1.64
LUX_COEFC = 0.59
LUX_COEFD = 0.86

# Register Addresses
REGISTER_ENABLE = 0x00
REGISTER_CONTROL = 0x01
REGISTER_THRESHHOLDL_LOW = 0x02
REGISTER_THRESHHOLDL_HIGH = 0x03
REGISTER_THRESHHOLDH_LOW = 0x04
REGISTER_THRESHHOLDH_HIGH = 0x05
REGISTER_INTERRUPT = 0x06
REGISTER_CRC = 0x08
REGISTER_ID = 0x0A
REGISTER_CHAN0_LOW = 0x14
REGISTER_CHAN0_HIGH = 0x15
REGISTER_CHAN1_LOW = 0x16
REGISTER_CHAN1_HIGH = 0x17

# Integration Times
INTEGRATIONTIME_100MS = 0x00
INTEGRATIONTIME_200MS = 0x01
INTEGRATIONTIME_300MS = 0x02
INTEGRATIONTIME_400MS = 0x03
INTEGRATIONTIME_500MS = 0x04
INTEGRATIONTIME_600MS = 0x05

# Gains
GAIN_LOW = 0x00   # 1x
GAIN_MED = 0x10   # 25x
GAIN_HIGH = 0x20  # 428x
GAIN_MAX = 0x30   # 9876x

class Tsl2591:
    def __init__(self, sensor_id, integration=INTEGRATIONTIME_200MS, gain=GAIN_MED):
        self.sensor_id = sensor_id
        self.bus = smbus2.SMBus(1)
        self.integration_time = integration
        self.gain = gain
        
        # Apply initial settings without disabling immediately
        self.set_timing(self.integration_time)
        self.set_gain(self.gain)
        self.disable() # Start in disabled state

    def enable(self):
        """Enable the sensor (Power ON + ALS Enable)"""
        self.bus.write_byte_data(
            SENSOR_ADDRESS,
            COMMAND_BIT | REGISTER_ENABLE,
            ENABLE_POWERON | ENABLE_AEN | ENABLE_AIEN
        )

    def disable(self):
        """Disable the sensor"""
        self.bus.write_byte_data(
            SENSOR_ADDRESS,
            COMMAND_BIT | REGISTER_ENABLE,
            ENABLE_POWEROFF
        )

    def set_timing(self, integration):
        """Set integration time without full power toggle cycle"""
        self.integration_time = integration
        # We only need to enable to write registers, but we shouldn't force a full disable after
        # best practice: modify control register, ensuring device is on if we want it on.
        # For simplicity here: enable, write, leave enabled if it was enabled, 
        # but since we track state in advanced_read, we just write.
        self.enable()
        self.bus.write_byte_data(
            SENSOR_ADDRESS,
            COMMAND_BIT | REGISTER_CONTROL,
            self.integration_time | self.gain
        )
        # Note: Changing timing resets the ADC integration cycle

    def set_gain(self, gain):
        """Set gain without full power toggle cycle"""
        self.gain = gain
        self.enable()
        self.bus.write_byte_data(
            SENSOR_ADDRESS,
            COMMAND_BIT | REGISTER_CONTROL,
            self.integration_time | self.gain
        )
        # Note: Changing gain resets the ADC integration cycle

    def get_int_time_ms(self):
        """Helper to return integration time in milliseconds"""
        case_integ = {
            INTEGRATIONTIME_100MS: 100,
            INTEGRATIONTIME_200MS: 200,
            INTEGRATIONTIME_300MS: 300,
            INTEGRATIONTIME_400MS: 400,
            INTEGRATIONTIME_500MS: 500,
            INTEGRATIONTIME_600MS: 600
        }
        return case_integ.get(self.integration_time, 100)

    def calculate_light(self, full, ir):
        """Convert raw counts to uW/cm2 based on current gain/time settings"""
        if (full >= 0xFFFF) or (ir >= 0xFFFF):
            # Saturated
            return 0.0, 0.0
            
        atime = float(self.get_int_time_ms())

        case_gain = {
            GAIN_LOW: 1.,
            GAIN_MED: 24.5,
            GAIN_HIGH: 400.,
            GAIN_MAX: 9876.
        }
        again = case_gain.get(self.gain, 24.5)

        # spec sheet: 264.1 counts per uW/cm2 at GAIN_HIGH (400) and 100ms
        # Formula: counts = (Irradiance) * (Time/100) * (Gain/400) * 264.1
        # Irradiance = counts / ((Time/100) * (Gain/400) * 264.1)
        
        cpuW0 = (atime / 100.0) * (again / 400.0) * 264.1
        
        # Avoid division by zero
        if cpuW0 == 0:
            return 0.0, 0.0

        fullc = full / cpuW0
        irc = ir / cpuW0
        return fullc, irc

    def read_word(self, register):
        """Read a word from the I2C device"""
        try:
            return self.bus.read_word_data(SENSOR_ADDRESS, COMMAND_BIT | register)
        except Exception as e:
            print(f"I2C Read Error: {e}")
            return 0

    def advanced_read(self):
        """
        Auto-ranging read function.
        Adjusts gain and integration time to find the best signal.
        Handles extremely bright (saturation) and very dark (noise) conditions.
        """
        self.enable()
        
        # Max attempts to find range
        max_attempts = 15
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            # 1. Wait for integration time + margin
            wait_time = (self.get_int_time_ms() / 1000.0) + 0.12 # 120ms margin
            time.sleep(wait_time)
            
            # 2. Read values
            full = self.read_word(REGISTER_CHAN0_LOW)
            ir = self.read_word(REGISTER_CHAN1_LOW)
            
            # 3. Check Saturation (Too Bright)
            # 0xFFFF is logical max, but TSL2591 often clips around 0xFFE0 or lower depending on temp
            if full > 60000: 
                # Decrease signal: Reduce Gain first, then Time
                changed = False
                if self.gain > GAIN_LOW:
                    # Drop gain step by step
                    if self.gain == GAIN_MAX: self.set_gain(GAIN_HIGH)
                    elif self.gain == GAIN_HIGH: self.set_gain(GAIN_MED)
                    elif self.gain == GAIN_MED: self.set_gain(GAIN_LOW)
                    changed = True
                elif self.integration_time > INTEGRATIONTIME_100MS:
                    # Gain is already Low, reduce time
                    # Logic: decrement integration time index
                    new_time = self.integration_time - 1
                    self.set_timing(new_time)
                    changed = True
                
                if changed:
                    continue # Retry measurement with new settings
                else:
                    # At absolute min settings and still saturated
                    break

            # 4. Check Low Signal (Too Dark)
            # If counts are very low, resolution is poor. Increase signal.
            # Using 200 counts as a safe lower threshold for good data.
            if full < 200:
                changed = False
                if self.gain < GAIN_MAX:
                    # Increase gain
                    if self.gain == GAIN_LOW: self.set_gain(GAIN_MED)
                    elif self.gain == GAIN_MED: self.set_gain(GAIN_HIGH)
                    elif self.gain == GAIN_HIGH: self.set_gain(GAIN_MAX)
                    changed = True
                elif self.integration_time < INTEGRATIONTIME_600MS:
                    # Gain is Max, increase time
                    new_time = self.integration_time + 1
                    self.set_timing(new_time)
                    changed = True
                
                if changed:
                    continue # Retry measurement
                else:
                    # At absolute max settings
                    break

            # If we are here, the reading is within valid range (200 < full < 60000)
            break
            
        self.disable()
        return full, ir