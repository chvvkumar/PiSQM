# SQM Reader with Auto-Ranging
# Uses TSL2591 to calculate MPSAS (Magnitudes Per Square Arc Second)

import tsl2591
import time
import math
import paho.mqtt.client as mqtt
from time import sleep
import sys
import signal
import json
import os

# MQTT Configuration
MQTT_SERVER = "192.168.1.250"
TOPIC_SUB = "Test/SQM/sub"
TOPIC_PUB = "Test/SQM"
TOPIC_PUB_PARAMS = "Test/SQM/Params"

# Global Configuration Variables (Can be updated via MQTT)
# M = M0 + GA - 2.5 * log10(Counts)
M0 = -16.07       # Magnitude Zero Point
GA = 25.55        # Glass Attenuation
MEASURE_INTERVAL = 10 # Seconds between readings

# Initialize the TSL2591 sensor
try:
    print("Initializing TSL2591...")
    # Initialize with default medium settings, auto-ranging will adjust
    tsl = tsl2591.Tsl2591(1, tsl2591.INTEGRATIONTIME_200MS, tsl2591.GAIN_MED)
except Exception as e:
    print(f"Failed to initialize TSL2591 sensor: {e}")
    sys.exit(1)

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(TOPIC_SUB)

def on_message(client, userdata, msg):
    """
    Handle incoming remote configuration messages.
    Expected Payload: JSON e.g. {"M0": -16.0, "GA": 25.0, "interval": 5}
    """
    global M0, GA, MEASURE_INTERVAL
    try:
        payload_str = msg.payload.decode()
        print(f"Message received on {msg.topic}: {payload_str}")
        
        data = json.loads(payload_str)
        
        if "M0" in data:
            M0 = float(data["M0"])
            print(f"Remote Config: Updated M0 to {M0}")
            
        if "GA" in data:
            GA = float(data["GA"])
            print(f"Remote Config: Updated GA to {GA}")
            
        if "interval" in data:
            MEASURE_INTERVAL = float(data["interval"])
            print(f"Remote Config: Updated Interval to {MEASURE_INTERVAL}s")
            
    except json.JSONDecodeError:
        print("Error: Received invalid JSON on subscription topic")
    except ValueError as e:
        print(f"Error: Invalid value format in configuration: {e}")
    except Exception as e:
        print(f"Error handling MQTT message: {e}")

def on_disconnect(client, userdata, rc):
    print(f"Disconnected from MQTT broker with result code {rc}")
    if rc != 0:
        print("Unexpected disconnection. Attempting to reconnect...")
        try:
            client.reconnect()
        except Exception as e:
            print(f"Failed to reconnect: {e}")

# Setup MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Connect to MQTT broker
try:
    client.connect(MQTT_SERVER, 1883, 60)
    client.loop_start()
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")
    print("Continuing without MQTT...")

# Handle graceful shutdown
def signal_handler(signum, frame):
    print("\nShutting down...")
    client.loop_stop()
    client.disconnect()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Main loop
print("Starting auto-ranging measurement loop...")
while True:
    try:
        # Read sensor data with Auto-Ranging
        full, ir = tsl.advanced_read()
        
        # Calculate flux in uW/cm2
        full_C, ir_C = tsl.calculate_light(full, ir)
        
        # Calculate sky brightness (MPSAS)
        flux_diff = full_C - ir_C
        if flux_diff > 0:
            mpsas = M0 + GA - 2.5 * math.log10(flux_diff)
        else:
            mpsas = 25.0 # Typical dark limit convention
            
        # Format and publish messages
        mpsas_msg = f"{mpsas:.2f}"
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        if client.is_connected():
            client.publish(TOPIC_PUB, mpsas_msg, retain=True)
            
            # Publish Params
            params_data = {
                "gain": tsl.gain,
                "integration_time_ms": tsl.get_int_time_ms(),
                "timestamp": timestamp,
                "config_M0": M0,
                "config_GA": GA
            }
            client.publish(TOPIC_PUB_PARAMS, json.dumps(params_data), retain=True)
            
        print(f"MPSAS: {mpsas_msg} | Time: {tsl.get_int_time_ms()}ms | Gain: {tsl.gain} | Interval: {MEASURE_INTERVAL}s")
        
        # Write SQM value to JSON file
        sqm_data = {"AS_MPSAS": float(mpsas_msg)}
        json_path = "/home/pi/allsky/config/overlay/extra/allskytsl2591SQM.json"
        
        # Create directory if it doesn't exist
        try:
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, 'w') as f:
                json.dump(sqm_data, f)
        except Exception as e:
            print(f"File IO Error: {e}")
            
    except Exception as e:
        print(f"Error in measurement loop: {e}")
        
    sleep(MEASURE_INTERVAL)