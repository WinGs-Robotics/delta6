from ..scservo_sdk.sts3023 import STS3032
from py_toolkit.rt_loop import RTLoop
import time


class Delta6GripperController(RTLoop):
    def __init__(self, motor_id: int, port: str, freq: float = 50, mode: str = "disable"):

        super().__init__(freq=freq)
        self.motor_id = motor_id
        self.motor = STS3032(port, 1000000)

        self.target_motor_angle = 0.0
        self.current_motor_angle = 0.0

        self.target_motor_torque = 0  # -1000 ~ +1000

        self.current_motor_load = 0.0
        self.max_width = 31.5  # mm
        self.angle_range = (0.0, 0.0)
        self.enabled = False
        self.to_set_enable = False
        self.mode = mode

    def setup(self):
        self.calibration()

        print("Entering RT loop...")

        self.set_mode(self.mode)

        super().setup()

    def loop(self):
        read_motor_angle, _, _ = self.motor.read_angle(self.motor_id)
        if read_motor_angle != None:
            self.current_motor_angle = read_motor_angle
        # load, direction, _, _ = self.motor.read_load(self.motor_id)
        # self.current_motor_load = direction * load

        if self.to_set_enable != self.enabled:
            if self.to_set_enable:
                self.motor.enable_torque(self.motor_id)
                self.enabled = True
            else:
                self.motor.disable_torque(self.motor_id)
                self.enabled = False
        if self.enabled == True:
            if self.mode == "pos":
                self.motor.write_angle(self.motor_id, self.target_motor_angle)
            elif self.mode == "torque":
                self.motor.write_torque(
                    self.motor_id, self.target_motor_torque)
            elif self.mode == "disable":
                self.motor.write_torque(
                    self.motor_id, self.target_motor_torque)
            else:
                print(f"[Error] Unknown mode: {self.mode}")

    def shutdown(self):
        super().shutdown()
        self.motor.disable_torque(self.motor_id)
        self.motor.close()
        print("Gripper shutdown and motor released.")

    def set_enable(self):
        self.to_set_enable = True
        return

    def set_disable(self):
        self.to_set_enable = False
        return

    def set_mode(self, mode: str):
        """
        switch mode to "pos" or "torque", "disable"
        """
        if mode not in ["pos", "torque", "disable"]:
            print(f"[Warning] Unsupported mode={mode}, defaulting to pos.")
            mode = "pos"

        self.mode = mode
        if self.mode == "pos":
            self.motor.set_max_torque(self.motor_id, 500)
            self.motor.set_control_mode(self.motor_id, 0)
            self.motor.enable_torque(self.motor_id)
            self.to_set_enable = True
            self.enabled = True
            print("[Info] Switched to Position Mode")
        elif self.mode == "disable":
            self.motor.set_control_mode(self.motor_id, 2)
            self.motor.disable_torque(self.motor_id)
            self.to_set_enable = False
            self.enabled = False
            print("[Info] Switched to Torque disable Mode")
        else:
            self.motor.set_control_mode(self.motor_id, 2)
            self.motor.enable_torque(self.motor_id)
            self.to_set_enable = True
            self.enabled = True
            print("[Info] Switched to Torque Mode")

    def set_angle(self, angle_deg: float):
        min_angle, max_angle = self.angle_range
        clamped_angle = max(min(angle_deg, max_angle), min_angle)
        if angle_deg != clamped_angle:
            print(
                f"[Warning] angle={angle_deg:.2f}° out of range, clamped to {clamped_angle:.2f}°")
        self.target_motor_angle = clamped_angle

    def set_torque(self, torque_val: int):
        torque_val = max(min(torque_val, 1000), -1000)
        self.target_motor_torque = torque_val

    def get_current_angle(self):
        return self.current_motor_angle

    def get_current_load(self):
        return self.current_motor_load

    def get_current_pos(self):
        _, max_angle = self.angle_range
        if max_angle <= 0:
            return 0.0
        pos = (self.current_motor_angle / max_angle) * self.max_width
        pos = max(0.0, min(pos, self.max_width))
        return pos

    def set_pos(self, pos_mm: float):
        pos_mm = max(0.0, min(pos_mm, self.max_width))
        _, max_angle = self.angle_range
        if max_angle <= 0:
            print("[Warning] angle_range invalid. Calibration not done yet?")
            return
        angle_deg = (pos_mm / self.max_width) * max_angle
        self.set_angle(angle_deg)

    def _wait_until_stall(self, direction: int, step_deg=2.0, stall_duration=1.0):
        while True:
            read_last_angle, _, _ = self.motor.read_angle(self.motor_id)
            if read_last_angle != None:
                target_angle = read_last_angle
                last_angle = read_last_angle
                unchanged_time = 0.0
                break

        while True:
            target_angle += direction * step_deg
            target_angle = max(min(target_angle, 180), -180)
            self.motor.write_angle(self.motor_id, target_angle)
            time.sleep(1.0 / self.freq)

            read_current_angle, _, _ = self.motor.read_angle(self.motor_id)
            if read_current_angle == None:
                continue
            else:
                current_angle = read_current_angle

                if abs(current_angle - last_angle) < 0.5:
                    unchanged_time += 1.0 / self.freq
                else:
                    unchanged_time = 0.0
                last_angle = current_angle

                if unchanged_time >= stall_duration:
                    return current_angle

    def calibration(self):
        print("== Delta6Gripper Calibration ==")
        self.motor.set_control_mode(self.motor_id, 0)  # 强制进入位置模式做校准
        self.motor.set_max_torque(self.motor_id, 500)
        time.sleep(0.2)

        self.motor.enable_torque(self.motor_id)
        time.sleep(0.2)

        self._wait_until_stall(direction=-1)
        self.motor.reset_zero(self.motor_id)
        time.sleep(0.2)
        print(f"Limit 1: 0.00°")

        angle2 = self._wait_until_stall(direction=1)
        print(f"Limit 2: {angle2:.2f}°")

        self.motor.disable_torque(self.motor_id)
        self.motor.set_max_torque(self.motor_id, 1000)

        self.angle_range = (0.0, abs(angle2))
        print(f"Gripper calibrated. Range: {self.angle_range}")
        self.set_angle(abs(angle2))


if __name__ == "__main__":
    gripper = Delta6GripperController(
        motor_id=1, port='COM8', freq=10, mode="torque")
    gripper.print_frequency = True
    gripper.setup()

    print("Main thread started loop_spin()...")
    gripper.loop_spin()
