import sys
import pigpio
import DHT
import time
import datetime
from os import system

pi = pigpio.pi()
if not pi.connected:
    exit()

push_button = 17 #GPIO17 & pin 11

pi.set_mode(17,pigpio.INPUT)    #set gpio17 as input
pi.set_pull_up_down(17,pigpio.PUD_UP) #enable pull up resistor


while True:
    if (pi.read(17)== 0):
        print("PB is working")
    