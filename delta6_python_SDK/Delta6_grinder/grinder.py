import serial
import time
from rt_loops.rt_loop import RTLoop

class Delta6_grinder(RTLoop):
    """
    A real-time loop-based motor speed controller that communicates with a lower-level device (e.g., Arduino) over serial.
    Waits for the device to send 'initialized' before setup completes.
    """

    def __init__(self, port='/dev/ttyACM1', freq=50):
        """
        :param port: Serial port (e.g., '/dev/ttyACM1')
        :param baud: Baud rate (e.g., 115200)
        :param freq: Control loop frequency in Hz
        """
        super().__init__(freq=freq)
        self.port = port
        self.baud = 115200

        # Speed range: 0.0 to 100.0
        self.speed = 0.0
        self.min_speed = 0.0
        self.max_speed = 100.0

        # Serial object
        self.ser = None

    def setup(self):
        """
        Called once before the main loop starts.
        Initializes the serial port and waits for Arduino to send 'initialized'.
        """
        # 1. Open serial connection
        self.ser = serial.Serial(port=self.port, baudrate=self.baud, timeout=1)
        time.sleep(2)  # Allow time for Arduino to reset and start up

        print("[Info] Waiting for Arduino to send 'Initialized'...")
        self._wait_for_arduino_init(msg="Initialized", timeout=10.0)
        
        print("[Info] Delta6_grinder setup complete.")

        # Call parent setup method if needed
        super().setup()

    def loop(self):
        """
        This method is called repeatedly at the specified frequency.
        Here it reads and prints any available serial data.
        """
        # while self.ser.in_waiting > 0:
        #     response = self.ser.readline().decode('utf-8').strip()
        #     if response:
        #         print("[Delta6_grinder] Arduino says:", response)
        pass

    def write_speed_percentage(self, percentage: float):
        """
        Sets the motor speed as a percentage (0 to 100) and sends it to the serial port.
        The Arduino should read it using Serial.parseFloat().
        """
        percentage = max(self.min_speed, min(self.max_speed, percentage))
        self.speed = percentage
        cmd = f"{self.speed:.1f}\n"
        self.ser.write(cmd.encode('utf-8'))

    def stop(self):
        """
        Stops the motor by setting speed to 0 and sending the command.
        """
        self.write_speed_percentage(0.0)
        print("[Info] Delta6_grinder stop() called, speed = 0.0")

    def shutdown(self):
        """
        Called after the loop ends. Cleans up serial resources.
        """
        self.stop()
        if self.ser and self.ser.is_open:
            self.ser.close()
        print("[Info] Delta6_grinder shutdown complete.")
        super().shutdown()

    def _wait_for_arduino_init(self, msg="initialized", timeout=10.0):
        """
        Waits for a specific message from Arduino to confirm initialization.
        :param msg: Expected message string from Arduino
        :param timeout: Timeout in seconds
        """
        start_time = time.time()
        while True:
            # Check for timeout
            if (time.time() - start_time) > timeout:
                raise TimeoutError(f"Waiting for '{msg}' timed out after {timeout} seconds.")

            # Check incoming serial data
            if self.ser.in_waiting > 0:
                response = self.ser.readline().decode('utf-8').strip()
                if response:
                    print(f"[Delta6_grinder] Received: '{response}'")
                    if response == msg:
                        print("[Delta6_grinder] Arduino init message detected!")
                        break
            else:
                time.sleep(0.1)  # Small delay to prevent tight loop


if __name__ == "__main__":
    # Example usage: run loop at 50 Hz
    grinder = Delta6_grinder(port='/dev/ttyACM1', freq=50)
    grinder.print_frequency = True

    grinder.setup()
    print("[Info] Starting main thread loop_spin()...")
    grinder.loop_spin()

    print("[Info] Main thread exiting.")
