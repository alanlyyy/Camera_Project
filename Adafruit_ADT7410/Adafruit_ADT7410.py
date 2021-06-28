import pigpio
import time


ADT7410_I2CADDR_DEFAULT = 0x48        #I2C address (by default)
ADT7410_REG__ADT7410_TEMPMSB = 0x00    #Temp. value MSB
ADT7410_REG__ADT7410_TEMPLSB = 0x01    #Temp. value LSB
ADT7410_REG__ADT7410_STATUS = 0x02     #Status register
ADT7410_REG__ADT7410_CONFIG = 0x03     #Configuration register
ADT7410_REG__ADT7410_ID = 0x0B         #Manufacturer identification
ADT7410_REG__ADT7410_SWRST = 0x2F     #Temperature hysteresis

#set temperature thresholds for triggering interrupt
HIGH_TEMP = 30
LOW_TEMP = -10
CRITICAL_TEMP = 50
HYST_TEMP = 5               #between 0 to 15 degrees C

#CONFINGURATION REGISTER
#FaultQueue
BIT0 = 0x00
BIT1 = 0x00
#CT Polarity
BIT2 = 0x00
#INT Polarity
BIT3 = 0x08
#INTERUPT (0) OR COMPARATOR MODE (1)
BIT4 = 0x10
#TEMP OPERATION MODE
BIT5 = 0x00
BIT6 = 0x00
#BIT RESOLUTION - 13 BIT (0) / 16 BIT (1)
BIT7 = 0x80
BIT_MODE = BIT0 + BIT1 + BIT2 +BIT3 + BIT4 + BIT5 + BIT6 + BIT7

class ADT7410:
    
    def __init__(self, pi):
        self.pi = pi
        
    def read_temp(self):
        """Read temperature from Temp value registers."""
        
        handle = self.pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
        d0 = self.pi.i2c_read_byte_data(handle, 0x01)   #read LSB
        d1 = self.pi.i2c_read_byte_data(handle, 0x00)   #read MSB
        self.pi.i2c_close(handle)                       #close i2c
        
        temp = int( d1 << 8 | d0 )
        
        sign_bit = temp & 0x8000
        
        if (sign_bit == 1):
            temp = (temp - 65536) / 128
        else:
            temp  /=128
        
        temp_c = temp 
        temp_f = temp_c * (9/5) + 32
        
        print_str = "Temp C* : %d , Temp F*: %d" %(temp_c, temp_f)
        print(print_str)
        
    def set_configuration_register(self,BIT_MODE):
        """ 
        CT self.pin used for critical temp interrupt
        INT self.pin used for below temp low or above temp high interrupt trigger.
        
        reading to any register resets CT/INT self.pin.
        
        """
        #enable 16 bit
        #resolution = 0x80
        
        #enable interrupt mode
        #INT = 0x00              #comparator mode = 0x10
        
        #set interrupt polarity to active high
        #INT_Polarity = 0x08
        
        #resolution + INT + INT_Polarity 
        
        handle = self.pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
        self.pi.i2c_write_byte_data( handle, 0x03, BIT_MODE )
        self.pi.i2c_close(handle)                       

    def set_temp_high(self, temp):
        """Set temp high register interrupt limit."""
        digitize_temp = temp
        
        if (digitize_temp > 0):
            digitize_temp = 128 * digitize_temp
        else:
            digitize_temp = (128 * digitize_temp) + 65536
            
        tempMSB = digitize_temp >> 8
        tempLSB = digitize_temp & 0x00FF
        
        handle = self.pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
        self.pi.i2c_write_byte_data( handle, 0x05, tempLSB)
        self.pi.i2c_write_byte_data( handle, 0x04, tempMSB)
        self.pi.i2c_close(handle)      

    def set_temp_critical(self, temp):
        """Set temp critical register interrupt limit."""
        digitize_temp = temp
        
        if (digitize_temp > 0):
            digitize_temp = 128 * digitize_temp
        else:
            digitize_temp = (128 * digitize_temp) + 65536
            
        tempMSB = digitize_temp >> 8
        tempLSB = digitize_temp & 0x00FF
        
        handle = self.pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
        self.pi.i2c_write_byte_data( handle, 0x09, tempLSB)
        self.pi.i2c_write_byte_data( handle, 0x08, tempMSB)
        self.pi.i2c_close(handle)      

    def set_temp_low(self, temp):
        """Set temp low register interrupt limit."""
        digitize_temp = temp
        
        if (digitize_temp > 0):
            digitize_temp = 128 * digitize_temp
        else:
            digitize_temp = (128 * digitize_temp) + 65536
            
        tempMSB = digitize_temp >> 8
        tempLSB = digitize_temp & 0x00FF
        
        handle = self.pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
        self.pi.i2c_write_byte_data( handle, 0x07, tempLSB)
        self.pi.i2c_write_byte_data( handle, 0x06, tempMSB)
        self.pi.i2c_close(handle)

    def set_temp_hyst(self, temp):
        """Set temp hysterisis register interrupt limit."""
        digitize_temp = temp
        
        #bound temp to be between 0 - 15 degrees C
        if (temp > 15):
            digitize_temp = 15
        
        if (temp < 0):
            digitize_temp = 0
        
        handle = self.pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
        self.pi.i2c_write_byte_data( handle, 0x0A, digitize_temp)
        self.pi.i2c_close(handle)    

    def read_temp_high(self):
        """Reads the Temp High Setpoint."""
        
        handle = self.pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
        d1 = self.pi.i2c_read_byte_data( handle, 0x04)
        d0 = self.pi.i2c_read_byte_data( handle, 0x05)
        self.pi.i2c_close(handle)

        temp = int( d1 << 8 | d0 )          #create a 16 bit integer
        
        sign_bit = temp & 0x8000            #if the MSB is 1, then we have a negative number.
        
        if (sign_bit):
            temp = (temp - 65536) / 128
        else:
            temp  /=128
        
        temp_c = temp 
        temp_f = temp_c * (9/5) + 32
        
        print_str = "HIGH Temp C* : %d , Temp F*: %d" %(temp_c, temp_f)
        print(print_str)
        
    def read_temp_critical(self):
        """Reads the Temp High Setpoint."""
        
        handle = self.pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
        d1 = self.pi.i2c_read_byte_data( handle, 0x08)
        d0 = self.pi.i2c_read_byte_data( handle, 0x09)
        self.pi.i2c_close(handle)

        temp = int( d1 << 8 | d0 )
        
        sign_bit = temp & 0x8000            #if the MSB is 1, then we have a negative number.
        
        if (sign_bit):
            temp = (temp - 65536) / 128
        else:
            temp  /=128
        
        temp_c = temp 
        temp_f = temp_c * (9/5) + 32
        
        print_str = "Critical Temp C* : %d , Temp F*: %d" %(temp_c, temp_f)
        print(print_str)

    def read_temp_low(self):
        """Reads the Temp Low Setpoint."""
        
        handle = self.pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
        d1 = self.pi.i2c_read_byte_data( handle, 0x06)
        d0 = self.pi.i2c_read_byte_data( handle, 0x07)
        self.pi.i2c_close(handle)

        temp = int( d1 << 8 | d0 )
        
        sign_bit = temp & 0x8000            #if the MSB is 1, then we have a negative number.
        
        if (sign_bit):
            temp = (temp - 65536) / 128
        else:
            temp  /=128
        
        temp_c = temp 
        temp_f = temp_c * (9/5) + 32
        
        print_str = "Low Temp C* : %d , Temp F*: %d" %(temp_c, temp_f)
        print(print_str)
        
    def read_temp_hyst(self):
        """Reads the Temp Low Setpoint."""
        
        handle = self.pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
        temp = self.pi.i2c_read_byte_data( handle, 0x0A)
        self.pi.i2c_close(handle)
        
        temp_c = temp 
        temp_f = temp_c * (9/5) + 32
        
        print_str = "HYST Temp C* : %d , Temp F*: %d" %(temp_c, temp_f)
        print(print_str)

    def read_configuration_register(self):
        """Read 8 bit configuration register.
        
        BIT 0:1 - Fault Queue, set number of undertemp + overtemp faults that occur before setting int/ct self.pin.
        BIT 2: - CT self.pin Polarity (0 low / 1 high)
        BIT 3: - INT self.pin Polarity (0 low / 1 high)
        BIT 4: - SELECT Interrrupt/Comparator Mode (0 INT/ 1 Comp)
        BIT 5:6: - temp operation mode
        BIT 7: - 13 it resolution (0) / 16 bit resolution (1)
        """ 
        handle = self.pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
        config = self.pi.i2c_read_byte_data( handle, 0x03)
        self.pi.i2c_close(handle)
        
        print(config)

    def read_status_register(self):
        """Read 6 bit status register.
        
        STATUS
        BIT 4 - Temp low interrupt flag (Active high)
        BIT 5 - Temp high interrupt flag (Active High)
        BIT 6 - Temp critical interrupt flag (Active high)
        BIT 7 - RDY goes low when temp written to temp value register / goes high when temp is read from temp value register.
        """
        
        handle = self.pi.i2c_open( 1, ADT7410_I2CADDR_DEFAULT )
        status = self.pi.i2c_read_byte_data( handle, 0x02)
        self.pi.i2c_close(handle)
        
        print(status)

