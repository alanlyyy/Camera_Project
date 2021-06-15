"""Script used to read data from fuel guage ic"""

import pigpio
import struct
import sys
import time
import baby_sitter_python_write_example             #set design capacity
import baby_sitter_python_example                   #read stats

GPOUT_PIN = 4
SET_CAPACITY = 2000

#opconfig register bit 2
BAT_LOW = 1
SOC_INT = 0

SOCI_SET = 15                                      # Interrupt set threshold at 20%
SOCI_CLR = 20                                      # Interrupt clear threshold at 25%
SOCF_SET = 5                                       # Final threshold set at 5%
SOCF_CLR = 10                                      # Final threshold clear at 10%

if sys.version > '3':
   buffer = memoryview
   
def setup(pi):
    pi.set_mode(GPOUT_PIN, pigpio.INPUT)
    pi.set_pull_up_down(GPOUT_PIN, pigpio.PUD_UP)                      #set pull up resistor
    
    baby_sitter_python_write_example.enterConfig(pi)
    time.sleep(1)
    baby_sitter_python_write_example.set_capacity(pi,SET_CAPACITY)
    time.sleep(1)
    
    setGPOUTPolarity(pi, 0)                                            #Set GPOUT to active-high
    time.sleep(1)
    setGPOUTFunction(pi,BAT_LOW)                                          #Set GPOUT to BAT_LOW mode
    time.sleep(1)
    setSOC1Thresholds(pi,SOCI_SET, SOCI_CLR)                              #Set SOCI set and clear thresholds
    time.sleep(1)
    setSOCFThresholds(pi,SOCF_SET, SOCF_CLR)                              #Set SOCF set and clear thresholds
    time.sleep(1)
    baby_sitter_python_write_example.exitConfig(pi)
    time.sleep(1)
    
    if (read_GPOUTPolarity(pi)):
        print("GPOUT set to active-HIGH")
    else:
        print("GPOUT set to active-LOW")
    
    time.sleep(1)
    print("GPOUT_POLARITY OPCONFIG REGISTER: ", read_opconfig_register(pi) )
    print("---")
    
    
    if (read_GPOUTFunction(pi)):
        print("GPOUT function set to BAT_LOW")
    else:
        print("GPOUT function set to SOC_INT")
    time.sleep(1)
    
    print("GPOUT_FUNCTION OPCONFIG REGISTER: ", read_opconfig_register(pi) )
    print("---")
    time.sleep(1)
    
    print("SOC1 Set Threshold: ", str((read_SOC1SetThreshold(pi))) )
    time.sleep(1)
    
    print("SOC1 Clear Threshold: ", str((read_SOC1ClearThreshold(pi))) )
    time.sleep(1)
    
    print("SOCF Set Threshold: ", str((read_SOCFSetThreshold(pi))) )
    time.sleep(1)
    
    print("SOCF Clear Threshold: ", str((read_SOCFClearThreshold(pi))) )
    time.sleep(1)
    
