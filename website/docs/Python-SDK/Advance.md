---
sidebar_position: 3
---

# Advanced Usage 🚀

This section provides a detailed explanation of the **DeltaRobot** class located at:

```bash
delta6_python_SDK/kinematics/delta6_analytics.py
```

The `DeltaRobot` class offers methods for advanced kinematics calculations, force estimation, and internal torque computations for the Delta6 system.

---

## 1. Initialization

Create a Delta6 robot model by specifying its physical parameters:

```python
from kinematics.delta6_analytics import DeltaRobot

delta6 = DeltaRobot(
    short_arm_length=40.0,         # Length of the short (servo) arm [mm]
    parallel_arm_length=120.0,     # Length of the parallel (linkage) arm [mm]
    base_radius=72.0,              # Radius of the fixed base [mm]
    end_effector_radius=21.24      # Radius of the moving end-effector platform [mm]
)
```

> 📌 **Note:** Default values are already tuned for the Delta6 system.

---

## 2. Main Interfaces

### 2.1 Updating Joint States

You can update the robot's internal state (angles and torques) using:

```python
delta6.update(theta1, theta2, theta3, theta4, theta5, theta6)
```

- `theta1` to `theta6` are joint angles (in radians).
- Internally, it updates both joint angles and spring torques.

---

### 2.2 Forward Kinematics

To compute the end-effector pose (position and orientation) from joint angles:

```python
pose = delta6.get_FK_result()
```

Returns a tuple:

```
(x, y, z, roll, pitch, yaw)
```
- All positions are in meters (m).
- All rotations are in radians (rad).

> 📌 **Tip:** The Delta6 model internally handles the mechanical offsets and link geometry.

---

### 2.3 Inverse Kinematics

To solve the required joint angles for a given target pose:

```python
thetas = delta6.inverse_kinematics(x, y, z, roll, pitch, yaw)
```

- Input: desired position (m) and orientation (rad).
- Output: six joint angles `(theta1, theta2, theta3, theta4, theta5, theta6)`.
- Returns `None` if the target is unreachable.

---

### 2.4 Force Estimation

To estimate the end-effector force/torque from spring readings:

```python
force = delta6.get_end_force()
```

Returns a tuple:

```
(Fx, Fy, Fz, Mx, My, Mz)
```
- Forces are in Newtons (N).
- Moments are in Newton-meters (Nm).

Internally, it uses the joint torques and geometric Jacobians.

---

### 2.5 Force-to-Torque Mapping

Given a desired force vector at the end-effector, you can calculate the required torques:

```python
torques = delta6.calculate_torque_123(Fx_target, Fy_target, Fz_target)
```

Useful for simulating force control.

---

### 2.6 Force-to-Pose Mapping

Given a full 6-DOF wrench `(Fx, Fy, Fz, Mx, My, Mz)`, estimate the corresponding pose:

```python
pose = delta6.calculate_euler_pose(Fx, Fy, Fz, Mx, My, Mz)
```

Returns:

```
(x, y, z, roll, pitch, yaw)
```

This is useful for **force-sensitive end-effector control** based on spring torque feedback.

---

## 3. Internal Model Details

> ⚙️ **Mechanics:**
> 
> - The Delta6 kinematics assumes 3 symmetric legs.
> - It internally applies mechanical z-offset corrections.
> - Rotations are handled using **scipy.spatial.transform** Euler conversion utilities.
> 
> - Forces are estimated based on spring extension/compression, taking into account the Delta geometry.

---

## 4. Summary

| Function | Purpose |
| :--- | :--- |
| `update()` | Update joint angles and compute torques |
| `get_FK_result()` | Compute end-effector pose from joint states |
| `inverse_kinematics()` | Solve joint states from target pose |
| `get_end_force()` | Estimate forces and moments |
| `calculate_torque_123()` | Map desired forces to spring torques |
| `calculate_euler_pose()` | Map desired forces/moments to end-effector pose |

---

🎯 **Advanced Tip:**  
You can combine real-time encoder readings + `update()` + `get_end_force()` to build a **real-time force estimation loop**, enabling force-controlled teleoperation or haptic feedback applications.

---
