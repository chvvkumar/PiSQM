# https://www.mnassa.org.za/html/Oct2017/2017MNASSA..76..Oct..215.pdf
#
# I = 3.719 x 10^(-9-0.4*M)  W/m2s2
#
# 1 W/m2 = 1 W/10^4 cm2 = 10^-4 W/cm2 = 100 uW/cm2
#
# I = 3.719 x 10^(-7-0.4*M)  uW/cm2s2
#
# from datasheet: at gain = 400 and T = 100 ms, 264 counts / uW/cm2
# this conversion is done in tsl2591.calculate_light()
# 
# log (I) = log (3.719) - 7 - 0.4 M
#
# M = -16.07 - 2.5*log(C)

import tsl2591
import time
import math
import paho.mqtt.client as mqtt
from time import sleep
import sys
import signal

# WiFi Configuration
SSID = "IoT"
PASSWORD = "kkkkkkkk"

# Constants from WIFI_CONFIG_OTA.py
MQTT_SERVER = "192.168.1.250"
TOPIC_SUB = "Test/SQM/incoming"
TOPIC_PUB = "Test/SQM"
TOPIC_PUB_TIME = "Test/SQM/DateTime"

# Constants for sky brightness calculation
M0 = -16.07
GA = 25.55  # this is a glass attenuation factor, depends on what's in front of the detector. Guesstimate

# Initialize the TSL2591 sensor
try:
    tsl = tsl2591.Tsl2591(1)
    tsl.set_gain(tsl2591.GAIN_MED)
    tsl.set_timing(tsl2591.INTEGRATIONTIME_300MS)
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
    sys.exit(1)

# Handle graceful shutdown
def signal_handler(signum, frame):
    print("\nShutting down...")
    client.loop_stop()
    client.disconnect()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Main loop
print("Starting measurement loop...")
while True:
    try:
        # Read sensor data
        full, ir = tsl.advanced_read()
        full_C, ir_C = tsl.calculate_light(full, ir)
        
        # Calculate sky brightness
        if ((full_C - ir_C) != 0):
            mpsas = M0 + GA - 2.5 * math.log10(full_C - ir_C)
        else:
            mpsas = -25.
            
        # Format and publish messages
        mpsas_msg = f"{mpsas:.2f}"
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        client.publish(TOPIC_PUB, mpsas_msg, retain=True)
        client.publish(TOPIC_PUB_TIME, timestamp, retain=True)
        print(f"Published sky brightness: {mpsas_msg} MPSAS at {timestamp}")
        
    except Exception as e:
        print(f"Error in measurement loop: {e}")
        
    sleep(10)  # Wait 10 seconds between measurements
