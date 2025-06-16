#ifndef ERCKS_H
#define ERCKS_H

#include "Arduino.h"

class ercks {
public:
  ercks();
  void attach(byte pinSS, byte pinSCK, byte pinMOSI);
  int readAngle();

private:
  byte _pinSS;
  byte _pinSCK;
  byte _pinMOSI;
  void _spiWByte(uint8_t tx);
  uint8_t _spiRByte();
};

#endif
