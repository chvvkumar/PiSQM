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
from machine import I2C, RTC, WDT
from utime import sleep

wdt = WDT(timeout=30000)
M0 = -16.07
GA = 25.55  # this is a glass attenuation factor, depends on what's in front of the detector. Guesstimate

tsl = tsl2591.Tsl2591(1,2)
tsl.set_gain(tsl2591.GAIN_MED)
tsl.set_timing(tsl2591.INTEGRATIONTIME_300MS)

def sub_cb(topic, msg):
  print((topic, msg))
  if topic == b'notification' and msg == b'received':
    print('ESP received hall value')

def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  client = MQTTClient(client_id, mqtt_server)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

try:
  client = connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()

while True:
  sleep(10)
  try:
      full, ir = tsl.advanced_read()
      full_C, ir_C = tsl.calculate_light(full, ir)
      if ((full_C - ir_C) != 0):
          mpsas = M0 + GA -2.5*math.log10(full_C - ir_C)
      else:
          mpsas = -25.
      mpsas_msg = b'{0:.2f}'.format(mpsas)
      client.publish(topic_pub, mpsas_msg)
      wdt.feed()
  except OSError as e:
      restart_and_reconnect()