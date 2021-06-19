"""Script used to read data from fuel guage ic"""

import pigpio
import struct
import sys
import time

if sys.version > '3':
   buffer = memoryview
   
GPOUT_PIN = 4
SET_CAPACITY = 2000
BQ72441_I2C_TIMEOUT = 2000

#opconfig register bit 2
BAT_LOW = 1
SOC_INT = 0

SOCI_SET = 15                                      # Interrupt set threshold at 20%
SOCI_CLR = 20                                      # Interrupt clear threshold at 25%
SOCF_SET = 5                                       # Final threshold set at 5%
SOCF_CLR = 10                                      # Final threshold clear at 10%

class BQ27441:
    
    def __init__(self,pi,GPOUT):
        
        self.pi = pi
        self.pi.set_mode(GPOUT, pigpio.INPUT)
        self.pi.set_pull_up_down(GPOUT, pigpio.PUD_UP)                      #set pull up resistor
        
    def unseal(self):
        #unseal should return 14
        #writing a 0x00 control command requires a subsequence 0xNNNN 2 byte sub command.
        
        #One byte write method to control command register
        handle = self.pi.i2c_open(1, 0x55)     #open i2c at 0x55
        self.pi.i2c_write_byte_data(handle,0x00, 0x00)    #LSB
        self.pi.i2c_write_byte_data(handle,0x01, 0x80)    #MSB
        self.pi.i2c_write_byte_data(handle,0x00, 0x00)    #LSB
        self.pi.i2c_write_byte_data(handle,0x01, 0x80)    #MSB
        self.pi.i2c_close(handle)

    def check_if_sealed(self):
        #report status of device use 0x0000 (CONTROL STATUS REGISTER)
        
        #2 byte incremental write
        handle = self.pi.i2c_open(1,0x55)
        self.pi.i2c_write_byte_data(handle,0x00,0x00)     #control command LSB
        self.pi.i2c_write_byte_data(handle,0x01,0x00)     #MSB
        self.pi.i2c_close(handle)
        
        #quick read
        handle = self.pi.i2c_open(1,0x55)
        (b, d) = self.pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
        self.pi.i2c_close(handle)
        
        
        #the number of bytes d has to equal format string. (here requesting 2 unsigned char 1 byte each for d0 and d1)
        (d0, d1) = struct.unpack('<BB', buffer(d))
        
        status = (d1 << 8) | d0
        
        print_str = "STATUS BIT: %d " %( status & (1 << 13) )
        
        print(print_str)
        
        
        return ( status & (1 << 13) )
        
    def enter_fuel_guage_config(self):
        #enter configuartion mode BQ27441_CONTROL_SET_CFGUPDATE  0x13
        
        handle = self.pi.i2c_open(1, 0x55)     #open i2c at 0x55
        self.pi.i2c_write_byte_data(handle, 0x00, 0x13)   #LSB
        self.pi.i2c_write_byte_data(handle, 0x01, 0x00 )  #MSB
        self.pi.i2c_close(handle)

    def check_fuel_guage_config(self):
        #check configuartion mode BQ27441_COMMAND_FLAGS      0x06 // Flags()
        
        handle = self.pi.i2c_open(1, 0x55)     #open i2c at 0x55
        self.pi.i2c_write_byte(handle, 0x06) 
        self.pi.i2c_close(handle)
        
        #quick read Flags() register
        handle = self.pi.i2c_open(1, 0x55)     #open i2c at 0x55
        (b, d) = self.pi.i2c_read_device(handle, 2)        #buffer read 2 bytes from fuel guage
        (d0, d1) = struct.unpack('<BB', buffer(d))
        self.pi.i2c_close(handle)              
        
        flags = d1 << 8 | d0
        
        bit_4 = flags & 0x10
        
        timeout = BQ72441_I2C_TIMEOUT
        
        #BQ27441_FLAG_CFGUPMODE  (1<<4)
        while ( (timeout > 0) and (  ~ ( bit_4 & (1 << 4) ) ) ): 
            timeout -= 1
            time.sleep(0.001)
        
        print_str = "Check Fuel guage config FLAGS: %d" %flags
        print(print_str)
        
        if (timeout >0):
            return True
            
    def enterConfig(self):
        
        if( ~ self.check_if_sealed()):
            self.unseal()
       
        self.enter_fuel_guage_config()
     
        
    def exitConfig(self):
        """
        FLAGS 392 when exit
        Exit config = 0 when exit
        """

        #Implement soft reset BQ27441_CONTROL_SOFT_RESET 0x42
        handle = self.pi.i2c_open(1,0x55)
        self.pi.i2c_write_byte_data(handle,0x00,0x42)          #LSB
        self.pi.i2c_write_byte_data(handle,0x01, 0x00)         #MSB    
        self.pi.i2c_close(handle)
        
        #quick read Flags register
        handle = self.pi.i2c_open(1, 0x55)
        self.pi.i2c_write_byte(handle,0x06)         #//BQ27441_COMMAND_FLAGS      0x06 , Flags()
        self.pi.i2c_close(handle)
        
        #quick read
        handle = self.pi.i2c_open(1,0x55)
        (b, d) = self.pi.i2c_read_device(handle, 2)        #buffer read 32 bytes from fuel guage
        (d0, d1) = struct.unpack('<BB', buffer(d))
        self.pi.i2c_close(handle)              #close i2c
        
        timeout = BQ72441_I2C_TIMEOUT
        flags = d1 << 8 | d0    #if flags == 0, config mode is turned off
        
        bit_4 = flags & 0x10
        
        while ((timeout > 0) and ((bit_4 & (1 << 4) ))):  #BQ27441_FLAG_CFGUPMODE 1<<4
            timeout -= 1
            time.sleep(0.001)
            
        print_str = "Exit Config FLAGS: %d"  %(int(flags))
        print(print_str, "Config_update mode 0 off", (flags & (1 << 4)) )
        print("Timeout: ", " ", timeout)
        
        if (timeout > 0):
        
            #Seal Device, write 0x0020 to control register
            handle = self.pi.i2c_open(1,0x55)
            self.pi.i2c_write_byte_data(handle,0x00,0x20)           #LSB
            self.pi.i2c_write_byte_data(handle,0x01, 0x00)          #MSB
            self.pi.i2c_close(handle)
            
            #i2c quick read
            handle = self.pi.i2c_open(1,0x55)
            (b, d) = self.pi.i2c_read_device(handle, 2)        
            self.pi.i2c_close(handle)              #close i2c
            (d0, d1) = struct.unpack('<BB', buffer(d))
            
            print_str  ="Exit Config Control Status register BIT 13  %d"  %int(d1 << 8 | d0) 
            print(print_str)
                
            return True 

    def block_data_control(self):
        """write block data control to register 0x61."""
        
        handle = self.pi.i2c_open(1, 0x55)     #open i2c at 0x55
        self.pi.i2c_write_byte_data(handle,0x61,0x00)    #//BQ27441_EXTENDED_CONTROL
        self.pi.i2c_close(handle)
        
    def block_data_class(self,CLASSID):
        """write block data class to register 0x3E"""
        
        handle = self.pi.i2c_open(1, 0x55)     #open i2c at 0x55
        self.pi.i2c_write_byte_data(handle,0x3E,CLASSID) #CLASSID = 82
        self.pi.i2c_close(handle)
        

    def block_data_offset(self,offset):
        """write block data offset to register 0x3F"""
        
        offset = int(offset) & 0xFF
        
        handle = self.pi.i2c_open(1, 0x55)     #open i2c at 0x55
        self.pi.i2c_write_byte_data(handle,0x3F,offset)    #BQ27441_EXTENDED_DATABLOCK 0x3F,offset is usually 0, 10/32
        self.pi.i2c_close(handle)
        
    def calculate_checksum(self):
        
        handle = self.pi.i2c_open(1,0x55)
        
        (b, d) = self.pi.i2c_read_i2c_block_data(handle,0x40, 32)        #buffer read 32 bytes starting at register 0x40
      
        data = struct.unpack('<32B', buffer(d))                     #break down 32 bytes string into 32 individual bytes in a tuple
        
        self.pi.i2c_close(handle)            
        
        old_check_sum =0
        
        for i in range(0,32):
            old_check_sum += data[i]
        
        #convert checksum to 1 byte LSB
        old_check_sum = (255 - old_check_sum) & 0xFF
        
        return old_check_sum
        
    def block_data_checksum(self):
        """
        read checksum from register 0x60
        #BQ27441_EXTENDED_CHECKSUM  0x60
        """
        handle = self.pi.i2c_open(1, 0x55)       
        self.pi.i2c_write_byte(handle, 0x60)             
        self.pi.i2c_close(handle)
        
        #quick read one byte
        handle = self.pi.i2c_open(1, 0x55)     
        (b, d) = self.pi.i2c_read_device(handle, 1)
        recalculate_check_sum = struct.unpack('<B', buffer(d))
        self.pi.i2c_close(handle)              #close i2c
        
        return recalculate_check_sum
        
    def write_block_data(self, offset, data):
        """write configuration data to register 0x40.
        #BQ27441_EXTENDED_BLOCKDAT = 0x40;
        """
        address = offset + 0x40         
        
        handle = self.pi.i2c_open(1, 0x55)       
        self.pi.i2c_write_byte_data(handle,address,data)             
        self.pi.i2c_close(handle)
        
    def read_block_data(self, offset):
        #Use BlockData() to read a byte from the loaded extended data
        
        address = offset + 0x40                            #BQ27441_EXTENDED_BLOCKDATA  0x40 // BlockData() - constrain to 1 BYTE
        
        handle = self.pi.i2c_open(1, 0x55)
        self.pi.i2c_write_byte(handle, address)
        self.pi.i2c_close(handle)
        
        handle = self.pi.i2c_open(1, 0x55)
        (b, d) =  self.pi.i2c_read_device(handle, 1)                     #read 1 byte of data.    
        data = struct.unpack('<B', buffer(d))
        self.pi.i2c_close(handle)
        
        return data

    def write_check_sum(self, new_check_sum):
        """Write new checksum to register 0x60 #BQ27441_EXTENDED_CHECKSUM
        
        """

        handle = self.pi.i2c_open(1, 0x55)
        
        
        self.pi.i2c_write_byte_data(handle,0x60,new_check_sum)             #BQ27441_EXTENDED_CHECKSUM
        
        
        self.pi.i2c_close(handle)

    def write_extended_data(self, classID, offset, data, len):
        
        if (len >32):
            return False
        
        self.enterConfig()
        
        self.block_data_control()                      #cannot access if device is sealsed
        
        self.block_data_class(classID)                #cannot access if device is sealed
        
        self.block_data_offset(offset/32)
        
        old_cs = self.calculate_checksum()
        
        old_check_sum = self.block_data_checksum()
        
        for i in range(0,len):
            
            self.write_block_data( (offset % 32) + i, data[i] )
            
        new_check_sum = self.calculate_checksum()
        
        print("NEW WRITE CHECKSUM: ", new_check_sum)
        
        print_str = "Blockdata checksum:  %d" %(old_check_sum)
        print(print_str)
        
        self.write_check_sum(new_check_sum)
        
        self.exitConfig() 
        
        
    def read_extended_data(self,classID, offset):
        
        self.enterConfig()
        
        self.block_data_control()                      #cannot access if device is sealsed
        
        self.block_data_class(classID)                #cannot access if device is sealed
        
        self.block_data_offset(offset/32)
        
        old_cs = self.calculate_checksum()
        
        old_check_sum = self.block_data_checksum()
        
        print("READ_EXTENDED_DATA CHECHKSUM: ", old_check_sum)
        
        return_data = self.read_block_data( (offset % 32) )      #Read from offset (limit to 0-31)
        
        self.exitConfig() 
        
        return return_data
        
    def set_capacity(self, capacity):
        
        #Unit: mAh
        capMSB = capacity >> 8
        capLSB = capacity & 0x00FF
        capacityData = [capMSB, capLSB]
        self.write_extended_data(82 ,10 ,capacityData , 2)
        
    def read_design_capacity(self):
        #quick read current design capacity from register 0x3C
        
        handle = self.pi.i2c_open(1,0x55)
        self.pi.i2c_write_byte(handle, 0x3C)
        self.pi.i2c_close(handle)
        
        handle = self.pi.i2c_open(1,0x55)
        (b1, data1) = self.pi.i2c_read_device(handle,2)
        data = struct.unpack('<BB', buffer(data1))
        self.pi.i2c_close(handle)              #close i2c
        
        print_str = "Capacity Remaining: %d" %(int(data[1] << 8 | data[0]) )
        print(print_str)
        
    def read_flags(self):
        """Quick read flags register"""
        #quick read flags register
        handle = self.pi.i2c_open(1,0x55)
        d0 = self.pi.i2c_read_byte_data(handle, 0x06)        #read LSB
        d1 = self.pi.i2c_read_byte_data(handle, 0x07)        #read MSB
        self.pi.i2c_close(handle)              #close i2c
        
        flags = d1 << 8 | d0    #if flags == 0, config mode is turned off
        
        print("Flags: ", flags)
        
        return flags

    def read_control_status_register(self):
        """Quick Read control status register."""

        #read control status register
        handle = self.pi.i2c_open(1,0x55)
        self.pi.i2c_write_byte_data(handle,0x00,0x00)
        self.pi.i2c_write_byte_data(handle, 0x01, 0x00)
        self.pi.i2c_close(handle)
        
        handle = self.pi.i2c_open(1,0x55)
        d0 = self.pi.i2c_read_byte_data(handle, 0x00)        #read LSB
        d1 = self.pi.i2c_read_byte_data(handle, 0x00)        #read MSB
        self.pi.i2c_close(handle)              #close i2c
        
        
        print_str  ="Exit Config Control Status register:  %d"  %int(d1 << 8 | d0) 
        print(print_str)
        
        return ((d1 << 8 | d0)  & (1 << 13) )
    
    #----------------------SET GPOUT INTERRUPT------------------------------------------
    
    def read_opconfig_register(self):
        #BQ27441_EXTENDED_OPCONFIG  0x3A // OpConfig()
        
        #quick read OPCONFIG REGISTER
        handle = self.pi.i2c_open(1,0x55)
        d0 = self.pi.i2c_read_byte_data(handle, 0x3A)        #read LSB
        d1 = self.pi.i2c_read_byte_data(handle, 0x3B)        #read MSB
        self.pi.i2c_close(handle)
        
        OPCONFIG = (d1 << 8) | d0
        
        return OPCONFIG

    def setGPOUTPolarity(self, POLARITY):
        
        new_opconfig = self.read_opconfig_register()
        
        print("BEFORE GPOUT_POLARITY:", new_opconfig)
        
        bit_11 = new_opconfig & 0x80
        
        if (POLARITY):
        
            #if bit 11 is set in the opconfig register and POLARITY is HIGH
            if (bit_11 & (1<<11) ):
                return True
                
            new_opconfig = new_opconfig | (1 << 11)
        else:
        
            #if bit 11 is not set in the opconfig register and POLARITY is LOW
            if ( ~(bit_11 & (1<<11) ) ):
                return True
                
            new_opconfig = new_opconfig &  ~((1<< 11) )
        
        op_config_MSB = new_opconfig >> 8
        op_config_LSB = new_opconfig & 0x00FF
        op_config_data = [ op_config_MSB, op_config_LSB ] 
        
        #OpConfig register location: BQ27441_ID_REGISTERS id, offset 0
        self.write_extended_data(64,0,op_config_data,2)
        
    def setGPOUTFunction(self, GPOUT_FUNCTION):
        
        new_opconfig = self.read_opconfig_register()
        
        print("BEFORE GPOUT_FUNCTION:", new_opconfig)
        
        #isolate bit 2 of opconfig register
        bit_2 = new_opconfig & 0x04
        
        if (GPOUT_FUNCTION):
            
            #if bit 2 is set in the opconfig register and GPOUT_FUNCTION is BAT_LOW
            if (bit_2 & (1<<2) ):
                return True
                
            new_opconfig = new_opconfig | (1 << 2)
        else:
            #if bit 2 is not set in the opconfig register and GPOUT_FUNCTION is SOC_INT
            if (~ (bit_2 & (1<<2) ) ):
                return True
                
            new_opconfig = new_opconfig &  ~( (1<< 2) )
        
        print("GPOUT_Function BATLOWEN: ", new_opconfig)
        op_config_MSB = new_opconfig >> 8
        op_config_LSB = new_opconfig & 0x00FF
        op_config_data = [ op_config_MSB, op_config_LSB ] 
        
        #OpConfig register location: BQ27441_ID_REGISTERS id, offset 0
        self.write_extended_data(64,0,op_config_data,2)
        
    def setSOC1Thresholds(self, SET , CLR):
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
            
        self.write_extended_data( 49, 0, [SET,CLR], 2)
        
    def setSOCFThresholds(self, SET , CLR):
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
            
        self.write_extended_data( 49, 2, [SET,CLR], 2)

    def read_GPOUTPolarity(self):
        #BQ27441_OPCONFIG_GPIOPOL  (1<<11)
        #Get GPOUT polarity setting (active-high or active-low)
        return ( self.read_opconfig_register() & (1 <<11 ) ) 

    def read_GPOUTFunction(self):
        #BQ27441_OPCONFIG_BATLOWEN (1<<2)
        #Get GPOUT function (BAT_LOW or SOC_INT)
        return ( self.read_opconfig_register() & ( 1 << 2 ) )
        
    def read_SOC1SetThreshold(self):
        #Get SOC1_Set Threshold - threshold to set the alert flag
        #BQ27441_ID_DISCHARGE    49  // Discharge
        data = self.read_extended_data( 49, 0)
        return data

    def read_SOC1ClearThreshold(self):
        #Get SOC1_Clear Threshold - threshold to clear the alert flag
        #BQ27441_ID_DISCHARGE    49  // Discharge
        data = self.read_extended_data( 49, 1)
        return data
        
    def read_SOCFSetThreshold(self):
        #Get SOCF_Set Threshold - threshold to set the alert flag
        #BQ27441_ID_DISCHARGE    49  // Discharge
        data = self.read_extended_data( 49, 2)
        return data

    def read_SOCFClearThreshold(self):
        #Get SOCF_Clear Threshold - threshold to clear the alert flag
        #BQ27441_ID_DISCHARGE    49  // Discharge
        data = self.read_extended_data( 49, 3)
        return data
    #----------------Read Values------------------------------
        
    def read_voltage(self):
      
        #read voltage
        handle = self.pi.i2c_open(1, 0x55)
        d0_voltage = self.pi.i2c_read_byte_data(handle, 0x04) #read LSB
        d1_voltage = self.pi.i2c_read_byte_data(handle, 0x05) #read MSB
        self.pi.i2c_close(handle)              #close i2c
        
        print_str = "Voltage: %d" %(int(d1_voltage << 8 | d0_voltage) )
        print(print_str)
      
    def get_device_type(self):
        
        handle = self.pi.i2c_open(1, 0x55)     #open i2c at 0x55
        self.pi.i2c_write_byte_data(handle,0x00, 0x01)       #write to command register LSB
        self.pi.i2c_write_byte_data(handle,0x01, 0x00)       #write to command register MSB
        self.pi.i2c_close(handle)
        
        #quick read device name
        handle = self.pi.i2c_open(1, 0x55)     #open i2c at 0x55
        
        d0 = self.pi.i2c_read_byte_data(handle, 0x00)        #read LSB from register 0x00
        d1 = self.pi.i2c_read_byte_data(handle, 0x01)        #read MSB from register 0x01

        self.pi.i2c_close(handle)             
        
        print_str = "DEVICE ID: %d" %(int(d1 << 8 | d0) )
        print( print_str )

    def read_current(self):

        #read current
        handle = self.pi.i2c_open(1, 0x55)
        d0_current = self.pi.i2c_read_byte_data(handle, 0x10) #read LSB
        d1_current = self.pi.i2c_read_byte_data(handle, 0x11) #read MSB
        self.pi.i2c_close(handle)              #close i2c
        
        print_str = "Current: %d" %(int(d1_current << 8 | d0_current) )
        print(print_str)
        
    def read_capacity(self):

        #read current
        handle = self.pi.i2c_open(1, 0x55)
        d0 = self.pi.i2c_read_byte_data(handle, 0x0C) #read LSB
        d1 = self.pi.i2c_read_byte_data(handle, 0x0D) #read MSB
        self.pi.i2c_close(handle)              #close i2c
        
        print_str = "Capacity Remaining: %d" %(int(d1 << 8 | d0) )
        print(print_str)
        
    def read_full_capacity(self):

        #read current
        handle = self.pi.i2c_open(1, 0x55)
        d0 = self.pi.i2c_read_byte_data(handle, 0x0E) #read LSB
        d1 = self.pi.i2c_read_byte_data(handle, 0x0F) #read MSB
        self.pi.i2c_close(handle)              #close i2c
        
        print_str = "FULL Capacity: %d" %(int(d1 << 8 | d0) )
        print(print_str)
        
    def read_SOC(self):

        #read soc
        handle = self.pi.i2c_open(1, 0x55)
        d0_soc = self.pi.i2c_read_byte_data(handle, 0x1C) #read LSB
        d1_soc = self.pi.i2c_read_byte_data(handle, 0x1D) #read MSB
        self.pi.i2c_close(handle)              #close i2c
        
        print_str = "SOC: %d" %(int(d1_soc << 8 | d0_soc) )
        print(print_str)
        
        
    def read_SOH(self):

        #read soh
        handle = self.pi.i2c_open(1, 0x55)
        d0_soh_percentage = self.pi.i2c_read_byte_data(handle, 0x20) #read LSB
        d1_soh_status = self.pi.i2c_read_byte_data(handle, 0x21) #read MSB
        self.pi.i2c_close(handle)              #close i2c
        
        print_str_percent = "SOH Percent: %d" %(int(d0_soh_percentage) )
        print_str_status = "SOH Status: %d" %(int(d1_soh_status) )
        print(print_str_percent, " ", print_str_status)
        
        
    def test_read(self):
        self.read_voltage()
        self.read_current()
        self.read_capacity()
        self.read_full_capacity()
        self.read_SOC()
        self.read_SOH()
        self.get_device_type()
        
    def test_read_all(self):
    
        #read current
        handle = self.pi.i2c_open(1, 0x55)
        d0_current = self.pi.i2c_read_byte_data(handle, 0x10) #read LSB
        d1_current = self.pi.i2c_read_byte_data(handle, 0x11) #read MSB
        self.pi.i2c_close(handle)              #close i2c
        
        print_str = "Current: %d" %(int(d1_current << 8 | d0_current) )
        print(print_str)
        
        #read voltage
        handle = self.pi.i2c_open(1, 0x55)
        d0_voltage = self.pi.i2c_read_byte_data(handle, 0x04) #read LSB
        d1_voltage = self.pi.i2c_read_byte_data(handle, 0x05) #read MSB
        self.pi.i2c_close(handle)              #close i2c
        
        print_str = "Voltage: %d" %(int(d1_voltage << 8 | d0_voltage) )
        print(print_str)
        
        #read soc
        handle = self.pi.i2c_open(1, 0x55)
        d0_soc = self.pi.i2c_read_byte_data(handle, 0x1C) #read LSB
        d1_soc = self.pi.i2c_read_byte_data(handle, 0x1D) #read MSB
        self.pi.i2c_close(handle)              #close i2c
        
        print_str = "SOC: %d" %(int(d1_soc << 8 | d0_soc) )
        print(print_str)
        
        #read soh
        handle = self.pi.i2c_open(1, 0x55)
        d0_soh_percentage = self.pi.i2c_read_byte_data(handle, 0x20) #read LSB
        d1_soh_status = self.pi.i2c_read_byte_data(handle, 0x21) #read MSB
        self.pi.i2c_close(handle)              #close i2c
        
        print_str_percent = "SOH Percent: %d" %(int(d0_soh_percentage) )
        print_str_status = "SOH Status: %d" %(int(d1_soh_status) )
        print(print_str_percent, " ", print_str_status)
        
    def set_GPOUT(self, SOCISET, SOCICLR, SOCFSET, SOCFCLR, BATLOW, POL):
        """Setting GPOUT routine."""
        
        self.setGPOUTPolarity(POL)                                            #Set GPOUT to active-high
        time.sleep(1)
        
        self.setGPOUTFunction(BATLOW)                                          #Set GPOUT to BAT_LOW mode
        time.sleep(1)
        
        self.setSOC1Thresholds( SOCISET, SOCICLR)                              #Set SOCI set and clear thresholds
        time.sleep(1)
        
        self.setSOCFThresholds( SOCFSET, SOCFCLR)                              #Set SOCF set and clear thresholds
        time.sleep(1)
        
        self.exitConfig()
        time.sleep(1)
        
        if (self.read_GPOUTPolarity()):
            print("GPOUT set to active-HIGH")
        else:
            print("GPOUT set to active-LOW")
        
        time.sleep(1)
        print("GPOUT_POLARITY OPCONFIG REGISTER: ", self.read_opconfig_register() )
        print("---")
        
        
        if (self.read_GPOUTFunction()):
            print("GPOUT function set to BAT_LOW")
        else:
            print("GPOUT function set to SOC_INT")
        time.sleep(1)
        
        print("GPOUT_FUNCTION OPCONFIG REGISTER: ", self.read_opconfig_register() )
        print("---")
        time.sleep(1)
        
        print("SOC1 Set Threshold: ", str(( self.read_SOC1SetThreshold() )) )
        time.sleep(1)
        
        print("SOC1 Clear Threshold: ", str(( self.read_SOC1ClearThreshold() )) )
        time.sleep(1)
        
        print("SOCF Set Threshold: ", str(( self.read_SOCFSetThreshold() )) )
        time.sleep(1)
        
        print("SOCF Clear Threshold: ", str(( self.read_SOCFClearThreshold() )) )
        time.sleep(1)
        
if __name__ == '__main__':

    try:
        os.system("sudo pigpiod")
    except:
        print("daemon already running")
        
    pi = pigpio.pi()             # exit script if no connection
    if not pi.connected:
       exit()
    
    bq = BQ27441(pi, GPOUT_PIN)
    
    bq.set_capacity(SET_CAPACITY)
    time.sleep(1)
    
    bq.set_GPOUT()
    
    bq.test_read()
    time.sleep(1)
    bq.test_read_all()
    time.sleep(1)
    bq.test_read_all()
    
    pi.stop()