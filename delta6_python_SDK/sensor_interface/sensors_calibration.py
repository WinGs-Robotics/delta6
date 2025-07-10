import time
from .interface import SensorInterface


def sensor_calibration(nano_port):

    sensor_interface = SensorInterface(port=nano_port)
    try:
        # Prompt user to move the device to a natural position
        print("Current position data:")
        # Initial read to display current position
        data_radians = sensor_interface.read_radians()
        print(data_radians)

        input(
            "Please move the device to a natural position, then press Enter to calibrate...")

        # Perform calibration
        sensor_interface.calibrate_sensors()

        # Display position data after calibration
        print("Position data after calibration:")
        data_radians = sensor_interface.read_radians()
        print(data_radians)
    finally:
        # Ensure that the SensorInterface is properly closed
        if hasattr(sensor_interface, 'close') and callable(getattr(sensor_interface, 'close')):
            sensor_interface.close()
            print("SensorInterface has been closed.")
            time.sleep(1)
        else:
            print("Warning: SensorInterface does not have a 'close' method. Resources may not be released properly.")
