import math
import serial
import time

# Define constants for the communication protocol
START_BYTE = 0xAA
CMD_CALIBRATION = 0x01
CMD_READ = 0x02

class SensorInterface:
    def __init__(self, port='/dev/ttyACM0', baudrate=115200, timeout=10):
        """
        Initialize the serial connection.
        """
        try:
            self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
            print(f"Serial port {port} opened successfully.")
            time.sleep(0.1)

        except serial.SerialException as e:
            print(f"Error opening serial port {port}: {e}")
            self.ser = None

    def calculate_checksum(self, data):
        """
        Calculate checksum (simple sum).
        """
        return sum(data) & 0xFF  # Ensure result is within 0-255

    def send_command(self, cmd):
        """
        Send command to Arduino.
        """
        if self.ser is None:
            print("Serial port not initialized.")
            return

        packet = bytearray()
        packet.append(START_BYTE)
        packet.append(cmd)
        checksum = self.calculate_checksum([cmd])
        packet.append(checksum)

        try:
            self.ser.write(packet)
            #print(f"Command {cmd:#04x} sent.")
        except serial.SerialException as e:
            print(f"Error sending command: {e}")

    def read_response(self):
        """
        Read and parse the response from Arduino.
        """
        if self.ser is None:
            print("Serial port not initialized.")
            return None

        try:
            # Look for the start byte
            while True:
                start_byte = self.ser.read(1)
                if not start_byte:
                    print("Timeout waiting for start byte.")
                    return None
                if start_byte[0] == START_BYTE:
                    break

            # Read the remaining data (14 bytes)
            expected_length = 14  # 6 sensors * 2 bytes + 1 error flag + 1 checksum
            data = self.ser.read(expected_length)
            if len(data) < expected_length:
                print("Incomplete data received.")
                return None

            # Parse sensor data
            sensor_values = []
            idx = 0
            for i in range(6):
                # Combine high byte and low byte to form a signed integer
                high_byte = data[idx]
                low_byte = data[idx + 1]
                value = (high_byte << 8) | low_byte
                if value >= 0x8000:
                    value -= 0x10000  # Convert to negative if needed
                sensor_values.append(value)
                idx += 2

            # Read error flags
            error_flags = data[idx]
            idx += 1

            # Read checksum
            received_checksum = data[idx]

            # Verify data integrity with checksum
            checksum_data = [byte for byte in data[:idx]]  # Exclude checksum byte
            calculated_checksum = self.calculate_checksum(checksum_data)
            if calculated_checksum != received_checksum:
                print("Checksum mismatch.")
                return None

            return sensor_values, error_flags

        except serial.SerialException as e:
            print(f"Error reading response: {e}")
            return None

    def calibrate_sensors(self):
        """
        Send calibration command.
        """
        self.send_command(CMD_CALIBRATION)
        # Wait for Arduino to process the calibration command
        time.sleep(0.1)

    def read_sensors(self):
        """
        Send read command and retrieve sensor data.
        """
        self.send_command(CMD_READ)
        time.sleep(0.05)  # Wait for Arduino to prepare data
        result = self.read_response()
        if result:
            sensor_values, error_flags = result
            # Process error flags
            for i in range(6):
                if error_flags & (1 << i):
                    print(f"Sensor {i+1} error.")
                # else:
                #     print(f"Sensor {i+1} value: {sensor_values[i]}")
        else:
            print("Failed to read sensor data.")

    def read_radians(self):
        """
        Convert the latest sensor angle data to radians.
        Each 14-bit sensor value ranges from 0 to 16383, representing 0 to 2π radians.
        """
        self.send_command(CMD_READ)
        #time.sleep(0.05)  # Wait for Arduino to prepare data
        result = self.read_response()
        radians_values = []
        if result:
            sensor_values, error_flags = result
            # Process error flags
            for i in range(6):
                if error_flags & (1 << i):
                    print(f"Sensor {i+1} error.")
                    return []
                else:
                    angle_in_radians = round((sensor_values[i] / 16383.0) * (2 * math.pi), 5)
                    radians_values.append(angle_in_radians)
        else:
            print("Failed to read sensor data.")
            return []
        
        return radians_values

    def close(self):
        """
        Close the serial connection.
        """
        if self.ser:
            self.ser.close()
            print("Serial port closed.")
