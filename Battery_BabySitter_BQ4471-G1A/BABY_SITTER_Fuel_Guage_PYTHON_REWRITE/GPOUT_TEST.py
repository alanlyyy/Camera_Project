"""Script used to read data from fuel guage ic"""

import pigpio
import struct
import sys
import time
import baby_sitter_python_write_example             #set design capacity
import baby_sitter_python_example                   #read stats
import baby_sitter_python_set_GPOUT                 #set GPOUT interrupt

GPOUT_PIN = 4
SET_CAPACITY = 2000

#opconfig register bit 2
BAT_LOW = 1
SOC_INT = 0

SOCI_SET = 15                                      # Interrupt set threshold at 20%
SOCI_CLR = 20                                      # Interrupt clear threshold at 25%
SOCF_SET = 5                                       # Final threshold set at 5%
SOCF_CLR = 10                                      # Final threshold clear at 10%

def setup(pi):

    pi.set_mode(GPOUT_PIN, pigpio.INPUT)
    pi.set_pull_up_down(GPOUT_PIN, pigpio.PUD_UP)                      #set pull up resistor
    
    baby_sitter_python_set_GPOUT.setGPOUTPolarity(pi, 0)                                            #Set GPOUT to active-high
    time.sleep(1)
    baby_sitter_python_set_GPOUT.setGPOUTFunction(pi,BAT_LOW)                                          #Set GPOUT to BAT_LOW mode
    time.sleep(1)
    baby_sitter_python_set_GPOUT.setSOC1Thresholds(pi,SOCI_SET, SOCI_CLR)                              #Set SOCI set and clear thresholds
    time.sleep(1)
    baby_sitter_python_set_GPOUT.setSOCFThresholds(pi,SOCF_SET, SOCF_CLR)                              #Set SOCF set and clear thresholds
    time.sleep(1)
    
    if (baby_sitter_python_set_GPOUT.read_GPOUTPolarity(pi)):
        print("GPOUT set to active-HIGH")
    else:
        print("GPOUT set to active-LOW")
    
    time.sleep(1)
    print("GPOUT_POLARITY OPCONFIG REGISTER: ", baby_sitter_python_set_GPOUT.read_opconfig_register(pi) )
    print("---")
    
    if (baby_sitter_python_set_GPOUT.read_GPOUTFunction(pi)):
        print("GPOUT function set to BAT_LOW")
    else:
        print("GPOUT function set to SOC_INT")
    time.sleep(1)
    
    print("GPOUT_FUNCTION OPCONFIG REGISTER: ", baby_sitter_python_set_GPOUT.read_opconfig_register(pi) )
    print("---")
    
    time.sleep(1)
    
    print("SOC1 Set Threshold: ", str((baby_sitter_python_set_GPOUT.read_SOC1SetThreshold(pi))) )
    time.sleep(1)
    
    print("SOC1 Clear Threshold: ", str((baby_sitter_python_set_GPOUT.read_SOC1ClearThreshold(pi))) )
    time.sleep(1)
    
    print("SOCF Set Threshold: ", str((baby_sitter_python_set_GPOUT.read_SOCFSetThreshold(pi))) )
    time.sleep(1)
    
    print("SOCF Clear Threshold: ", str((baby_sitter_python_set_GPOUT.read_SOCFClearThreshold(pi))) )
    time.sleep(1)
    
if  __name__ == '__main__':
    try:
        os.system("sudo pigpiod")
    except:
        print("daemon already running")
        
    pi_init = pigpio.pi()             # exit script if no connection
    if not pi_init.connected:
       exit()
        
    setup(pi_init)
    
    pi_init.stop()
    