def read_opconfig_register(pi):
    #BQ27441_EXTENDED_OPCONFIG  0x3A // OpConfig()
    
    #quick write to opConfig register
    handle = pi.i2c_open(1, 0x55)   
    pi.i2c_write_byte(handle, 0x3A) 
    pi.i2c_close(handle)
    
    #quick read OPCONFIG REGISTER
    handle = pi.i2c_open(1,0x55)
    (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
    pi.i2c_close(handle)
    
    
    #the number of bytes d has to equal format string. (here requesting 2 unsigned char 1 byte each for d0 and d1)
    (d0, d1) = struct.unpack('<BB', buffer(d))
    
    OPCONFIG = (d1 << 8) | d0
    
    #print_str = "OPCONFIG REGISTER: %d " %(OPCONFIG)
    #print(print_str)
    
    return OPCONFIG

def setGPOUTPolarity(pi, POLARITY):
    
    new_opconfig = read_opconfig_register(pi)
    
    print("BEFORE GPOUT_POLARITY:", new_opconfig)
    
    bit_11 = new_opconfig & 0x80
    
    if (POLARITY):
        if (bit_11 & (1<<11) ):
            return True
            
        new_opconfig = new_opconfig | (1 << 11)
    else:
        if ( ~(bit_11 & (1<<11) ) ):
            return True
            
        new_opconfig = new_opconfig &  ~((1<< 11) )
    
    op_config_MSB = new_opconfig >> 8
    op_config_LSB = new_opconfig & 0x00FF
    op_config_data = [ op_config_MSB, op_config_LSB ] 
    
    #OpConfig register location: BQ27441_ID_REGISTERS id, offset 0
    baby_sitter_python_write_example.write_extended_data(pi,64,0,op_config_data,2)
    

def setGPOUTFunction(pi, GPOUT_FUNCTION):
    
    new_opconfig = read_opconfig_register(pi)
    
    print("BEFORE GPOUT_FUNCTION:", new_opconfig)
    
    bit_2 = new_opconfig & 0x04
    
    if (GPOUT_FUNCTION):
        
        if (bit_2 & (1<<2) ):
            return True
            
        new_opconfig = new_opconfig | (1 << 2)
    else:
    
        if (~ (bit_2 & (1<<2) ) ):
            return True
            
        new_opconfig = new_opconfig &  ~( (1<< 2) )
    
    print("GPOUT_Function BATLOWEN: ", new_opconfig)
    op_config_MSB = new_opconfig >> 8
    op_config_LSB = new_opconfig & 0x00FF
    op_config_data = [ op_config_MSB, op_config_LSB ] 
    
    #OpConfig register location: BQ27441_ID_REGISTERS id, offset 0
    baby_sitter_python_write_example.write_extended_data(pi,64,0,op_config_data,2)
    
def setSOC1Thresholds(pi, SET , CLR):
    #BQ27441_ID_DISCHARGE 49  // Discharge
    
    #constrain SET between 0 and 100
    if (SET > 100):
        SET = 100
    
    if (SET < 0):
        SET = 0
    
    #constrain CLR between 0 and 100
    if (CLR > 100):
        CLR = 100
    
    if (CLR < 0):
        CLR = 0
        
    baby_sitter_python_write_example.write_extended_data(pi, 49, 0, [SET,CLR], 2)
    
def setSOCFThresholds(pi, SET , CLR):
    #BQ27441_ID_DISCHARGE 49  // Discharge
    
    #constrain SET between 0 and 100
    if (SET > 100):
        SET = 100
    
    if (SET < 0):
        SET = 0
    
    #constrain CLR between 0 and 100
    if (CLR > 100):
        CLR = 100
    
    if (CLR < 0):
        CLR = 0
        
    baby_sitter_python_write_example.write_extended_data(pi, 49, 2, [SET,CLR], 2)

def read_GPOUTPolarity(pi):
    #BQ27441_OPCONFIG_GPIOPOL  (1<<11)
    #Get GPOUT polarity setting (active-high or active-low)
    return ( read_opconfig_register(pi) & (1 <<11 ) ) 

def read_GPOUTFunction(pi):
    #BQ27441_OPCONFIG_BATLOWEN (1<<2)
    #Get GPOUT function (BAT_LOW or SOC_INT)
    return ( read_opconfig_register(pi) & ( 1 << 2 ) )
    
def read_SOC1SetThreshold(pi):
    #Get SOC1_Set Threshold - threshold to set the alert flag
    #BQ27441_ID_DISCHARGE    49  // Discharge
    data = baby_sitter_python_write_example.read_extended_data(pi, 49, 0)
    return data

def read_SOC1ClearThreshold(pi):
    #Get SOC1_Clear Threshold - threshold to clear the alert flag
    #BQ27441_ID_DISCHARGE    49  // Discharge
    data = baby_sitter_python_write_example.read_extended_data(pi, 49, 1)
    return data
    
def read_SOCFSetThreshold(pi):
    #Get SOCF_Set Threshold - threshold to set the alert flag
    #BQ27441_ID_DISCHARGE    49  // Discharge
    data = baby_sitter_python_write_example.read_extended_data(pi, 49, 2)
    return data

def read_SOCFClearThreshold(pi):
    #Get SOCF_Clear Threshold - threshold to clear the alert flag
    #BQ27441_ID_DISCHARGE    49  // Discharge
    data = baby_sitter_python_write_example.read_extended_data(pi, 49, 3)
    return data
    
if __name__ == '__main__':
    try:
        os.system("sudo pigpiod")
    except:
        print("daemon already running")
        
    pi_init = pigpio.pi()             # exit script if no connection
    if not pi_init.connected:
       exit()
        
    setup(pi_init)
    
    pi_init.stop()