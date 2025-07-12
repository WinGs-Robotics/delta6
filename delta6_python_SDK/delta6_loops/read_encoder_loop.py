# ReadEncoderLoop.py

import time
import threading
import logging
from delta6_sensor_interface.interface import SensorInterface


class ReadEncoderLoop:
    def __init__(self, nano_port, encoder_dir):
        """
        Initialize the ReadEncoderLoop by loading configuration and establishing a connection to the robot.
        Also initializes the SensorInterface for reading encoder data.
        """

        self.encoder_dir = encoder_dir

        # Initialize encoder_result with default values
        self.encoder_result = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        # Lock to ensure thread-safe access to encoder_result
        self.encoder_lock = threading.Lock()

        # Initialize SensorInterface for reading encoder data
        try:
            self.sensor_interface = SensorInterface(port=nano_port)
        except Exception as e:
            logging.error(f"Failed to initialize SensorInterface: {e}")
            exit(1)  # Exit if SensorInterface initialization fails

        # Thread control
        self._stop_event = threading.Event()
        self._thread = None

    def loop(self):
        """
        Execute the loop task: read encoder data and update encoder_result.
        """
        try:
            # Read encoder data using SensorInterface
            encoder_data = self.sensor_interface.read_radians()

            # Update encoder_result with thread safety
            if encoder_data:
                with self.encoder_lock:
                    self.encoder_result = [
                        a * b for a, b in zip(encoder_data, self.encoder_dir)]

            else:
                logging.warning("Failed to read Encoder data")

        except Exception as e:
            logging.error(f"Error getting encoder data: {e}")

    def get_encoder_reading(self):
        """
        Get the latest encoder reading.

        :return: List of encoder values or [None, ...] if an error occurred.
        """
        with self.encoder_lock:
            return self.encoder_result.copy()

    def _spin_loop(self, frequency):
        """
        Internal method to run the spinning loop in a separate thread.

        :param frequency: Loop frequency in Hz.
        """
        interval = 1.0 / frequency  # Seconds
        logging.info(
            f"ReadForceLoop thread started at {frequency} Hz (every {interval * 1000:.2f} ms)")
        while not self._stop_event.is_set():
            # Execute the loop task
            self.loop()

            # Sleep for the interval duration
            time.sleep(interval)

    def loop_spin(self, frequency=100):
        """
        Start the spinning loop in a separate thread that runs the loop method at the specified frequency.

        :param frequency: Loop frequency in Hz. Default is 100 Hz.
        """
        if self._thread is None:
            self._thread = threading.Thread(
                target=self._spin_loop, args=(frequency,), daemon=True)
            self._thread.start()
            logging.info("ReadEncoderLoop spinning thread has been started.")
        else:
            logging.warning(
                "ReadEncoderLoop spinning thread is already running.")

    def stop_spin(self):
        """
        Stop the spinning loop gracefully.
        """
        if self._thread is not None:
            self._stop_event.set()
            self._thread.join()
            logging.info("ReadEncoderLoop spinning thread has been stopped.")
            self._thread = None
        else:
            logging.warning("ReadEncoderLoop spinning thread is not running.")

    def shutdown(self):
        """
        Shutdown the spinning loop and close the SensorInterface.
        """
        self.stop_spin()
        # Ensure that SensorInterface is properly closed
        if hasattr(self, 'sensor_interface') and callable(getattr(self.sensor_interface, 'close', None)):
            self.sensor_interface.close()
            logging.info("SensorInterface has been closed.")
        else:
            logging.warning(
                "SensorInterface does not have a 'close' method. Resources may not be released properly.")


if __name__ == "__main__":
    """
    Example usage of ReadEncoderLoop with threading.
    This block can be used for testing purposes.
    """
    import logging

    # Configure logging at the beginning of your script
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    NANO_PORT_NAME = "/dev/ttyACM0"
    ENCODER_DIR = [1, 1, 1, -1, -1, -1]

    # Initialize the ReadEncoderLoop
    read_encoder_loop = ReadEncoderLoop(
        nano_port=NANO_PORT_NAME, encoder_dir=ENCODER_DIR)

    # Start the spinning loop
    read_encoder_loop.loop_spin(frequency=100)

    try:
        while True:
            # Example: Access encoder data every second
            encoder_data = read_encoder_loop.get_encoder_reading()
            logging.info(f"Latest Encoder Data: {encoder_data}")
            time.sleep(1)  # Sleep for 1 second
    except KeyboardInterrupt:
        logging.info("\nReadEncoderLoop stopped by user.")
    finally:
        # Shutdown the loop and clean up resources
        read_encoder_loop.shutdown()
