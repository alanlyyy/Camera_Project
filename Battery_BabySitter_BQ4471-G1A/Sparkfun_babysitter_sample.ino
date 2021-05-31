#include "C:\Users\Alan\Downloads\SparkFun_BQ27441_Arduino_Library-master\SparkFun_BQ27441_Arduino_Library-master\src\SparkFunBQ27441.h"
#include <Wire.h>


// Set BATTERY_CAPACITY to the design capacity of your battery.
const unsigned int BATTERY_CAPACITY = 2000; // e.g. 850mAh battery

const byte SOCI_SET = 15; // Interrupt set threshold at 20%
const byte SOCI_CLR = 20; // Interrupt clear threshold at 25%
const byte SOCF_SET = 5; // Final threshold set at 5%
const byte SOCF_CLR = 10; // Final threshold clear at 10%

// Arduino pin connected to BQ27441's GPOUT pin
const int GPOUT_PIN = 2;

void setup() {
  // put your setup code here, to run once:
  pinMode(GPOUT_PIN, INPUT_PULLUP); // Set the GPOUT pin as an input w/ pullup
  Serial.begin(115200);
  Wire.begin();  //enable I2C transmission

  //BQ27441_DEVICE_ID = 0x0421
  if (get_device_type() == 0x0421) {
    Serial.println("I2C connected");
    Serial.println("Connected to BQ27441!");

  } else {
    Serial.println("I2C not connected");
    Serial.println("Error: Unable to communicate with BQ27441.");
    Serial.println("  Check wiring and try again.");
    Serial.println("  (Battery must be plugged into Battery Babysitter!)");
    while (1);
  }

  // In this example, we'll manually enter and exit config mode. By controlling
  // config mode manually, you can set the chip up faster -- completing all of
  // the set up in a single config mode sweep.
  write_enterConfig(); // To configure the values below, you must be in config mode
  set_capacity2(BATTERY_CAPACITY); // Set the battery capacity
  write_setGPOUTPolarity(LOW); // Set GPOUT to active-high
  write_setGPOUTFunction(BAT_LOW); // Set GPOUT to BAT_LOW mode
  write_setSOC1Thresholds(SOCI_SET, SOCI_CLR); // Set SOCI set and clear thresholds
  write_setSOCFThresholds(SOCF_SET, SOCF_CLR); // Set SOCF set and clear thresholds
  write_exitConfig();

  // Use lipo.GPOUTPolarity to read from the chip and confirm the changes
  if (read_GPOUTPolarity())
    Serial.println("GPOUT set to active-HIGH");
  else
    Serial.println("GPOUT set to active-LOW");

  // Use lipo.GPOUTFunction to confirm the functionality of GPOUT
  if (read_GPOUTFunction())
    Serial.println("GPOUT function set to BAT_LOW");
  else
    Serial.println("GPOUT function set to SOC_INT");

  // Read the set and clear thresholds to make sure they were set correctly
  Serial.println("SOC1 Set Threshold: " + String((read_SOC1SetThreshold())));
  Serial.println("SOC1 Clear Threshold: " + String(read_SOC1ClearThreshold()));
  Serial.println("SOCF Set Threshold: " + String(read_SOCFSetThreshold()));
  Serial.println("SOCF Clear Threshold: " + String(read_SOCFClearThreshold()));
}

uint16_t get_device_type() {

  //write 0x01 to slave device.
  uint8_t command[2] = {0x01, 0x00}; // LSB to MSB

  Wire.beginTransmission(0x55);  //device address is 0x55
  Wire.write((uint8_t) 0);      //write to subaddress

  for (int i = 0; i < 2; i++) {
    Wire.write(command[i]);
  }

  Wire.endTransmission(true);

  //--------------------------------------

  //read data from slave device
  Wire.beginTransmission(0x55);
  Wire.write((uint8_t)0);
  Wire.endTransmission(true);

  Wire.requestFrom(0x55, 2);    //read 2 bytes from address 0x55


  uint8_t data[2] = {0, 0} ;

  for (int i = 0; i < 2; i++) {
    data[i] = Wire.read();
  }
  Wire.endTransmission(true);

  return ((uint16_t)data[1] << 8) | data[0];
}

