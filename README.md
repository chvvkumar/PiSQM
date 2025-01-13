# PiSQM - Sky Quality Meter for Raspberry Pi

Heavily inspired by Richard's work on the ESP platform

https://github.com/rabssm/Radiometer

A Sky Quality Meter implementation for Raspberry Pi using the TSL2591 light sensor. This project measures sky brightness in magnitudes per square arcsecond (MPSAS) and publishes the readings to an MQTT broker.


## Hardware Requirements

- Raspberry Pi (any model with I2C pins)
- TSL2591 light sensor
- Appropriate housing/enclosure for outdoor use (if applicable)

## Installation

1. Enable I2C on your Raspberry Pi:
```bash
sudo raspi-config
# Navigate to: Interface Options -> I2C -> Enable
sudo apt-get install -y i2c-tools
```

2. Verify I2C connection:
```bash
sudo i2cdetect -y 1
# You should see the TSL2591 sensor at address 0x29.
```


3. Create virtual environment and Install required packages:

```bash
cd PiSQM

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or manually install dependencies
pip3 install smbus2 paho-mqtt
```

## Wiring

Connect the TSL2591 sensor to the Raspberry Pi:
- VIN -> 3.3V (Pin 1)
- GND -> Ground (Pin 6)
- SDA -> GPIO2/SDA (Pin 3)
- SCL -> GPIO3/SCL (Pin 5)

## Configuration

Edit the MQTT settings in `main.py`:
```python
MQTT_SERVER = "192.168.1.250"  # Your MQTT broker address
TOPIC_SUB = "Test/SQM/incoming"
TOPIC_PUB = "Test/SQM"
TOPIC_PUB_TIME = "Test/SQM/DateTime"
```

## Usage

Run the program:
```bash
python3 main.py
```

The program will:
1. Initialize the TSL2591 sensor
2. Connect to the MQTT broker
3. Take measurements every 10 seconds
4. Publish readings to the configured MQTT topic
5. Print readings to the console

To stop the program, press Ctrl+C for graceful shutdown.

## Calibration

The glass attenuation factor (GA) in main.py may need adjustment based on your setup:
```python
GA = 25.55  # Adjust based on your enclosure/setup
```

## Troubleshooting

1. If you get I2C errors:
   - Check wiring connections
   - Verify I2C is enabled: `sudo raspi-config`
   - Check sensor address: `sudo i2cdetect -y 1`

2. If MQTT connection fails:
   - Verify broker address and port
   - Check network connectivity
   - Ensure MQTT broker is running

## References

- TSL2591 Datasheet: https://ams.com/documents/20143/36005/TSL2591_DS000338_6-00.pdf
- Sky Quality Measurement theory: https://www.mnassa.org.za/html/Oct2017/2017MNASSA..76..Oct..215.pdf
