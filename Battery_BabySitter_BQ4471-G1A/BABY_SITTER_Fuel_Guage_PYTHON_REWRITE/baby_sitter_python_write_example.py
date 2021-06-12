"""
Write Design Capacity from 1200mAh to 2000mAh

Resource:
https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/658708/bq27441-g1-problem-trying-to-set-the-design-capacity
"""

import pigpio
import struct
import sys
import time
import baby_sitter_python_example

GPOUT_PIN = 4

BQ72441_I2C_TIMEOUT = 2000
CAPACITY = 2000

if sys.version > '3':
   buffer = memoryview
   
def setup(pi):
    pi.set_mode(4, pigpio.INPUT)
    
def get_device_type(pi):
    
    #One byte write to control command register
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte_data(handle,0x00, 0x00) #LSB
    pi.i2c_write_byte_data(handle,0x01, 0x01) #MSB
    pi.i2c_close(handle)
    
    #Quick read
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
  
    #the number of bytes d has to equal format string. (here requesting 2 unsigned char 1 byte each for d0 and d1)
    (d0, d1) = struct.unpack('<BB', buffer(d))
    
    pi.i2c_close(handle)              #close i2c
    
    print_str = "DEVICE ID: %d" %( (int(d1) << 8) | d0 )
    print( print_str )

def unseal(pi):
    #unseal should return 14
    #writing a 0x00 control command requires a subsequence 0xNNNN 2 byte sub command.
    
    #One byte write method to control command register
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte_data(handle,0x00, 0x00)    #LSB
    pi.i2c_write_byte_data(handle,0x01, 0x80)    #MSB
    pi.i2c_write_byte_data(handle,0x00, 0x00)    #LSB
    pi.i2c_write_byte_data(handle,0x01, 0x80)    #MSB
    pi.i2c_close(handle)
    

