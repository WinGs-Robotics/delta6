---
sidebar_position: 3
---

# Calibration Procedure 🎯

This section explains how to calibrate the Delta6 sensors to ensure accurate force and displacement measurements.

The calibration script is located at:

```bash
delta6_python_SDK/sensor_interface/sensors_calibration.py
```

---

## 1. Preparation

Before starting the calibration:

- Ensure the Arduino Nano Every is properly connected and communicating.
- Complete the microcontroller setup steps described previously.
- Place the Delta6 device in a **neutral, relaxed position** without external forces.

---

## 2. Running the Calibration Script

Activate the Python virtual environment (if not already activated):

```bash
# On Ubuntu
source venv/bin/activate

# On Windows
source venv/Scripts/activate
```

Then run the calibration script:

```bash
python delta6_python_SDK/sensor_interface/sensors_calibration.py --port /dev/ttyACM0
```

Replace `/dev/ttyACM0` with the correct port for your Arduino Nano Every.

---

## 3. Calibration Procedure

The script will perform the following steps:

1️⃣ **Initial Reading:**  
The script reads and prints the current sensor data (in radians) to the terminal.

2️⃣ **User Prompt:**  
You will be prompted:

```
Please move the device to a natural position, then press Enter to calibrate...
```
Move the Delta6 device gently into its natural resting position, and press **Enter** when ready.

3️⃣ **Calibration Execution:**  
The system will record the resting values and perform internal calibration to zero out any offsets.

4️⃣ **Post-Calibration Reading:**  
The script will print the new sensor data, showing that the baseline has been adjusted.

5️⃣ **Resource Cleanup:**  
The script will automatically close the serial connection safely after calibration is complete.

---

## 4. Important Notes

> ⚡ **Tip:**  
Always calibrate the device **before each new session** to ensure consistent measurement accuracy.

> 📌 **Warning:**  
If you skip calibration, sensor readings may include offsets from mechanical relaxation or minor misalignments.

---

🎯 **Congratulations!**  
Once calibration is complete, your Delta6 system is ready for real-time data acquisition and experiments.

