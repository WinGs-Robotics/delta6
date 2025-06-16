# Delta6 Firmware Communication Protocol

## Overview

This document describes the communication protocol between the PC (host) and the Delta6 end-effector firmware, including command formats, response formats, functional descriptions, and error handling mechanisms.

---

## 📱 Command Frame Format (PC → Firmware)

| Field           | Description                                  |
|:---------------:|:--------------------------------------------:|
| Start Byte      | `0xAA`, indicates the beginning of a frame   |
| Command Byte    | Operation code (Calibration or Read)         |
| Checksum        | Simple additive checksum                    |

**Command Byte Values**:
- `0x01`: **Calibration Command**
- `0x02`: **Read Command**

**Checksum**:  
The checksum is calculated as the simple sum of the start byte and command byte, modulo 256.

---

## 📥 Response Frame Format (Firmware → PC)

| Field                | Description                                         |
|:--------------------:|:---------------------------------------------------:|
| Start Byte           | `0xAA`, indicates the beginning of a frame          |
| Sensor 1 Data        | 2 bytes (signed integer, calibrated angle)          |
| ...                  | ...                                                 |
| Sensor 6 Data        | 2 bytes (signed integer, calibrated angle)          |
| Error Flags          | 1 byte (each bit indicates a sensor read error)     |
| Checksum             | 1 byte (simple additive checksum)                  |

**Sensor Data**:  
Each sensor outputs a signed 2-byte integer representing the calibrated angle.

**Error Flags**:  
- 1 byte total.
- Each bit corresponds to one sensor.  
  If a bit is `1`, the corresponding sensor encountered a read error.

**Checksum**:  
The checksum is calculated as the simple sum of all bytes after the start byte.

---

## 🔧 Functional Details

### Calibration Function

Upon receiving a **Calibration Command (0x01)**, the firmware:
- Reads the current angle values from all sensors.
- Stores them as calibration offsets.

### Read Function

Upon receiving a **Read Command (0x02)**, the firmware:
- Reads the current sensor values.
- Subtracts calibration offsets.
- Sends the calibrated values along with error flags and checksum.

### Error Handling

In the `updatePositions()` function:
- If a sensor read returns `-1`, the corresponding error flag bit is set.
- Errors are reported in the response frame's error flag byte.

### Data Integrity

- A simple additive checksum ensures data integrity.
- CRC can be used for more robust error detection if needed.

---

## 📌 Notes

- Start byte `0xAA` must always be included at the beginning of each frame.
- Only two commands (`0x01` and `0x02`) are currently supported.
- All multi-byte data are transmitted **big-endian** unless otherwise specified.

---

✅ **This communication protocol ensures reliable, efficient interaction between the PC and the Delta6 firmware, enabling robust 6-DOF force-sensing operations.**

## Acknowledgment

**Some parts of the documentation and code were assisted by language models (OpenAI's ChatGPT) during their initial drafting. All content was subsequently reviewed and verified by the project authors.**