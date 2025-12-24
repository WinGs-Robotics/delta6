#include <SPI.h>
#include <ercks.h>
#include <EEPROM.h>  // Include the EEPROM library

/* ercks Rotary Position Sensors */
const byte csPins[6] = {3, 4, 5, 6, 7, 8};         // Array of CS pins for 6 sensors
const byte mosiPins[6] = {19, 18, 17, 16, 15, 14}; // Each sensor's corresponding MOSI pin
byte pinSCK = 2;                                   // Shared SCK pin

ercks sensors[6]; // Create 6 ercks sensor objects

#define START_BYTE 0xAA
#define CMD_CALIBRATION 0x01
#define CMD_READ 0x02

int calibrationOffsets[6] = {0}; // Stores calibration offset for each sensor
int positions[6] = {0};          // Stores current position for each sensor
uint8_t errorFlags = 0;          // Error flag byte

// Function declarations (function prototypes)
void processSerial();
uint8_t calculateChecksum(uint8_t *data, uint8_t length);
void handleCalibration();
void handleRead();
void updatePositions();

void setup() {
  Serial.begin(115200);

  // Load calibration offsets from EEPROM
  for (int i = 0; i < 6; i++) {
    EEPROM.get(i * sizeof(int), calibrationOffsets[i]); // Read calibration offsets from EEPROM
  }

  // Initialize each sensor
  for (int i = 0; i < 6; i++) {
    sensors[i].attach(csPins[i], pinSCK, mosiPins[i]);
  }

  //Serial.println("6x ercks Rotary Position Sensors Initialized");
}

void loop() {
  processSerial();    // Process serial commands
  updatePositions();  // Update sensor position data
  delay(10);          // Small delay
}

// Process serial data
void processSerial() {
  static enum { WAIT_START, READ_CMD, READ_CHECKSUM } state = WAIT_START;
  static uint8_t cmd;
  static uint8_t checksum;

  while (Serial.available()) {
    uint8_t byte = Serial.read();
    switch (state) {
      case WAIT_START:
        if (byte == START_BYTE) {
          state = READ_CMD;
        }
        break;
      case READ_CMD:
        cmd = byte;
        state = READ_CHECKSUM;
        break;
      case READ_CHECKSUM:
        checksum = byte;
        // Verify checksum
        uint8_t calcChecksum = calculateChecksum(&cmd, 1);
        if (checksum == calcChecksum) {
          // Process command
          if (cmd == CMD_CALIBRATION) {
            handleCalibration();
          } else if (cmd == CMD_READ) {
            handleRead();
          }
        }
        // Reset state regardless of checksum verification result
        state = WAIT_START;
        break;
    }
  }
}

// Calculate checksum (simple sum)
uint8_t calculateChecksum(uint8_t *data, uint8_t length) {
  uint8_t sum = 0;
  for (uint8_t i = 0; i < length; i++) {
    sum += data[i];
  }
  return sum;
}

// Handle calibration command
void handleCalibration() {
  // Read current position as calibration offset
  for (int i = 0; i < 6; i++) {
    int angle = sensors[i].readAngle();
    if (angle == -1) {
      errorFlags |= (1 << i);        // Set error flag for corresponding sensor
      calibrationOffsets[i] = 0;     // Set offset to 0 if an error occurs
    } else {
      calibrationOffsets[i] = angle; // Save calibration offset
      EEPROM.put(i * sizeof(int), calibrationOffsets[i]); // Store offset in EEPROM
    }
  }
  // Optionally, send confirmation to the host
}

// Handle read command
void handleRead() {
  // Prepare response packet
  uint8_t packet[1 + 6 * 2 + 1 + 1]; // Start byte + data + error flag + checksum
  uint8_t idx = 0;
  packet[idx++] = START_BYTE;

  // Add position data for each sensor (considering calibration offset)
  for (int i = 0; i < 6; i++) {
    int16_t adjustedAngle = positions[i] - calibrationOffsets[i];
    packet[idx++] = (adjustedAngle >> 8) & 0xFF; // High byte
    packet[idx++] = adjustedAngle & 0xFF;        // Low byte
  }

  // Add error flag byte
  packet[idx++] = errorFlags;

  // Calculate checksum
  uint8_t checksum = calculateChecksum(&packet[1], idx - 1); // Exclude start byte
  packet[idx++] = checksum;

  // Send data packet
  Serial.write(packet, idx);

  // Clear error flags after sending
  errorFlags = 0;
}

// Update sensor position data
void updatePositions() {
  for (int i = 0; i < 6; i++) {
    int angle = sensors[i].readAngle();
    if (angle == -1) {
      errorFlags |= (1 << i); // Set error flag for corresponding sensor
      positions[i] = 0;       // Set position to 0 if an error occurs, or handle as needed
    } else {
      positions[i] = angle;   // Update position data
    }
  }
}