bool write_enterConfig(){
    check_if_sealed();
    unseal_device();
    unseal_device();

    if (enter_fuel_guage_config()){
      check_fuel_guage_config();
    }
  }

bool write_exitConfig(){
  //exit out of configuration mode.
  
  
  //BQ27441_CONTROL_SEALED 0x20

  //write soft reset comand to update SOC and voltage reading
  uint8_t subCommandMSB = (0x42 >> 8);               
  uint8_t subCommandLSB = (0x42 & 0x00FF);
  uint8_t command[2] = {subCommandLSB, subCommandMSB};

  Wire.beginTransmission(0x55);
  Wire.write((uint8_t)0);
  for ( int i = 0; i < 2; i++) {
    Wire.write(command[i]);                 //BQ27441_CONTROL_SOFT_RESET 0x42
  }
  Wire.endTransmission(true);


  //check config status
  Wire.beginTransmission(0x55);
  Wire.write(0x06);                         //BQ27441_COMMAND_FLAGS      0x06 // Flags()
  Wire.endTransmission(true);
  Wire.requestFrom(0x55, 2);
  uint8_t data[2];
  for (int i = 0; i < 2; i++)
  {
    data[i] = Wire.read();
  }
  
  int16_t timeout = BQ72441_I2C_TIMEOUT;
  uint16_t flags = ((uint16_t) data[1] << 8) | data[0];   //if flags == 0, config mode is turned off

  while ((timeout--) && ((flags & (1 << 4) )))  //BQ27441_FLAG_CFGUPMODE  (1<<4)
    delay(1);

  if (timeout > 0)
  {
    //readControlWord(BQ27441_CONTROL_SEALED);
    uint8_t seal_command[2] = {0x20, 0x00};     //Seal back up if we IC was sealed coming in
    uint8_t data_seal[2] = {0,0};

    //write seal command
    Wire.beginTransmission(0x55);
    Wire.write((uint8_t)0);
    for ( int i = 0; i < 2; i++) {
      Wire.write(command[i]);
    }
    Wire.endTransmission(true);

    //acknowledge seal command
    Wire.beginTransmission(0x55);
    Wire.write((uint8_t)0);                
    Wire.endTransmission(true);
    Wire.requestFrom(0x55, 2);
    for (int i = 0; i < 2; i++)
    {
      data_seal[i] = Wire.read();
    }
  }

  return true;
  
}

bool check_if_sealed(void) {
  //check if device is sealed.
  
  //return stat & BQ27441_STATUS_SS (1<<13)
  //readControlWord(BQ27441_CONTROL_STATUS);

  uint8_t command[2] = {0x00, 0x00};        //BQ27441_CONTROL_STATUS      0x00
  uint8_t data[2] = {0, 0};

  Wire.beginTransmission(0x55);             //write address
  Wire.write((uint8_t)0);                   //write subaddress 0
  for ( int i = 0; i < 2; i++) {
    Wire.write(command[i]);
  }
  Wire.endTransmission(true);

  Wire.beginTransmission(0x55);
  Wire.write( (uint8_t) 0);
  Wire.endTransmission(true);

  Wire.requestFrom(0x55, 2);
  for (int i = 0; i < 2; i++)
  {
    data[i] = Wire.read();
  }

  uint16_t status =  ((uint16_t)data[1] << 8) | data[0];

  return status & (1 << 13);
}

bool unseal_device(void) {
  //UNSEAL devices
  //readControlWord(BQ27441_UNSEAL_KEY);
  uint8_t subCommandMSB = (0x8000 >> 8);
  uint8_t subCommandLSB = (0x8000 & 0x00FF);
  uint8_t command[2] = {subCommandLSB, subCommandMSB};
  uint8_t data_unseal_command[2] =  { subCommandLSB, subCommandMSB }; //0x8000
  uint8_t data_unseal_read[2] = {0, 0};

  //write command 0x8000
  Wire.beginTransmission(0x55);
  Wire.write((uint8_t)0);
  for ( int i = 0; i < 2; i++) {
    Wire.write(data_unseal_command[i]);
  }
  Wire.endTransmission(true);

  //read acknoledgement from BQ27441-G1A
  Wire.beginTransmission(0x55);
  Wire.write( (uint8_t) 0);
  Wire.endTransmission(true);

  Wire.requestFrom(0x55, 2);
  for (int i = 0; i < 2; i++)
  {
    data_unseal_read[i] = Wire.read();
  }
  return ((uint16_t)data_unseal_read[1] << 8) | data_unseal_read[0];
}

