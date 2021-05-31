//--- defining some values----------------------
const int SSPin = 11;
const int SCKPin = 10;
const int MISOPin = 9;
const int MOSIPin = 8;

void setup() {
  
  Serial.begin(9600); //used to write to terminal
  
  pinMode(MISOPin, OUTPUT);

  pinMode(SSPin, INPUT);

  pinMode(SCKPin, INPUT);

  pinMode(MOSIPin, INPUT);

}

byte RecvChar(){
    byte x = 0b00000000;
    
    for (int i = 0; i <8; i++)
    {
      bitWrite(x,i, digitalRead(MOSIPin));
      
      delay(10);
      
    }

    return (char)x;
}

void loop() {

  if (digitalRead(SSPin) == LOW){
      byte c = RecvChar();
      Serial.println((char)c);
  }

  delay(100);
}
