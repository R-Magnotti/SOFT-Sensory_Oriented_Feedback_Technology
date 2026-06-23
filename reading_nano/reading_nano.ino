const int analogPin = A0;  // Analog input pin

// Function to write a float as 4 raw bytes + CR/LF terminator
void writeToMatlab(float number)
{
  byte *b = (byte *) &number;
  Serial.write(b, 4);     // 4 raw bytes of the float
  Serial.write(13);       // '\r'
  Serial.write(10);       // '\n'
}

void setup() {
  Serial.begin(115200);   // Match the baud rate from your MATLAB-compatible code
}

void loop() {
  static unsigned long lastSampleTime = 0;
  const unsigned long SAMPLE_INTERVAL = 10000;  // 10,000 µs = 100 Hz
  
  unsigned long now = micros();
  
  if (now - lastSampleTime >= SAMPLE_INTERVAL) {
    lastSampleTime += SAMPLE_INTERVAL;  // Precise timing
    
    int sensorValue = analogRead(analogPin);
    float voltage = sensorValue * (5.0 / 1023.0);
    
    writeToMatlab(voltage);  // Send as binary float
  }
}