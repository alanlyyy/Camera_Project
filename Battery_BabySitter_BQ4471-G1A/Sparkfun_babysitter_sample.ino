#include "C:\Users\Alan\Downloads\SparkFun_BQ27441_Arduino_Library-master\SparkFun_BQ27441_Arduino_Library-master\src\SparkFunBQ27441.h"
#include <Wire.h>

void setup() {
  // put your setup code here, to run once:
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

  //Serial.println(check_if_sealed());
  //Serial.println(unseal_device());
  //check_fuel_guage_config();

  set_capacity(2000);
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

  //convert data[1] from uint8_t to uint16_t shift bits left by 8 bits, and OR with data[0] uint8_t
  Serial.println(((uint16_t)data[1] << 8) | data[0]);     //0000010000100001

  return ((uint16_t)data[1] << 8) | data[0];
}

bool enterConfig(){
    check_if_sealed();
    unseal_device();
    unseal_device();

    if (enter_fuel_guage_config()){
      check_fuel_guage_config();
    }
  }

bool exitConfig(){
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
    Serial.print("Sealed Device ");
    Serial.println( ((uint16_t)data_seal[1] << 8) | data_seal[0]);
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

  Serial.print("Device is sealed: "); 
  Serial.println(status);
  Serial.println(status & (1 << 13));
  return status & (1 << 13);
}

bool unseal_device(void) {
  //UNSEAL device
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
  Serial.print("Device is unsealed: ");
  Serial.println(((uint16_t)data_unseal_read[1] << 8) | data_unseal_read[0]);
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

  Serial.print("fuel guage config: ");
  Serial.println((flags & (1 << 4) )); //if 0 there isn't config update detected, if 1 config update detected.


  if (timeout > 0)
    return true;
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

  enterConfig();

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

  exitConfig();
}

void write_check_sum(uint8_t newCheckSum){
  //writeBlockCheckSum(newCheckSum);
  //-------i2cWriteBytes(BQ27441_EXTENDED_CHECKSUM, &csum, 1);
  Wire.beginTransmission(0x55);
  Wire.write(0x60);
  Wire.write(newCheckSum);                        //write new check sum
  Wire.endTransmission(true);
}

uint8_t blockDataChecksum()
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
  Wire.write(0x61);             //BQ27441_EXTENDED_CONTROL
  Wire.write(enableByte);
  Wire.endTransmission(true);
}

void write_blockDataClass()
{
  //enable block data class
  Wire.beginTransmission(0x55);
  Wire.write(0x3E);             //BQ27441_EXTENDED_DATACLASS
  Wire.write(82);               //BQ27441_ID_STATE      82
  Wire.endTransmission(true);
}

void write_blockDataOffset()
{
  //enable block data offset
  Wire.beginTransmission(0x55);
  Wire.write(0x3F);             //BQ27441_EXTENDED_DATABLOCK 0x3F
  Wire.write(10/32);            //offset is usually 0
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
  
  for (int i=0; i<count; i++)
  {
    data[i] = Wire.read();
  }

  return ((uint16_t) data[1] << 8) | data[0];
}

bool setGPOUTPolarity(bool activeHigh)
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
  
  return writeOpConfig(newOpConfig);

  //---write 16 bit opconfig register in extended data.
  uint8_t opConfigMSB = value >> 8;
  uint8_t opConfigLSB = value & 0x00FF;
  uint8_t opConfigData[2] = {opConfigMSB, opConfigLSB};

    // OpConfig register location: BQ27441_ID_REGISTERS id, offset 0
  //return writeExtendedData(BQ27441_ID_REGISTERS, 0, opConfigData, 2);
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
