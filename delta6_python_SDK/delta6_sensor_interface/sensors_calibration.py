"""
Robust sensor-calibration helper.
© 2025  MindChildren Robotics
"""

from contextlib import contextmanager
import time
from typing import List, Optional
from .interface import SensorInterface


@contextmanager
def open_sensor(port: str,
                baudrate: int = 115200,
                timeout: float = 0.5):
    """Context-managed SensorInterface that always closes the port."""
    sensor = SensorInterface(port=port,
                             baudrate=baudrate,
                             timeout=timeout)
    if hasattr(sensor, "serial"):
        sensor.serial.reset_input_buffer()
    try:
        yield sensor
    finally:
        if hasattr(sensor, "close") and callable(sensor.close):
            sensor.close()
            print("[Info] SensorInterface closed.")


def try_read(sensor: SensorInterface,
             retries: int = 8,
             delay: float = 0.15,
             expected_len: Optional[int] = None) -> List[float]:
    """
    Read radians with retry until a non-empty, valid packet is received.

    Parameters
    ----------
    sensor : SensorInterface
    retries : int
        Maximum attempts before giving up.
    delay : float
        Sleep between attempts (seconds).
    expected_len : int | None
        If given, also check len(data) == expected_len.

    Returns
    -------
    List[float]
        Valid joint angles.

    Raises
    ------
    RuntimeError
        If still no valid data after all retries.
    """
    for attempt in range(1, retries + 1):
        try:
            data = sensor.read_radians()
            if data and (expected_len is None or len(data) == expected_len):
                return data
            print(f"[Warn] Empty/partial packet on attempt {attempt}.")
        except Exception as exc:  # noqa: BLE001
            print(f"[Warn] read_radians failed (attempt {attempt}): {exc}")
        time.sleep(delay)
    raise RuntimeError("Unable to read valid radians after multiple retries.")


def sensor_calibration(nano_port: str,
                       expected_len: int = 6):
    """
    In-place calibration on the Nano-connected sensor board.

    Parameters
    ----------
    nano_port : str
        Serial device path, e.g. '/dev/ttyACM1'.
    expected_len : int
        Number of joints you expect to read back.
    """
    with open_sensor(nano_port) as sensor:
        print("Current position data:")
        print(try_read(sensor, expected_len=expected_len))

        input("Move the device to a neutral position, "
              "then press Enter to calibrate...")

        sensor.calibrate_sensors()

        if hasattr(sensor, "serial"):
            sensor.serial.reset_input_buffer()
        time.sleep(0.5)

        print("Position data after calibration:")
        print(try_read(sensor, expected_len=expected_len))
