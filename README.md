# PiSQM - Sky Quality Meter for Raspberry Pi

Automated sky brightness monitoring system using the TSL2591 light sensor and INA260 power sensor with MQTT telemetry and Home Assistant integration.

## Overview

PiSQM measures sky brightness in magnitudes per square arcsecond (MPSAS) using a TSL2591 digital light sensor. The system features adaptive auto-ranging for measurements from daylight conditions to dark sky readings (~22 MPSAS). It also monitors power consumption using an INA260 sensor. Measurements are published via MQTT with automatic Home Assistant discovery support.

Inspired by [rabssm/Radiometer](https://github.com/rabssm/Radiometer).

## Prerequisites

### Hardware

- Raspberry Pi (any model with I2C GPIO pins)
- TSL2591 light sensor module
- INA260 power sensor module
- Jumper wires for I2C connection
- Weatherproof enclosure (for outdoor deployment)

### Software

- Raspberry Pi OS (Raspbian Buster or later)
- Python 3.7 or higher
- I2C interface enabled
- MQTT broker (e.g., Mosquitto) accessible on the network
- systemd (for service installation)

### Network

- Active network connection
- Access to MQTT broker (default port 1883)

## Installation

### 1. Enable I2C Interface

Enable the I2C bus on the Raspberry Pi:

```bash
sudo raspi-config
```

Navigate to: **Interface Options → I2C → Enable**

Install I2C utilities:

```bash
sudo apt-get update
sudo apt-get install -y i2c-tools python3-venv git
```

### 2. Verify Sensor Connection

Connect the TSL2591 and INA260 sensors to the Raspberry Pi I2C pins:

| Sensor Pin | Raspberry Pi Pin | GPIO Function |
|-------------|------------------|---------------|
| VIN         | Pin 1            | 3.3V          |
| GND         | Pin 6            | Ground        |
| SDA         | Pin 3            | GPIO2 (SDA)   |
| SCL         | Pin 5            | GPIO3 (SCL)   |

Verify the sensors are detected at address `0x29` (TSL2591) and `0x40` (INA260):

```bash
sudo i2cdetect -y 1
```

Expected output shows `29` and `40` in the grid.

### 3. Clone Repository

```bash
cd ~
git clone <repository-url> PiSQM
cd PiSQM
```

### 4. Configure MQTT Settings

Edit MQTT broker settings in [main.py](main.py):

```python
MQTT_SERVER = "192.168.1.250"  # Replace with your MQTT broker IP
TOPIC_SUB = "Test/SQM/sub"      # Topic for remote configuration
TOPIC_PUB = "Test/SQM"          # Topic for MPSAS readings
TOPIC_PUB_PARAMS = "Test/SQM/Params"  # Topic for detailed parameters
```

Optionally configure Home Assistant discovery:

```python
HA_DISCOVERY_PREFIX = "homeassistant"  # Default HA discovery prefix
HA_NODE_ID = "sqm_reader"              # Unique device ID
```

### 5. Automated Service Installation

Run the installation script with sudo:

```bash
sudo ./install.sh
```

The script will:
- Fetch latest updates from git
- Create a Python virtual environment
- Install dependencies from `requirements.txt`
- Generate and install systemd service file
- Enable auto-start on boot
- Start the service

### 6. Manual Installation (Alternative)

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Run manually:

```bash
python3 main.py
```

## Configuration

### Calibration Parameters

Edit these values in [main.py](main.py) based on your setup:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `M0` | -16.07 | Magnitude zero point for sensor calibration |
| `GA` | 28.02 | Glass attenuation factor (accounts for enclosure transmission loss) |
| `MEASURE_INTERVAL` | 10 | Seconds between measurements |

**Note:** `GA` must be calibrated for your specific enclosure. Higher values indicate more light loss through glass/acrylic.

### Remote Configuration via MQTT

Send a JSON payload to the subscription topic to update parameters without restarting:

```bash
mosquitto_pub -h <broker-ip> -t "Test/SQM/sub" -m '{"M0": -16.0, "GA": 28.5, "interval": 15}'
```

Supported parameters:
- `M0`: Magnitude zero point
- `GA`: Glass attenuation
- `interval`: Measurement interval in seconds

### Allsky Integration

The system writes SQM data to a JSON file for Allsky integration:

```
/home/pi/allsky/config/overlay/extra/allskytsl2591SQM.json
```

Format:
```json
{"AS_MPSAS": 21.45}
```

## Usage

### Service Management

Check service status:

```bash
sudo systemctl status pisqm.service
```

Start the service:

```bash
sudo systemctl start pisqm.service
```

Stop the service:

```bash
sudo systemctl stop pisqm.service
```

Restart the service:

```bash
sudo systemctl restart pisqm.service
```

View real-time logs:

```bash
sudo journalctl -u pisqm.service -f
```

### Expected Output

Console output during operation:

```
Initializing TSL2591...
Initializing INA260...
Publishing Home Assistant Auto Discovery payloads...
Connected to MQTT broker with result code 0
Starting auto-ranging measurement loop...
MPSAS: 21.34 | Time: 200ms | Gain: 16 | Interval: 10s
MPSAS: 21.38 | Time: 200ms | Gain: 16 | Interval: 10s
```

### MQTT Topics

Published data:

| Topic | Format | Retain | Description |
|-------|--------|--------|-------------|
| `Test/SQM` | `21.34` | Yes | Current MPSAS reading (string) |
| `Test/SQM/Params` | JSON | Yes | Full parameters including gain, integration time, config |

Example `Test/SQM/Params` payload:

```json
{
  "sqm": 21.34,
  "gain": 16,
  "integration_time_ms": 200,
  "timestamp": "2025-12-24 14:30:45",
  "config_M0": -16.07,
  "config_GA": 28.02,
  "ina260_current": 0.1,
  "ina260_voltage": 12.1,
  "ina260_power": 1.2,
  "ina260_current_avg": 0.1,
  "ina260_current_min": 0.0,
  "ina260_current_max": 0.2,
  "ina260_voltage_avg": 12.1,
  "ina260_voltage_min": 12.0,
  "ina260_voltage_max": 12.2,
  "ina260_power_avg": 1.2,
  "ina260_power_min": 0.0,
  "ina260_power_max": 2.4
}
```

### Home Assistant Integration

The system publishes MQTT discovery messages on startup. Entities appear automatically in Home Assistant:

- **SQM** (mpsas) - Primary sky quality measurement
- **INA260 Current** (A)
- **INA260 Voltage** (V)
- **INA260 Power** (W)
- **INA260 Current Avg** (A)
- **INA260 Current Min** (A)
- **INA260 Current Max** (A)
- **INA260 Voltage Avg** (V)
- **INA260 Voltage Min** (V)
- **INA260 Voltage Max** (V)
- **INA260 Power Avg** (W)
- **INA260 Power Min** (W)
- **INA260 Power Max** (W)
- **Sensor Gain** (diagnostic)
- **Integration Time** (diagnostic)
- **Config M0** (diagnostic)
- **Config GA** (diagnostic)
- **Last Update** (diagnostic)

## Auto-Ranging Behavior

The TSL2591 driver implements adaptive auto-ranging:

1. **Saturation Detection**: If counts exceed 60,000, gain or integration time is reduced
2. **Low Signal Detection**: If counts fall below 200, gain or integration time is increased
3. **Range Priority**: Gain is adjusted before integration time
4. **Valid Range**: System targets 200-60,000 counts for optimal precision

This enables accurate measurements from bright daylight to extremely dark skies without manual intervention.

## Troubleshooting

### I2C Communication Errors

**Symptom:** `OSError: [Errno 121] Remote I/O error` or sensor not detected

**Resolution:**
1. Verify I2C is enabled: `sudo raspi-config`
2. Check wiring connections
3. Confirm sensor address: `sudo i2cdetect -y 1`
4. Test with different I2C pull-up resistors if using long cables
5. Verify 3.3V power supply is stable

### MQTT Connection Failures

**Symptom:** `Failed to connect to MQTT broker` or continuous reconnection attempts

**Resolution:**
1. Verify MQTT broker is running: `sudo systemctl status mosquitto`
2. Test network connectivity: `ping <broker-ip>`
3. Check firewall rules allow port 1883
4. Verify `MQTT_SERVER` IP address in [main.py](main.py)
5. Check broker authentication settings (anonymous access may be disabled)

### Service Fails to Start

**Symptom:** `systemctl status pisqm.service` shows failed state

**Resolution:**
1. Check logs: `sudo journalctl -u pisqm.service -n 50`
2. Verify Python dependencies: `source venv/bin/activate && pip list`
3. Confirm file permissions: `ls -l /home/pi/PiSQM`
4. Ensure user `pi` has I2C access: `sudo usermod -a -G i2c pi`
5. Reboot and retry: `sudo reboot`

### Unrealistic MPSAS Readings

**Symptom:** Readings consistently too high/low or unstable

**Resolution:**
1. Calibrate `M0` and `GA` parameters using a reference SQM device
2. Ensure sensor is not obstructed or contaminated
3. Verify enclosure transmission characteristics match `GA` value
4. Check for nearby light sources causing interference
5. Review integration time and gain in diagnostic output

### File IO Errors (Allsky JSON)

**Symptom:** `File IO Error: [Errno 2] No such file or directory`

**Resolution:**
1. Create directory manually: `sudo mkdir -p /home/pi/allsky/config/overlay/extra`
2. Set permissions: `sudo chown -R pi:pi /home/pi/allsky`
3. Comment out file write section in [main.py](main.py) if Allsky integration is not needed

## Uninstallation

Remove the service and clean up:

```bash
sudo ./uninstall.sh
```

This will:
- Stop the service
- Disable auto-start
- Remove systemd service file
- Reload systemd daemon

The project directory and virtual environment remain intact for potential reinstallation.

## Project Structure

```
PiSQM/
├── main.py                      # Main application entry point
├── tsl2591.py                   # TSL2591 sensor driver with auto-ranging
├── ina260.py                    # INA260 sensor driver
├── requirements.txt             # Python dependencies
├── install.sh                   # Automated installation script
├── uninstall.sh                 # Service removal script
├── pisqm.service.template       # systemd service template
├── README.md                    # This file
└── CONTEXT_DOCUMENTATION.md     # Project context notes
```

## Technical Details

### Measurement Formula

```
MPSAS = M0 + GA - 2.5 × log₁₀(flux_diff)
```

Where:
- `flux_diff` = Full spectrum counts - IR counts (in µW/cm²)
- `M0` = Magnitude zero point calibration
- `GA` = Glass attenuation factor

### TSL2591 Specifications

- I2C Address: `0x29`
- Gain Settings: 1×, 25×, 428×, 9876×
- Integration Times: 100ms, 200ms, 300ms, 400ms, 500ms, 600ms
- Dynamic Range: ~188,000,000:1
- Spectral Responsivity: 400-1050nm

## Attribution

Based on concepts from Richard's ESP-based radiometer: https://github.com/rabssm/Radiometer

## References

- TSL2591 Datasheet: https://ams.com/documents/20143/36005/TSL2591_DS000338_6-00.pdf
- INA260 Datasheet: https://www.ti.com/lit/ds/symlink/ina260.pdf
- Sky Quality Measurement theory: https://www.mnassa.org.za/html/Oct2017/2017MNASSA..76..Oct..215.pdf
