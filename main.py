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
TOPIC_PUB_TIME = "Test/SQM/time"
TOPIC_PUB_PARAMS = "Test/SQM/Params"

# Constants for sky brightness calculation
# M = M0 + GA - 2.5 * log10(Counts)
M0 = -16.07
GA = 25.55  # Glass attenuation factor

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
    print(f"Message received on {msg.topic}: {msg.payload.decode()}")

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
    # Continue without MQTT if fails? Or exit?
    # sys.exit(1) 
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
        # The new advanced_read() handles gain/time switching automatically
        full, ir = tsl.advanced_read()
        
        # Calculate flux in uW/cm2
        # calculate_light uses the current gain/time settings stored in the class
        full_C, ir_C = tsl.calculate_light(full, ir)
        
        # Calculate sky brightness (MPSAS)
        # Avoid log(0) errors
        flux_diff = full_C - ir_C
        if flux_diff > 0:
            mpsas = M0 + GA - 2.5 * math.log10(flux_diff)
        else:
            # Too dark to measure or error
            mpsas = 25.0 # Typical dark limit convention or -25 based on previous code
            
        # Format and publish messages
        mpsas_msg = f"{mpsas:.2f}"
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        if client.is_connected():
            client.publish(TOPIC_PUB, mpsas_msg, retain=True)
            client.publish(TOPIC_PUB_TIME, timestamp, retain=True)
            
            # Publish Gain and Integration Time params
            params_data = {
                "gain": tsl.gain,
                "integration_time_ms": tsl.get_int_time_ms()
            }
            client.publish(TOPIC_PUB_PARAMS, json.dumps(params_data), retain=True)
            
        print(f"MPSAS: {mpsas_msg} | Time: {tsl.get_int_time_ms()}ms | Gain: {tsl.gain} | Raw Full: {full}")
        
        # Write SQM value to JSON file
        sqm_data = {"AS_MPSAS": float(mpsas_msg)}
        json_path = "/home/pi/allsky/config/overlay/extra/allskytsl2591SQM.json"
        
        # Create directory if it doesn't exist
        try:
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            # Write JSON file
            with open(json_path, 'w') as f:
                json.dump(sqm_data, f)
        except Exception as e:
            print(f"File IO Error: {e}")
            
    except Exception as e:
        print(f"Error in measurement loop: {e}")
        # Reset sensor connection if needed
        # tsl = tsl2591.Tsl2591(1) 
        
    sleep(10)  # Wait 10 seconds between measurements