def check_if_sealed(pi):
    #report status of device use 0x0000 (CONTROL STATUS REGISTER)
    
    #2 byte incremental write
    handle = pi.i2c_open(1,0x55)
    pi.i2c_write_byte_data(handle,0x00,0x00)     #control command LSB
    pi.i2c_write_byte_data(handle,0x01,0x00)     #MSB
    pi.i2c_close(handle)
    
    
    #quick read
    handle = pi.i2c_open(1,0x55)
    (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
    pi.i2c_close(handle)
    
    
    #the number of bytes d has to equal format string. (here requesting 2 unsigned char 1 byte each for d0 and d1)
    (d0, d1) = struct.unpack('<BB', buffer(d))
    
    status = (d1 << 8) | d0
    
    print_str = "STATUS BIT: %d " %( status & (1 << 13) )
    
    print(print_str)
    
    
    return ( status & (1 << 13) )
    
    
def enter_fuel_guage_config(pi):
    #enter configuartion mode BQ27441_CONTROL_SET_CFGUPDATE  0x13
    
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte_data(handle, 0x00, 0x13)   #LSB
    pi.i2c_write_byte_data(handle, 0x01, 0x00 )  #MSB
    pi.i2c_close(handle)


    

def check_fuel_guage_config(pi):
    #check configuartion mode BQ27441_COMMAND_FLAGS      0x06 // Flags()
    
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte(handle, 0x06) 
    pi.i2c_close(handle)
    
    #quick read Flags() register
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
    (d0, d1) = struct.unpack('<BB', buffer(d))
    pi.i2c_close(handle)              
    
    flags = d1 << 8 | d0
    
    timeout = BQ72441_I2C_TIMEOUT
    
    #BQ27441_FLAG_CFGUPMODE  (1<<4)
    while ( (timeout > 0) and (  ~ (flags & (1 << 4) ) ) ): 
        timeout -= 1
        time.sleep(0.001)
    
    print_str = "Check Fuel guage config FLAGS: %d" %flags
    print(print_str)
    
    if (timeout >0):
        return True
        

def enterConfig(pi):
    
    if( ~ check_if_sealed(pi)):
        unseal(pi)
   
    enter_fuel_guage_config(pi)
 
    
def exitConfig(pi):
    """
    FLAGS 392 when exit
    Exit config = 0 when exit
    """

    #Implement soft reset BQ27441_CONTROL_SOFT_RESET 0x42
    handle = pi.i2c_open(1,0x55)
    pi.i2c_write_byte_data(handle,0x00,0x42)          #LSB
    pi.i2c_write_byte_data(handle,0x01, 0x00)         #MSB    
    pi.i2c_close(handle)
    
    #quick read Flags register
    handle = pi.i2c_open(1, 0x55)
    pi.i2c_write_byte(handle,0x06)         #//BQ27441_COMMAND_FLAGS      0x06 , Flags()
    pi.i2c_close(handle)
    
    #quick read
    handle = pi.i2c_open(1,0x55)
    (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 32 bytes from fuel guage
    (d0, d1) = struct.unpack('<BB', buffer(d))
    pi.i2c_close(handle)              #close i2c
    
    timeout = BQ72441_I2C_TIMEOUT
    flags = d1 << 8 | d0    #if flags == 0, config mode is turned off

    while ((timeout > 0) and ((flags & (1 << 4) ))):  #BQ27441_FLAG_CFGUPMODE 1<<4
        timeout -= 1
        time.sleep(0.001)
        
    print_str = "Exit Config FLAGS: %d"  %(int(flags))
    print(print_str, "Config_update mode 0 off", (flags & (1 << 4)) )
    print("Timeout: ", " ", timeout)
    
    if (timeout > 0):
    
        #Seal Device, write 0x0020 to control register
        handle = pi.i2c_open(1,0x55)
        pi.i2c_write_byte_data(handle,0x00,0x20)           #LSB
        pi.i2c_write_byte_data(handle,0x01, 0x00)          #MSB
        pi.i2c_close(handle)
        
        #i2c quick read
        handle = pi.i2c_open(1,0x55)
        (b, d) = pi.i2c_read_device(handle, 2)        
        pi.i2c_close(handle)              #close i2c
        (d0, d1) = struct.unpack('<BB', buffer(d))
        
        print_str  ="Exit Config Control Status register BIT 13  %d"  %int(d1 << 8 | d0) 
        print(print_str)
            
        return True 
    
def read_flags(pi):
    """Quick read flags register"""
    
    handle = pi.i2c_open(1, 0x55)
    pi.i2c_write_byte(handle,0x06)         #//BQ27441_COMMAND_FLAGS      0x06 , Flags()
    pi.i2c_close(handle)
    
    #quick read flags register
    handle = pi.i2c_open(1,0x55)
    (b, d) = pi.i2c_read_device(handle, 2)        #buffer read 32 bytes from fuel guage
    (d0, d1) = struct.unpack('<BB', buffer(d))
    pi.i2c_close(handle)              #close i2c
    
    time.sleep(0.00066)
    
    timeout = BQ72441_I2C_TIMEOUT
    flags = d1 << 8 | d0    #if flags == 0, config mode is turned off
    
    print("Flags: ", flags)

def read_control_status_register(pi):
    """Quick Read control status register."""

    #read control status register
    handle = pi.i2c_open(1,0x55)
    pi.i2c_write_byte_data(handle,0x00,0x00)
    pi.i2c_write_byte_data(handle, 0x01, 0x00)
    pi.i2c_close(handle)
    
    handle = pi.i2c_open(1,0x55)
    (b, d) = pi.i2c_read_device(handle, 2)        
    (d0, d1) = struct.unpack('<BB', buffer(d))
    pi.i2c_close(handle)              #close i2c
    
    
    print_str  ="Exit Config Control Status register:  %d"  %int(d1 << 8 | d0) 
    print(print_str)
    
    return ((d1 << 8 | d0)  & (1 << 13) )

def block_data_control(pi):
    """write block data control to register 0x61."""
    
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte_data(handle,0x61,0x00)    #//BQ27441_EXTENDED_CONTROL
    pi.i2c_close(handle)
    
def block_data_class(pi,CLASSID):
    """write block data class to register 0x3E"""
    
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte_data(handle,0x3E,CLASSID) #CLASSID = 82
    pi.i2c_close(handle)
    

def block_data_offset(pi,offset):
    """write block data offset to register 0x3F"""
    
    offset = int(offset) & 0xFF
    
    handle = pi.i2c_open(1, 0x55)     #open i2c at 0x55
    pi.i2c_write_byte_data(handle,0x3F,offset)    #BQ27441_EXTENDED_DATABLOCK 0x3F,offset is usually 0, 10/32
    pi.i2c_close(handle)
    
def calculate_checksum(pi):
    
    handle = pi.i2c_open(1,0x55)
    
    (b, d) = pi.i2c_read_i2c_block_data(handle,0x40, 32)        #buffer read 32 bytes starting at register 0x40
  
    data = struct.unpack('<32B', buffer(d))                     #break down 32 bytes string into 32 individual bytes in a tuple
    
    pi.i2c_close(handle)            
    
    old_check_sum =0
    
    for i in range(0,32):
        old_check_sum += data[i]
    
    #convert checksum to 1 byte
    old_check_sum = (255 - old_check_sum) & 0xFF
    
    print(old_check_sum)
    
    return old_check_sum
    
def block_data_checksum(pi):
    """
    read checksum from register 0x60
    #BQ27441_EXTENDED_CHECKSUM  0x60
    """
    handle = pi.i2c_open(1, 0x55)       
    pi.i2c_write_byte(handle, 0x60)             
    pi.i2c_close(handle)
    
    #quick read one byte
    handle = pi.i2c_open(1, 0x55)     
    (b, d) = pi.i2c_read_device(handle, 1)
    recalculate_check_sum = struct.unpack('<B', buffer(d))
    pi.i2c_close(handle)              #close i2c
    
    print_str = "Blockdata checksum:  %d" %(recalculate_check_sum)
    print(print_str)
    return recalculate_check_sum

def read_design_capacity(pi):
    #quick read current design capacity from register 0x3C
    
    handle = pi.i2c_open(1,0x55)
    pi.i2c_write_byte(handle, 0x3C)
    pi.i2c_close(handle)
    
    handle = pi.i2c_open(1,0x55)
    (b1, data1) = pi.i2c_read_device(handle,2)
    data = struct.unpack('<BB', buffer(data1))
    pi.i2c_close(handle)              #close i2c
    
    print_str = "Capacity Remaining: %d" %(int(data[1] << 8 | data[0]) )
    print(print_str)
    
def write_block_data(pi, offset, data):
    """write configuration data to register 0x40.
    #BQ27441_EXTENDED_BLOCKDAT = 0x40;
    """
    address = offset + 0x40         
    
    handle = pi.i2c_open(1, 0x55)       
    pi.i2c_write_byte_data(handle,address,data)             
    pi.i2c_close(handle)
    
def write_check_sum(pi, new_check_sum):
    """Write new checksum to register 0x60 #BQ27441_EXTENDED_CHECKSUM
    
    """

    handle = pi.i2c_open(1, 0x55)
    
    print("Current Checksum: ", new_check_sum)
    
    pi.i2c_write_byte_data(handle,0x60,new_check_sum)             #BQ27441_EXTENDED_CHECKSUM
    
    
    pi.i2c_close(handle)

def write_extended_data(pi, classID, offset, data, len):
    
    if (len >32):
        return False
    
    enterConfig(pi)
    
    block_data_control(pi)                      #cannot access if device is sealsed
    
    block_data_class(pi,classID)                #cannot access if device is sealed
    
    block_data_offset(pi,offset/32)
    
    old_cs = calculate_checksum(pi)
    
    old_check_sum = block_data_checksum(pi)
    
    for i in range(0,len):
        
        write_block_data( pi, (offset % 32) + i, data[i] )
        
    new_check_sum = calculate_checksum(pi)
    
    write_check_sum(pi,new_check_sum)
    
    exitConfig(pi) 
    
    print("Old CheckSum", old_cs)
    print ("New CheckSum", new_check_sum)
    
def set_capacity(pi, capacity):
    
    #Unit: mAh
    capMSB = capacity >> 8
    capLSB = capacity & 0x00FF
    capacityData = [capMSB, capLSB]
    write_extended_data(pi ,82 ,10 ,capacityData , 2)
    
if __name__ == '__main__':

    try:
        os.system("sudo pigpiod")
    except:
        print("daemon already running")
        
    pi_init = pigpio.pi()             # exit script if no connection
    if not pi_init.connected:
       exit()
    
    #Status checks
    read_flags(pi_init)
    read_control_status_register(pi_init)
    read_design_capacity(pi_init)
    
    set_capacity(pi_init,CAPACITY)
    
    baby_sitter_python_example.test_read(pi_init)
    
    #check status after exiting configuration
    read_flags(pi_init)