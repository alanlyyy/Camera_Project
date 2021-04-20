#!/usr/bin/env python3

# 2020-09-27
"""
    A Program to read the DHTXX temperature/humidity sensors.

    REQUIREMENTS
    DHT.py    download "module" from http://abyz.me.uk/rpi/pigpio/code/DHT.py
    pigpiod running (sudo pigpiod) before running script
"""

import sys
import pigpio
import DHT
import time
import datetime
from os import system

#setup DHT11 sensor
#run pigpiod before executing rest of the script.
try:
    system("sudo pigpiod")
except:
    print("daemon already running")

pi = pigpio.pi()
if not pi.connected:
    exit()

class DHT_Wrapper:
    """DHT_Wrapper is a child of DHT"""
    
    def __init__(self,pi, pin, sensor=1):
        #default DHT wrapper initializes uses 1 or DHT11 sensor
        self.s = DHT.sensor(pi, pin, model = sensor)
        self._last_temp_reading = 0
        

    def output_data(self,timestamp, temperature, humidity):
        #Prints the data in the shell -Sample output Date: Timestamp, Temperature: 25°C, Humidity: 72%
        date = datetime.datetime.fromtimestamp(timestamp).replace(microsecond=0).isoformat()
        print(u"Date: {:s}, Temperature: {:g}\u00b0C, Humidity: {:g}%".format(date, temperature, humidity))


    def get_current_temperature_reading(self):
        
        """read current temperature reading."""
        
        tries = 5   # try 5 times if error
        
        while tries:
            try:
                
                timestamp, gpio, status, temperature, humidity = self.s.read()   #read DHT device
                
                if(status == DHT.DHT_TIMEOUT):  # no response from sensor
                    #exit()
                    break
                    
                if(status == DHT.DHT_GOOD):
                    print("Good Status")
                    self.output_data(timestamp, temperature, humidity)
                    
                    #record the last temperature reading
                    self._last_temp_reading = temperature
                    
                    #exit()      # Exit after successful read
                    break
                
                #get reading at 2 second intervals
                time.sleep(2)
                
                tries -=1
            
            except KeyboardInterrupt:
                exit()
                
    def get_last_temp_reading(self):
        return self._last_temp_reading
        
if __name__ == '__main__':
    
    # Sensor should be set to DHT.DHT11, DHT.DHTXX or DHT.DHTAUTO
    sensor = DHT.DHT11
    
    # Data - Pin 7 (BCM 4)
    pin = 4
    
    push_button = 17 #GPIO17 & pin 11
    
    pi.set_mode(17,pigpio.INPUT)    #set gpio17 as input
    pi.set_pull_up_down(17,pigpio.PUD_UP) #enable pull down resistor
    
    dht_sensor = DHT_Wrapper(pi,pin,sensor)
    
    #if push button is pressed get current temperature reading.
    while True:
        
        #if push button is pressed, get and print reading.
        if (pi.read(17) == 0):
            print(True)
            dht_sensor.get_current_temperature_reading()
            print(dht_sensor.get_last_temp_reading())
         