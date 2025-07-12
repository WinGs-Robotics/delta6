from scservo_sdk import *


class STS3032:
    def __init__(self, device_name='/dev/ttyUSB0', baudrate=1000000):
        self.port_handler = PortHandler(device_name, baudrate)
        if not self.port_handler.openPort():
            raise RuntimeError("Failed to open port")

        self.packet_handler = sms_sts(self.port_handler)

        self.control_mode = 0

    def close(self):
        self.port_handler.closePort()

    def write_register(self, motor_id, address, length, data):
        if length == 1:
            return self.packet_handler.write1ByteTxRx(motor_id, address, data)
        elif length == 2:
            return self.packet_handler.write2ByteTxRx(motor_id, address, data)
        elif length == 4:
            return self.packet_handler.write4ByteTxRx(motor_id, address, data)
        else:
            raise ValueError("Unsupported data length. Use 1, 2, or 4.")

    def read_register(self, motor_id, address, length):
        if length == 1:
            data, comm_result, error = self.packet_handler.read1ByteTxRx(
                motor_id, address)
        elif length == 2:
            data, comm_result, error = self.packet_handler.read2ByteTxRx(
                motor_id, address)
        elif length == 4:
            data, comm_result, error = self.packet_handler.read4ByteTxRx(
                motor_id, address)
        else:
            raise ValueError("Unsupported data length. Use 1, 2, or 4.")
        return data, comm_result, error

    def enable_torque(self, motor_id):
        TORQUE_ENABLE_ADDR = 40
        VEL_ADDR = 46
        ACC_ADDR = 41
        TIM_ADDR = 44
        self.write_register(motor_id, VEL_ADDR, 2, 2000)
        self.write_register(motor_id, ACC_ADDR, 1, 200)
        self.write_register(motor_id, TIM_ADDR, 2, 0)
        return self.write_register(motor_id, TORQUE_ENABLE_ADDR, 1, 1)

    def disable_torque(self, motor_id):
        TORQUE_ENABLE_ADDR = 40
        return self.write_register(motor_id, TORQUE_ENABLE_ADDR, 1, 0)

    def read_angle(self, motor_id):
        address = 56  # PRESENT_POSITION_L
        raw_pos, comm_result, error = self.packet_handler.read2ByteTxRx(
            motor_id, address)
        if comm_result != COMM_SUCCESS or raw_pos is None:
            return None, comm_result, error

        angle_deg = (raw_pos * 360.0 / 4095.0) - 180.0
        return angle_deg, comm_result, error

    def read_velocity(self, motor_id):
        address = 58  # PRESENT_POSITION_L
        raw_vel, comm_result, error = self.packet_handler.read2ByteTxRx(
            motor_id, address)

        def map_vel(value):
            if value > 2885:
                return 2885-value
            else:
                return value

        angular_vel = (raw_vel * 360.0 / 4095.0)
        maped_angular_vel = map_vel(angular_vel)
        return maped_angular_vel, comm_result, error

    def write_angle(self, motor_id, angle_deg):
        if self.control_mode != 0:
            print(
                f"[Info] Motor {motor_id} not in position mode, switching to mode=0 now.")
            self.set_control_mode(motor_id, 0)

        if not -180.0 <= angle_deg <= 180.0:
            raise ValueError("Angle must be between -180 and +180 degrees")

        # print(f"[Debug] (Pos Mode) Writing angle {angle_deg:.2f}° to motor {motor_id}")
        raw_pos = int((angle_deg + 180.0) * 4095.0 / 360.0)
        GOAL_POSITION_ADDR = 42  # GOAL_POSITION_L
        return self.packet_handler.write2ByteTxRx(motor_id, GOAL_POSITION_ADDR, raw_pos)

    def set_max_torque(self, motor_id, torque_val):
        if not (0 <= torque_val <= 1000):
            raise ValueError("Torque value must be between 0 and 1000")
        MAX_TORQUE_ADDR = 48
        return self.write_register(motor_id, MAX_TORQUE_ADDR, 2, torque_val)

    def read_load(self, motor_id):
        LOAD_ADDR = 60
        raw_load, comm_result, error = self.read_register(
            motor_id, LOAD_ADDR, 2)

        if comm_result != COMM_SUCCESS or raw_load is None:
            return None, None, comm_result, error

        load_value = raw_load & 0x3FF
        direction = -1 if (raw_load & 0x400) else 1
        return load_value, direction, comm_result, error

    def reset_zero(self, motor_id):
        TORQUE_ENABLE_ADDR = 40
        return self.write_register(motor_id, TORQUE_ENABLE_ADDR, 1, 128)

    def set_control_mode(self, motor_id, mode):
        """
        mode: 0 => Position Mode
              2 => Torque Mode
        """
        if mode not in [0, 2]:
            raise ValueError(
                "Unsupported control mode. Use 0 (Position) or 2 (Torque).")

        CONTROL_MODE_ADDR = 33
        print(f"[Debug] Setting motor {motor_id} to control mode {mode}")
        self.write_register(motor_id, CONTROL_MODE_ADDR, 1, mode)
        self.control_mode = mode

    def write_torque(self, motor_id, torque_val):
        if self.control_mode != 2:
            print(
                f"[Info] Motor {motor_id} not in torque mode, switching to mode=2 now.")
            self.set_control_mode(motor_id, 2)

        def map_torque(value):
            if value < 0:
                # Map -1000 to -1 to 1025 to 2024
                return int(-value + 1024)
            else:
                return value

        def clamp(value, min_value, max_value):
            return max(min_value, min(value, max_value))

        clamped_torque = clamp(torque_val, -1000, 1000)
        clamped_torque = int(clamped_torque)
        mapped_torque = map_torque(clamped_torque)
        torque_data = self.int_to_byte_array(mapped_torque)

        # print(f"[Debug] (Torque Mode) Writing torque={mapped_torque} to motor {motor_id}")
        TORQUE_ADDR = 44
        return self.packet_handler.writeTxRx(motor_id, TORQUE_ADDR, 2, torque_data)

    def read_pos_and_load(self, motor_id):
        START_ADDR = 56      # Position_L
        LEN = 6       # 2B Pos + 2B Vel + 2B Load

        raw, comm_result, error = self.packet_handler.readTxRx(
            motor_id, START_ADDR, LEN)

        if comm_result != COMM_SUCCESS or raw is None:
            return None, None, comm_result, error

        pos_raw = int.from_bytes(raw[0:2], "little")
        load_raw = int.from_bytes(raw[4:6], "little")

        angle_deg = (pos_raw * 360.0 / 4095.0) - 180.0
        load_val = load_raw & 0x3FF
        direction = -1 if (load_raw & 0x400) else 1

        return angle_deg, direction * load_val, comm_result, error

    def int_to_byte_array(self, value, length=2):
        return [(value >> (8 * i)) & 0xFF for i in range(length)]