bool enter_fuel_guage_config() {
  //enter into configuration mode for the fuel guage

  uint8_t subCommandMSB = (0x13 >> 8);  //BQ27441_CONTROL_SET_CFGUPDATE  0x13
  uint8_t subCommandLSB = (0x13 & 0x00FF);
  uint8_t command[2] = {subCommandLSB, subCommandMSB};
  uint8_t data[2] = {0, 0};

  //write command 0x8000
  Wire.beginTransmission(0x55);
  Wire.write((uint8_t)0);
  for ( int i = 0; i < 2; i++) {
    Wire.write(command[i]);
  }
  Wire.endTransmission(true);

  return true;
}

bool check_fuel_guage_config() {
  //check if the fuel guage is in configuration mode
  int16_t timeout = BQ72441_I2C_TIMEOUT;

  uint8_t data[2];

  //i2cReadBytes(BQ27441_COMMAND_FLAGS, data, 2);
  Wire.beginTransmission(0x55);
  Wire.write(0x06);                 //BQ27441_COMMAND_FLAGS      0x06 // Flags()
  Wire.endTransmission(true);

  Wire.requestFrom(0x55, 2);

  for (int i = 0; i < 2; i++)
  {
    data[i] = Wire.read();
  }

  uint16_t flags = ((uint16_t) data[1] << 8) | data[0];

  while ((timeout--) && (!(flags & (1 << 4) )))  //BQ27441_FLAG_CFGUPMODE  (1<<4)
    delay(1);

  if (timeout > 0)
    return true;
}

bool set_capacity2(uint16_t capacity)
{
  //high level version of set_capacity hiding the details.
  uint8_t capMSB = capacity >> 8;
  uint8_t capLSB = capacity & 0x00FF;
  uint8_t capacityData[2] = {capMSB, capLSB};

  write_extended_data(82, 10, capacityData, 2);
}
bool set_capacity(uint16_t capacity)
{
    // Write to STATE subclass (82) of BQ27441 extended memory.
  // Offset 0x0A (10)
  // Design capacity is a 2-byte piece of data - MSB first
  // Unit: mAh
  uint8_t capMSB = capacity >> 8;
  uint8_t capLSB = capacity & 0x00FF;
  uint8_t capacityData[2] = {capMSB, capLSB};

  write_enterConfig();

  //-----------------------------------------------------

  //enable block data control
  uint8_t enableByte = 0x00;
  Wire.beginTransmission(0x55);
  Wire.write(0x61);             //BQ27441_EXTENDED_CONTROL
  Wire.write(enableByte);
  Wire.endTransmission(true);

  //enable block data class
  Wire.beginTransmission(0x55);
  Wire.write(0x3E);             //BQ27441_EXTENDED_DATACLASS
  Wire.write(82);               //BQ27441_ID_STATE      82
  Wire.endTransmission(true);

  //enable block data offset
  Wire.beginTransmission(0x55);
  Wire.write(0x3F);             //BQ27441_EXTENDED_DATABLOCK 0x3F
  Wire.write(10/32);            //offset is usually 0
  Wire.endTransmission(true);

  //calculate the checksum
  uint8_t data[32];
  uint8_t oldCheckSum= 0;
  Wire.beginTransmission(0x55);
  Wire.write(0x40);             //BQ27441_EXTENDED_BLOCKDATA  0x40
  Wire.endTransmission(true);
  Wire.requestFrom(0x55,32);     //request 32 bytes of data

  for( int i = 0; i < 32; i++){
    data[i] = Wire.read();
  }

  for (int i=0; i<32; i++)
  {
    oldCheckSum += data[i];
  }
  oldCheckSum = 255 - oldCheckSum;

  uint8_t recalculate_check_sum;
  //i2cReadBytes(BQ27441_EXTENDED_CHECKSUM, &csum, 1);

  //write blockDataCheckSum()
  Wire.beginTransmission(0x55);
  Wire.write(0x60);                             //BQ27441_EXTENDED_CHECKSUM  0x60
  Wire.endTransmission(true);
  Wire.requestFrom(0x55, 1);
  recalculate_check_sum = Wire.read();

  //writeExtendedData(BQ27441_ID_STATE, 10, capacityData, 2);
  for( int i = 0; i <2; i++){

    //writeBlockData((offset % 32) + i, data[i]);
    uint8_t address = (10%32) + i + 0x40;        //BQ27441_EXTENDED_BLOCKDAT = 0x40;

    //i2cWriteBytes(address, &data, 1);
    Wire.beginTransmission(0x55);
    Wire.write(address);
    Wire.write(capacityData[i]);
    Wire.endTransmission(true);
  }

  uint8_t newCheckSum= 0;
  Wire.beginTransmission(0x55);
  Wire.write(0x40);                               //BQ27441_EXTENDED_BLOCKDATA  0x40
  Wire.endTransmission(true); 

  Wire.requestFrom(0x55,32);                      //request 32 bytes of data

  for( int i = 0; i < 32; i++){
    data[i] = Wire.read();
  }

  for (int i=0; i<32; i++)
  {
    newCheckSum += data[i];
  }
  newCheckSum = 255 - newCheckSum;


  //writeBlockCheckSum(newCheckSum);
  //-------i2cWriteBytes(BQ27441_EXTENDED_CHECKSUM, &csum, 1);
  Wire.beginTransmission(0x55);
  Wire.write(0x60);
  Wire.write(newCheckSum);                        //write new check sum
  Wire.endTransmission(true);

  write_exitConfig();
}

