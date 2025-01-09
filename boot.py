# Complete project details at https://RandomNerdTutorials.com

import time
from umqttsimple import MQTTClient
import ubinascii
import machine
import micropython
import network
import esp
import ntptime
import sys
#esp.osdebug(None)
import gc
import webrepl
#import webrepl_setup
webrepl.start()
from utime import sleep

gc.collect()

from WIFI_CONFIG_OTA import SSID, PASSWORD, MQTT_SERVER, TOPIC_SUB, TOPIC_PUB, TOPIC_PUB_TIME

ssid = SSID
password = PASSWORD

mqtt_server = MQTT_SERVER
client_id = ubinascii.hexlify(machine.unique_id())
topic_sub = TOPIC_SUB
topic_pub = TOPIC_PUB
topic_pub_time = TOPIC_PUB_TIME

last_message = 0
message_interval = 10

# intitialise WIFI
network.country("US")
station = network.WLAN(network.STA_IF)

sta_if = network.WLAN(network.STA_IF)

sta_if.active(False)
sta_if.active(True)

hostname = "sqmmeter"
sta_if.config(dhcp_hostname=hostname)

if not sta_if.isconnected():
     loopnum = 0
     try:
         sta_if.active(True)
         sta_if.config(txpower=10)
         sta_if.connect(ssid, password)
         print('Maybe connected now: {}...'.format(sta_if.status()))
         sleep(1)
     except:
         print("well that attempt failed")
         sta_if.disconnect()
         sta_if.active(False)

     while loopnum < 10:
         print('Got status {}...'.format(sta_if.status()))
         if sta_if.status() == 1010: #CONNECTED
             print(station.ifconfig())
             break
         loopnum = loopnum + 1
         sleep(1)

try:
    ntptime.settime()
except Exception as e:
    sys.print_exception(e)


