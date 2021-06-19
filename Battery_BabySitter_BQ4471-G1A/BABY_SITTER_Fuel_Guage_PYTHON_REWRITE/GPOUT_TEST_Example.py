"""Script used to read data from fuel guage ic"""

import pigpio
import struct
import sys
import time
import BQ27441_source

GPOUT_PIN = 4
SET_CAPACITY = 2000

#opconfig register bit 2
BAT_LOW = 1
SOC_INT = 0

SOCI_SET = 15                                      # Interrupt set threshold at 20%
SOCI_CLR = 20                                      # Interrupt clear threshold at 25%
SOCF_SET = 5                                       # Final threshold set at 5%
SOCF_CLR = 10                                      # Final threshold clear at 10%
    
if  __name__ == '__main__':
    try:
        os.system("sudo pigpiod")
    except:
        print("daemon already running")
        
    pi_init = pigpio.pi()             # exit script if no connection
    if not pi_init.connected:
       exit()
       
    bq = BQ27441_source.BQ27441(pi_init, GPOUT_PIN )
    
    bq.set_capacity(SET_CAPACITY)
    
    bq.set_GPOUT(SOCI_SET,SOCI_CLR, SOCF_SET, SOCF_CLR, BAT_LOW, 0)
    
    time.sleep(5)
    
    while (True):
        
        pin_4_read = pi_init.read(GPOUT_PIN)

        print(pin_4_read)
        #read the pin
        
        #If the GPOUT interrupt is active (low)
        if ( pin_4_read == 0 ):
        
            flagState = bq.read_flags() 
            SOC1 = (flagState & 0x04) & ( 1 << 2)         #BQ27441_FLAG_SOC1 (1<<2)
            SOCF = (flagState & 0x02) & ( 1 << 1)         #BQ27441_FLAG_SOCF (1<<1)
            
            print( "GPOUT PIN -  ", "SOC1: ", SOC1, " ", "SOCF: ", SOCF )
        
            if ( SOCF ):
                print( "<!-- WARNING: Battery Dangerously low -->" )
            elif( SOC1 ):
                print( "<!-- WARNING: Battery Low -->")
        
        #delay for 1 second
        time.sleep(5)
        
        bq.test_read()

    pi_init.stop()
    