// Use BlockData() to write a byte to an offset of the loaded data
bool write_block_data(uint8_t offset, uint8_t data){
  //writeExtendedData(BQ27441_ID_STATE, 10, capacityData, 2);
    
  uint8_t address = offset + 0x40;        //BQ27441_EXTENDED_BLOCKDAT = 0x40;
  Wire.beginTransmission(0x55);
  Wire.write(address);                    //write subaddress
  Wire.write(data);                       //write data
  Wire.endTransmission(true);

  return true;
}

// Use BlockData() to read a byte from the loaded extended data
uint8_t read_block_data(uint8_t offset)
{
  uint8_t ret;
  uint8_t address = offset + 0x40;        //BQ27441_EXTENDED_BLOCKDATA  0x40 // BlockData()
  
  //i2cReadBytes(address, &ret, 1);
  Wire.beginTransmission(0x55);
  Wire.write(address);
  Wire.endTransmission(true);

  Wire.requestFrom(0x55, 1);              //read 1 byte of data.
  ret = Wire.read();
  
  return ret;
}

void write_check_sum(uint8_t newCheckSum){
  //writeBlockCheckSum(newCheckSum);
  //-------i2cWriteBytes(BQ27441_EXTENDED_CHECKSUM, &csum, 1);
  Wire.beginTransmission(0x55);
  Wire.write(0x60);
  Wire.write(newCheckSum);                        //write new check sum
  Wire.endTransmission(true);
}

uint8_t write_blockDataChecksum()
{
   uint8_t recalculate_check_sum;

  //write blockDataCheckSum()
  Wire.beginTransmission(0x55);
  Wire.write(0x60);                             //BQ27441_EXTENDED_CHECKSUM  0x60
  Wire.endTransmission(true);
  Wire.requestFrom(0x55, 1);
  recalculate_check_sum = Wire.read();

  return recalculate_check_sum;
}

uint8_t calculate_check_sum(){
  //calculate the checksum
  uint8_t data[32];
  uint8_t csum= 0;
  Wire.beginTransmission(0x55);
  Wire.write(0x40);             //BQ27441_EXTENDED_BLOCKDATA  0x40
  Wire.endTransmission(true);
  
  Wire.requestFrom(0x55,32);     //request 32 bytes of data

  for( int i = 0; i < 32; i++){
    data[i] = Wire.read();
  }

  for (int i=0; i<32; i++)
  {
    csum += data[i];
  }
  csum = 255 - csum;

  return csum;
}