if __name__ == '__main__':

    try:
        os.system("sudo self.pigself.piod")
    except:
        print("daemon already running")
        
    pi = pigpio.pi()             # exit script if no connection
    if not pi.connected:
       exit()

    GPOUT_PIN = 4
    PB = 17
    
    pi.set_mode(GPOUT_PIN, pigpio.INPUT)
    pi.set_mode(PB, pigpio.INPUT)
    pi.set_pull_up_down(PB, pigpio.PUD_UP)                      #set pull up resistor
    
    sensor = ADT7410(pi)
    
    sensor.read_configuration_register()
    time.sleep(1)
    sensor.set_configuration_register(BIT_MODE)
    time.sleep(1)
    sensor.read_configuration_register()
    time.sleep(1)
    
    sensor.read_temp_high()
    time.sleep(1)
    sensor.set_temp_high(HIGH_TEMP)
    time.sleep(1)
    sensor.read_temp_high()
    
    sensor.read_temp_low()
    time.sleep(1)
    sensor.set_temp_low(LOW_TEMP)
    time.sleep(1)
    sensor.read_temp_low()
    
    sensor.read_temp_critical()
    time.sleep(1)
    sensor.set_temp_critical(CRITICAL_TEMP)
    time.sleep(1)
    sensor.read_temp_critical()
    
    sensor.read_temp_hyst()
    time.sleep(1)
    sensor.set_temp_hyst(HYST_TEMP)
    time.sleep(1)
    sensor.read_temp_hyst()
    
    while(1):
        
        if (pi.read(PB) == 0):
            break
        
        if(pi.read(GPOUT_PIN) == 1):
            print("Interrupt Triggered")
            sensor.read_status_register()
        
        sensor.read_temp()
            
        time.sleep(1)
        