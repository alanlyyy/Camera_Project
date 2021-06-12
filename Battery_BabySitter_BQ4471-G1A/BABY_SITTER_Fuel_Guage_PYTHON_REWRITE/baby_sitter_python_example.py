"""Script used to read data from fuel guage ic"""

import pigpio
import struct
import sys

GPOUT_PIN = 4

if sys.version > '3':
   buffer = memoryview
   
def setup(pi):
    pi.set_mode(4, pigpio.INPUT)
    
def read_voltage(pi):
  
  #read voltage from register 0x04
  handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
  pi.i2c_write_byte(handle, 0x04)   #write subaddress
  pi.i2c_close(handle)
    
  #Quick read
  handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
  (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
  (d0, d1) = struct.unpack('<BB', buffer(d))    
  
  pi.i2c_close(handle)              #close i2c
  
  print_str = "Voltage: %d" %(int(d1 << 8 | d0) )
  print( print_str )

def get_device_type(pi):

    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte_data(handle,0x00, 0x01)       #write to command register LSB
    pi.i2c_write_byte_data(handle,0x01, 0x00)       #write to command register MSB
    pi.i2c_close(handle)
    
    #quick read device name
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
  
    #the number of bytes d has to equal format string. (here requesting 2 unsigned char 1 byte each for d0 and d1)
    (d0, d1) = struct.unpack('<BB', buffer(d))

    pi.i2c_close(handle)             
    print_str = "DEVICE ID: %d" %(int(d1 << 8 | d0) )
    print( print_str )

def read_current(pi):

    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte(handle, 0x10)
    pi.i2c_close(handle)
    
    
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
    (d0, d1) = struct.unpack('<BB', buffer(d))
    pi.i2c_close(handle)           

    print_str = "Current: %d" %(int(d1 << 8 | d0) )
    print( print_str )
    
def read_capacity(pi):

    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte(handle, 0x0C)
    pi.i2c_close(handle)
    
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
  
    #the number of bytes d has to equal format string. (here requesting 2 unsigned char 1 byte each for d0 and d1)
    (d0, d1) = struct.unpack('<BB', buffer(d))
    pi.i2c_close(handle)              #close i2c
    
    print_str = "Capacity Remaining: %d" %(int(d1 << 8 | d0) )
    print(print_str)
    
def read_full_capacity(pi):

    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte(handle, 0x0E)
    pi.i2c_close(handle)
    
    
    handle = pi.i2c_open(1, 0x55)     
    (b, d) = pi.i2c_read_device(handle, 2)        
    (d0, d1) = struct.unpack('<BB', buffer(d))
    pi.i2c_close(handle)              #close i2c
    
    print_str = "Total Capacity: %d" %(int(d1 << 8 | d0) )
    
    print(print_str)
    
def test_read(pi_init):
    read_voltage(pi_init)
    read_current(pi_init)
    read_capacity(pi_init)
    read_full_capacity(pi_init)
    get_device_type(pi_init)
    
if __name__ == '__main__':
    try:
        os.system("sudo pigpiod")
    except:
        print("daemon already running")
        
    pi_init = pigpio.pi()             # exit script if no connection
    if not pi_init.connected:
       exit()
        
    setup(pi_init)
    read_voltage(pi_init)
    read_current(pi_init)
    read_capacity(pi_init)
    read_full_capacity(pi_init)
    
    pi_init.stop()