void  write_blockDataControl()
{
    //enable block data control
  uint8_t enableByte = 0x00;
  Wire.beginTransmission(0x55);
  Wire.write(0x61);                   //BQ27441_EXTENDED_CONTROL
  Wire.write(enableByte);
  Wire.endTransmission(true);
}

void write_blockDataClass(uint8_t classID)
{
  //enable block data class
  Wire.beginTransmission(0x55);
  Wire.write(0x3E);                   //BQ27441_EXTENDED_DATACLASS
  Wire.write(classID);          
  Wire.endTransmission(true);
}

void write_blockDataOffset(uint8_t offset)
{
  //enable block data offset
  Wire.beginTransmission(0x55);
  Wire.write(0x3F);                   //BQ27441_EXTENDED_DATABLOCK 0x3F
  Wire.write(offset / 32);            //offset is usually 0
  Wire.endTransmission(true);
}
uint16_t read_opconfig_register()
{
  //read opconfig register values
  
  uint8_t data[2];

  Wire.beginTransmission(0x55);
  Wire.write(0x3A);                                    // BQ27441_EXTENDED_OPCONFIG  0x3A // OpConfig()
  Wire.endTransmission(true);
  
  Wire.requestFrom(0x55, 2);                           
  
  for (int i=0; i<2; i++)
  {
    data[i] = Wire.read();
  }

  return ((uint16_t) data[1] << 8) | data[0];
}

// Set GPOUT polarity to active-high or active-low
bool write_setGPOUTPolarity(bool activeHigh)
{
  uint16_t oldOpConfig = read_opconfig_register();

  //Check to see if we need to update opConfig         //BQ27441_OPCONFIG_GPIOPOL  (1<<11) "11th bit"
  if ((activeHigh && (oldOpConfig & (1<<11) )) ||
        (!activeHigh && !(oldOpConfig & (1<<11) )))
    return true;

  uint16_t newOpConfig = oldOpConfig;

  if (activeHigh)
    newOpConfig |= (1 << 11);
  else
    newOpConfig &= ~(1 << 11);

  //-------writeOpConfig(newOpConfig)-----------------------
 
  //---write 16 bit opconfig register in extended data.
  uint8_t opConfigMSB = newOpConfig >> 8;
  uint8_t opConfigLSB = newOpConfig & 0x00FF;
  uint8_t opConfigData[2] = {opConfigMSB, opConfigLSB};

  // OpConfig register location: BQ27441_ID_REGISTERS id, offset 0
  write_extended_data(64, 0, opConfigData,2);           //BQ27441_ID_REGISTERS    64  // Registers

}

// Set the SOC1 set and clear thresholds to a percentage
bool write_setSOC1Thresholds(uint8_t set, uint8_t clear)
{
  uint8_t thresholds[2];
  thresholds[0] = constrain(set, 0, 100);                           //constrain is from arduino.h, constrains X between A and B, for example SET between 0 and 100
  thresholds[1] = constrain(clear, 0, 100);
  return write_extended_data(49, 0, thresholds, 2);                 //BQ27441_ID_DISCHARGE    49  // Discharge
}

// Set the SOCF set and clear thresholds to a percentage
bool write_setSOCFThresholds(uint8_t set, uint8_t clear)
{
  uint8_t thresholds[2];
  thresholds[0] = constrain(set, 0, 100);
  thresholds[1] = constrain(clear, 0, 100);
  return write_extended_data(49, 2, thresholds, 2);   //BQ27441_ID_DISCHARGE    49  // Discharge
}

