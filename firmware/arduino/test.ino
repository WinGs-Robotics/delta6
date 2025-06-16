#include <SPI.h>
#include <MLX90316.h>

/* MLX90316 Rotary Position Sensors */
const byte csPins[6] = {3, 4, 5, 6, 7, 8};        
const byte mosiPins[6] = {19, 18, 17, 16, 15, 14}; 
byte pinSCK = 2;                                   

MLX90316 sensors[6];

void setup() {
  Serial.begin(115200);

  for (int i = 0; i < 6; i++) {
    sensors[i].attach(csPins[i], pinSCK, mosiPins[i]);
  }

  Serial.println("6x MLX90316 Rotary Position Sensors Initialized");
}

void loop() {
  for (int i = 0; i < 6; i++) {
    int angle = sensors[i].readAngle(); 

    float preciseAngle = (float)angle * 360.0 / 3600.0;

    Serial.print("Sensor ");
    Serial.print(i + 1);
    Serial.print(" Angle = ");
    Serial.print(preciseAngle); 
    Serial.print(" ");
  }
  delay(10); 
  Serial.println("");
}
