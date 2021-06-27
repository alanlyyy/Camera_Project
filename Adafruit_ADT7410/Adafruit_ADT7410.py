
import pigpio
import time

ADT7410_I2CADDR_DEFAULT = 0x48        #I2C address (by default)
ADT7410_REG__ADT7410_TEMPMSB = 0x00    #Temp. value MSB
ADT7410_REG__ADT7410_TEMPLSB = 0x01    #Temp. value LSB
ADT7410_REG__ADT7410_STATUS = 0x02     #Status register
ADT7410_REG__ADT7410_CONFIG = 0x03     #Configuration register
ADT7410_REG__ADT7410_ID = 0x0B         #Manufacturer identification
ADT7410_REG__ADT7410_SWRST = 0x2F     #Temperature hysteresis

try:
    os.system("sudo pigpiod")
except:
    print("daemon already running")
    
pi = pigpio.pi()             # exit script if no connection
if not pi.connected:
   exit()
   

def read_temp(pi):
    """Read temperature from Temp value registers."""
    
    handle = pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
    d0 = pi.i2c_read_byte_data(handle, 0x01)   #read LSB
    d1 = pi.i2c_read_byte_data(handle, 0x00)   #read MSB
    pi.i2c_close(handle)                       #close i2c
    
    temp = int( d1 << 8 | d0 )
    
    sign_bit = temp & 0x8000
    
    if (sign_bit == 1):
        temp = (temp - 32768) / 128
    else:
        temp  /=128
    
    temp_c = temp 
    temp_f = temp_c * (9/5) + 32
    
    print_str = "Temp C* : %d , Temp F*: %d" %(temp_c, temp_f)
    print(print_str)
    
def set_configuration_register(pi):
    
    #enable 16 bit
    resolution = 0x80
    
    #enable comparator mode
    CT = 0x10
    
    #set comparator polarity to active high
    CT_Polarity = 0x04
    
    handle = pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
    pi.i2c_write_byte_data( handle, 0x03, resolution + CT + CT_Polarity )
    pi.i2c_close(handle)                       

def set_temp_high(pi, temp):
    """Set temp high interrupt limit."""
    digitize_temp = temp
    
    if (digitize_temp > 0):
        digitize_temp = 128 * digitize_temp
    else:
        digitize_temp = (128 * digitize_temp) + 65536
        
    tempMSB = digitize_temp >> 8
    tempLSB = digitize_temp & 0x00FF
    
    handle = pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
    pi.i2c_write_byte_data( handle, 0x05, tempLSB)
    pi.i2c_write_byte_data( handle, 0x04, tempMSB)
    pi.i2c_close(handle)      

def set_temp_critical(pi, temp):
    """Set temp high interrupt limit."""
    digitize_temp = temp
    
    if (digitize_temp > 0):
        digitize_temp = 128 * digitize_temp
    else:
        digitize_temp = (128 * digitize_temp) + 65536
        
    tempMSB = digitize_temp >> 8
    tempLSB = digitize_temp & 0x00FF
    
    handle = pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
    pi.i2c_write_byte_data( handle, 0x09, tempLSB)
    pi.i2c_write_byte_data( handle, 0x08, tempMSB)
    pi.i2c_close(handle)      

def set_temp_low(pi, temp):
    """Set temp high interrupt limit."""
    digitize_temp = temp
    
    if (digitize_temp > 0):
        digitize_temp = 128 * digitize_temp
    else:
        digitize_temp = (128 * digitize_temp) + 65536
        
    tempMSB = digitize_temp >> 8
    tempLSB = digitize_temp & 0x00FF
    
    handle = pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
    pi.i2c_write_byte_data( handle, 0x07, tempLSB)
    pi.i2c_write_byte_data( handle, 0x06, tempMSB)
    pi.i2c_close(handle)    

def read_temp_high(pi):
    """Reads the Temp High Setpoint."""
    
    handle = pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
    d1 = pi.i2c_read_byte_data( handle, 0x04)
    d0 = pi.i2c_read_byte_data( handle, 0x05)
    pi.i2c_close(handle)

    temp = int( d1 << 8 | d0 )
    
    sign_bit = temp & 0x8000            #if the MSB is 1, then we have a negative number.
    
    if (sign_bit):
        temp = (temp - 65536) / 128
    else:
        temp  /=128
    
    temp_c = temp 
    temp_f = temp_c * (9/5) + 32
    
    print_str = "HIGH Temp C* : %d , Temp F*: %d" %(temp_c, temp_f)
    print(print_str)
    
def read_temp_critical(pi):
    """Reads the Temp High Setpoint."""
    
    handle = pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
    d1 = pi.i2c_read_byte_data( handle, 0x08)
    d0 = pi.i2c_read_byte_data( handle, 0x09)
    pi.i2c_close(handle)

    temp = int( d1 << 8 | d0 )
    
    sign_bit = temp & 0x8000
    
    if (sign_bit):
        temp = (temp - 65536) / 128
    else:
        temp  /=128
    
    temp_c = temp 
    temp_f = temp_c * (9/5) + 32
    
    print_str = "Critical Temp C* : %d , Temp F*: %d" %(temp_c, temp_f)
    print(print_str)

def read_temp_low(pi):
    """Reads the Temp Low Setpoint."""
    
    handle = pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
    d1 = pi.i2c_read_byte_data( handle, 0x06)
    d0 = pi.i2c_read_byte_data( handle, 0x07)
    pi.i2c_close(handle)

    temp = int( d1 << 8 | d0 )
    
    sign_bit = temp & 0x8000
    
    if (sign_bit):
        temp = (temp - 65536) / 128
    else:
        temp  /=128
    
    temp_c = temp 
    temp_f = temp_c * (9/5) + 32
    
    print_str = "Low Temp C* : %d , Temp F*: %d" %(temp_c, temp_f)
    print(print_str)

def read_configuration_register(pi):

    handle = pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
    config = pi.i2c_read_byte_data( handle, 0x03)
    pi.i2c_close(handle)
    
    print(config)

def read_status_register(pi):

    handle = pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
    status = pi.i2c_read_byte_data( handle, 0x02)
    pi.i2c_close(handle)
    
    print(status)

if __name__ == '__main__':
    read_configuration_register(pi)
    time.sleep(1)
    set_configuration_register(pi)
    time.sleep(1)
    read_configuration_register(pi)
    time.sleep(1)
    
    read_temp_high(pi)
    time.sleep(1)
    set_temp_high(pi,50)
    time.sleep(1)
    read_temp_high(pi)
    
    read_temp_low(pi)
    time.sleep(1)
    set_temp_low(pi,-5)
    time.sleep(1)
    read_temp_low(pi)
    
    read_temp_critical(pi)
    time.sleep(1)
    set_temp_critical(pi,75)
    time.sleep(1)
    read_temp_critical(pi)
    
    
    #while(1):
    read_temp(pi)
    time.sleep(1)