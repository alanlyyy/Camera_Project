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
  
  #Wire.beginTransmission(0x55);  #device address is 0x55
  handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
  
  pi.i2c_write_byte(handle, 0x04)   #write subaddress
  
  pi.i2c_close(handle)

  handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
  
  (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
  
  #the number of bytes d has to equal format string. (here requesting 2 unsigned char 1 byte each for d0 and d1)
  (d0, d1) = struct.unpack('<BB', buffer(d))    
  
  pi.i2c_close(handle)              #close i2c
    
  print(b)
  print(d)
  
  data = [d0,d1]
  
  #convert data[1] from uint8_t to uint16_t shift bits left by 8 bits, and OR with data[0] uint8_t
  #print( (data[1] << 8) | data[0]) )
    
  #return (data[1] << 8) | data[0])
  
  print(data[0])
  print(data[1])
  print(data[1] << 8)
  
  print_str = "Voltage: %d" %(int(data[1] << 8 | data[0]) )
  print( print_str )

def get_device_type(pi):

    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte(handle, 0x00)   #write subaddress
    pi.i2c_write_word_data(handle,0, 0x0001) #write device id command
    pi.i2c_close(handle)
    
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte(handle, 0x00)   #write subaddress
    pi.i2c_close(handle)
    
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
  
    #the number of bytes d has to equal format string. (here requesting 2 unsigned char 1 byte each for d0 and d1)
    (d0, d1) = struct.unpack('<BB', buffer(d))
    
    data = [d0, d1]
    
    pi.i2c_close(handle)              #close i2c
    
    print(data[0])
    print(data[1])
    print(data[1] << 8)
    print_str = "DEVICE ID: %d" %(int(data[1] << 8 | data[0]) )
    print( print_str )

def read_current(pi):

    #Wire.beginTransmission(0x55);  #device address is 0x55
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte(handle, 0x10)
    pi.i2c_close(handle)
    
    
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
  
    #the number of bytes d has to equal format string. (here requesting 2 unsigned char 1 byte each for d0 and d1)
    (d0, d1) = struct.unpack('<BB', buffer(d))
    pi.i2c_close(handle)              #close i2c
    
    data = [d0, d1]
    
    
    print(data[0])
    print(data[1])
    print(data[1] << 8)
    print_str = "Current: %d" %(int(data[1] << 8 | data[0]) )
    print( print_str )
    
def read_capacity(pi):

    #Wire.beginTransmission(0x55);  #device address is 0x55
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte(handle, 0x0C)
    pi.i2c_close(handle)
    
    
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
  
    #the number of bytes d has to equal format string. (here requesting 2 unsigned char 1 byte each for d0 and d1)
    (d0, d1) = struct.unpack('<BB', buffer(d))
    pi.i2c_close(handle)              #close i2c
    
    data = [d0, d1]
    
    
    print(data[0])
    print(data[1])
    print(data[1] << 8)
    
    print_str = "Capacity Remaining: %d" %(int(data[1] << 8 | data[0]) )
    print(print_str)
    
def read_full_capacity(pi):

    #Wire.beginTransmission(0x55);  #device address is 0x55
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte(handle, 0x0E)
    pi.i2c_close(handle)
    
    
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
  
    #the number of bytes d has to equal format string. (here requesting 2 unsigned char 1 byte each for d0 and d1)
    (d0, d1) = struct.unpack('<BB', buffer(d))
    pi.i2c_close(handle)              #close i2c
    
    data = [d0, d1]
    
    
    print(data[0])
    print(data[1])
    print(data[1] << 8)
    
    print_str = "Total Capacity: %d" %(int(data[1] << 8 | data[0]) )
    
    print(print_str)
    
def test_read(pi_init):
    read_voltage(pi_init)
    read_current(pi_init)
    read_capacity(pi_init)
    read_full_capacity(pi_init)
    #get_device_type(pi_init)
    
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
    #get_device_type(pi_init)
    
    
    pi_init.stop()