//----define--------------
const int SSPin = 11;
const int SCKPin = 10;
const int MISOPin = 9;
const int MOSIPin = 8;

byte sendData = 65; //value to be send
byte slaveData = 0; // for storing the value sent by slave

void setup() {
  // put your setup code here, to run once:
  pinMode(MISOPin, INPUT);

  pinMode(SSPin, OUTPUT);

  pinMode(SCKPin, OUTPUT);

  pinMode(MOSIPin, OUTPUT);

  
  digitalWrite(SSPin, HIGH); //set SS pin high, when SS goes from 1 -> 0 communication begins.
  

}

byte bitBangData(byte _send) { //This function transmit the data via bitbanging

  byte _receive = 0;

  for(int i =0; i <8;i++){ // 8 bits in a byte

    digitalWrite(MOSIPin, bitRead(_send,i)); //send output to slave
    digitalWrite(SCKPin, HIGH);   //clock pin high
    bitWrite(_receive, i , digitalRead(MISOPin)); //Capture Slave Output
    digitalWrite(SCKPin, LOW);    //clock pin low
    delay(10);  //delay by 5 ms
  }

  return _receive;
}

void sendWord(String s){
  for(int i=0;i<4;i++){
    bitBangData((byte)s[i]);
  }
}
void loop() {
  digitalWrite(SSPin, LOW);   //1->0 communication start

  //slaveData = bitBangData(sendData);  //data transmission
  sendWord("Hope");
  
  digitalWrite(SSPin, HIGH);   //0->1 communication ends

  delay(100);
}