// Set GPOUT function to BAT_LOW or SOC_INT
bool write_setGPOUTFunction(gpout_function function)
{
  uint16_t oldOpConfig =  read_opconfig_register();
  
  // Check to see if we need to update opConfig:                    //BQ27441_OPCONFIG_BATLOWEN (1<<2) BIT 2 of opConfig register.
  if ((function && (oldOpConfig & (1<<2))) ||
        (!function && !(oldOpConfig & (1<<2))))
    return true;
  
  // Modify BATLOWN_EN bit of opConfig:
  uint16_t newOpConfig = oldOpConfig;
  if (function)
    newOpConfig |= (1<<2);
  else
    newOpConfig &= ~( (1<<2) );

  // Write new opConfig

  //-------writeOpConfig(newOpConfig)-----------------------
 
  //---write 16 bit opconfig register in extended data.
  uint8_t opConfigMSB = newOpConfig >> 8;
  uint8_t opConfigLSB = newOpConfig & 0x00FF;
  uint8_t opConfigData[2] = {opConfigMSB, opConfigLSB};

  // OpConfig register location: BQ27441_ID_REGISTERS id, offset 0
  write_extended_data(64, 0, opConfigData,2);           //BQ27441_ID_REGISTERS    64  // Registers

}
uint8_t read_extended_data(uint8_t classID, uint8_t offset)
{
  uint8_t retData = 0;
  
  write_enterConfig();
    
  write_blockDataControl(); // // enable block data memory control
  
  write_blockDataClass(classID); // Write class ID using DataBlockClass()
  
  write_blockDataOffset(offset / 32); // Write 32-bit block offset (usually 0)
  
  calculate_check_sum(); // Compute checksum going in
  
  uint8_t oldCsum = write_blockDataChecksum();
  
  retData = read_block_data(offset % 32); // Read from offset (limit to 0-31)
  
  write_exitConfig();
  
  return retData;
}
// Write a specified number of bytes to extended data specifying a 
// class ID, position offset.
bool write_extended_data(uint8_t classID, uint8_t offset, uint8_t * data, uint8_t len)
{
  if (len > 32)
    return false;
  
  write_enterConfig();
  
  write_blockDataControl();

  write_blockDataClass(classID);

  write_blockDataOffset(offset / 32);
  
  calculate_check_sum(); // Compute checksum going in
  uint8_t oldCsum = write_blockDataChecksum();  //read checksum value from fuel guage ic

  // Write data bytes:
  for (int i = 0; i < len; i++)
  {
    // Write to offset, mod 32 if offset is greater than 32
    // The blockDataOffset above sets the 32-bit block
    write_block_data((offset % 32) + i, data[i]);
  }
  
  // Write new checksum using BlockDataChecksum (0x60)
  uint8_t newCsum = calculate_check_sum(); // Compute the new checksum
  write_check_sum(newCsum);

  write_exitConfig();
  
  return true;
}

//------------------Read values from BQ27441-----------------------------
void read_current()
{
//  //read current
//
  //readWord(uint16_t subAddress)
  //uint8_t data[2];
  //i2cReadBytes(subAddress, data, 2);
  //return ((uint16_t) data[1] << 8) | data[0];
  //

  uint8_t data[2];

  Wire.beginTransmission(0x55);
  Wire.write(0x10);                 //BQ27441_COMMAND_AVG_CURRENT    0x10 // AverageCurrent()
  Wire.endTransmission(true);

  Wire.requestFrom(0x55, 2);

  for (int i=0; i<2; i++)
  {
    data[i] = Wire.read();
  }

  Serial.print("AVG Current Reading: ");
  Serial.print( (int16_t) ( ((uint16_t) data[1] << 8) | data[0] ) );
  Serial.println(" mA");
}

void read_voltage()
{
  //read voltage
  uint8_t data[2];

  Wire.beginTransmission(0x55);
  Wire.write(0x04);                 //BQ27441_COMMAND_VOLTAGE      0x04 // Voltage()
  Wire.endTransmission(true);

  Wire.requestFrom(0x55, 2);

  for (int i=0; i<2; i++)
  {
    data[i] = Wire.read();
  }

  Serial.print("AVG Voltage Reading: ");
  Serial.print( (int16_t) ( ((uint16_t) data[1] << 8) | data[0] ) );
  Serial.println( " mV");
}

void read_capacity()
{
  //read remaining capacity of battery
  uint8_t data[2];

  Wire.beginTransmission(0x55);
  Wire.write(0x0C);                   //BQ27441_COMMAND_REM_CAPACITY 0x0C // RemainingCapacity()
  Wire.endTransmission(true);

  Wire.requestFrom(0x55, 2);

  for (int i=0; i<2; i++)
  {
    data[i] = Wire.read();
  }

  Serial.print("Remaining Capacity Reading: ");
  Serial.print( (int16_t) ( ((uint16_t) data[1] << 8) | data[0] ) );
  Serial.println( " mAh");
}

