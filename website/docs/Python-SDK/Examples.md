---
sidebar_position: 2
---

# Quick Start Examples 💡

This section provides a quick guide on how to run a basic real-time loop using the Delta6 Python SDK.

The example script is located at:

```bash
delta6_python_SDK/example.py
```

---

## 1. Purpose of This Example

The `example.py` script demonstrates:

- Calibrating the sensors
- Reading encoder data in real-time
- Computing forward kinematics
- Visualizing the estimated end-effector forces

It serves as a **minimal starting point** to verify that all hardware and software are working correctly.

---

## 2. How to Run

Activate the Python environment first:

```bash
# On Ubuntu
source venv/bin/activate

# On Windows
source venv/Scripts/activate
```

Then run the example:

```bash
python delta6_python_SDK/example.py --port /dev/ttyACM0 --freq 50
```

- Replace `/dev/ttyACM0` with your Arduino Nano Every's actual port.
- `--freq` controls the loop frequency (default is 50 Hz).

---

## 3. How It Works

The script defines a `MainLoop` class (derived from `RTLoop`) to organize initialization, looping, and shutdown behaviors.

The full execution flow is as follows:

### Initialization (`setup()` method)

1️⃣ **Sensor Calibration**  
   - Code: `sensor_calibration(nano_port=self.nano_port)`
   - Prompts the user to move the device to a neutral position and records zero offsets.

2️⃣ **Start Encoder Reading Loop**  
   - Code: `self.read_encoder_loop = ReadEncoderLoop(nano_port=self.nano_port, encoder_dir=ENCODER_DIR)`
   - Encoder angles are read asynchronously at high frequency.

3️⃣ **Initialize Delta6 Kinematics Model**  
   - Code: `self.Delta6 = DeltaRobot()`
   - Creates a new DeltaRobot instance to calculate forward kinematics from encoder readings.

4️⃣ **Start Force Visualizer**  
   - Code: 
     ```python
     self.force_visualizer = ForceVisualizer(...)
     self.force_visualizer.start()
     ```
   - A real-time window opens to display the estimated end-effector forces.

5️⃣ **Start Real-Time Loop Spin**  
   - Code: `super().setup()`
   - Prepares the internal threading/timing logic to start looping.

---

### Main Loop (`loop()` method)

Each real-time cycle (`50 Hz` by default):

- **Read encoder data**  
  Code: `encoder_reading = self.read_encoder_loop.get_encoder_reading()`

- **Update Delta6 model**  
  Code: `self.Delta6.update(*encoder_reading)`

- **Compute and print end-effector pose**  
  Code: 
  ```python
  delta6_pose_reading = self.Delta6.get_FK_result()
  print(f"End-effector pose (x, y, z, roll, pitch, yaw): {delta6_pose_reading}")
  ```

- **Update the force visualizer**  
  Code:
  ```python
  delta6_end_force = self.Delta6.get_end_force()
  self.force_visualizer.update_forces([delta6_end_force])
  ```

Example console output:

```
End-effector pose (x, y, z, roll, pitch, yaw): [0.012, 0.005, 0.230, 0.01, -0.02, 0.00]
```

---

### Shutdown (`shutdown()` method)

When exiting the program (e.g., Ctrl+C):

- **Stop the force visualizer**  
  Code: `self.force_visualizer.stop()`

- **Terminate real-time loop cleanly**  
  Code: `super().shutdown()`

- **Print shutdown confirmation**  
  Code: `print("Force visualizer shutdown.")`

---

## 4. Notes

> 📌 **Tip:**  
You can adjust the `--freq` parameter to higher values (e.g., 100 Hz) for faster updates, depending on your PC performance.

> ⚡ **Warning:**  
Always run sensor calibration before starting meaningful data collection, to avoid force/pose estimation errors.

---

🎯 **Congratulations!**  
By running this quick start example, you have verified that your Delta6 system hardware and software are properly set up!
