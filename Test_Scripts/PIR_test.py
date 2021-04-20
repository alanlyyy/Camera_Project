import sys
import pigpio
import DHT
import time
import datetime
from os import system

pi = pigpio.pi()
if not pi.connected:
    exit()

PIR = 27 #GPIO27 & pin 13

pi.set_mode(PIR, pigpio.INPUT)    #set gpio17 as input
pi.set_pull_up_down(PIR,pigpio.PUD_DOWN) #enable pull down resistor
while True:
    if (pi.read(PIR)):
        print("PIR is working")
    
exit()