void read_full_capacity()
{
//read full capacity of battery
  uint8_t data[2];

  Wire.beginTransmission(0x55);
  Wire.write(0x0E);                   //BQ27441_COMMAND_FULL_CAPACITY  0x0E // FullChargeCapacity()
  Wire.endTransmission(true);

  Wire.requestFrom(0x55, 2);

  for (int i=0; i<2; i++)
  {
    data[i] = Wire.read();
  }

  Serial.print("FULL Capacity Reading: ");
  Serial.print( (int16_t) ( ((uint16_t) data[1] << 8) | data[0] ) );
  Serial.println( " mAh");
}

void read_soc()
{
  //read state of charge
  uint8_t data[2];

  Wire.beginTransmission(0x55);
  Wire.write(0x1C);                   //BQ27441_COMMAND_SOC        0x1C // StateOfCharge()
  Wire.endTransmission(true);

  Wire.requestFrom(0x55, 2);

  for (int i=0; i<2; i++)
  {
    data[i] = Wire.read();
  }

  Serial.print("SOC Reading: ");
  Serial.print( (int16_t) ( ((uint16_t) data[1] << 8) | data[0] ) );
  Serial.println( " %");
}

void read_soh(int soh_type = 1)
{
  //read state of health

  uint8_t data[2];

  Wire.beginTransmission(0x55);
  Wire.write(0x20);                   //BQ27441_COMMAND_SOH        0x20 // StateOfHealth()
  Wire.endTransmission(true);

  Wire.requestFrom(0x55, 2);

  for (int i=0; i<2; i++)
  {
    data[i] = Wire.read();
  }
  uint16_t sohRaw = ((uint16_t) data[1] << 8) | data[0];
  uint8_t sohStatus = sohRaw >> 8;
  uint8_t sohPercent = sohRaw & 0x00FF;

  Serial.print("State of Health Reading: ");
  Serial.print( (int) sohPercent );
  Serial.println( " %");
  Serial.println(" ");
  Serial.print("State of Health Status Reading: ");
  Serial.println( (int) sohStatus);
}

// Get GPOUT polarity setting (active-high or active-low)
bool read_GPOUTPolarity()
{
  uint16_t opConfigRegister = read_opconfig_register();
  
  return (opConfigRegister & (1 << 11 ) );       //BQ27441_OPCONFIG_GPIOPOL  (1<<11)
}

// Get GPOUT function (BAT_LOW or SOC_INT)
bool read_GPOUTFunction()
{
  uint16_t opConfigRegister = read_opconfig_register();
  
  return (opConfigRegister & (1<<2) );  //BQ27441_OPCONFIG_BATLOWEN (1<<2)
}

// Get SOC1_Set Threshold - threshold to set the alert flag
uint8_t read_SOC1SetThreshold(void)
{
  return read_extended_data(49, 0); //BQ27441_ID_DISCHARGE    49  // Discharge
}

// Get SOC1_Clear Threshold - threshold to clear the alert flag
uint8_t read_SOC1ClearThreshold(void)
{
  return read_extended_data(49, 1);  //BQ27441_ID_DISCHARGE   49  // Discharge
}

// Get SOCF_Set Threshold - threshold to set the alert flag
uint8_t read_SOCFSetThreshold(void)
{
  return read_extended_data(49, 2);   //BQ27441_ID_DISCHARGE   49  // Discharge
}

// Get SOCF_Clear Threshold - threshold to clear the alert flag
uint8_t read_SOCFClearThreshold(void)
{
  return read_extended_data(49, 3); //BQ27441_ID_DISCHARGE   49  // Discharge
}

void print_stats(){
  // put your main code here, to run repeatedly:
  read_current();
  read_capacity();
  read_full_capacity();
  read_voltage();
  read_soh();
  read_soc();
}
void loop() {
  read_capacity();
  read_full_capacity();
  delay(1000);
}
