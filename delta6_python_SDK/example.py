import time
import argparse
from kinematics.delta6_analytics import DeltaRobot
from rt_loops.rt_loop import RTLoop
from rt_loops.read_encoder_loop import ReadEncoderLoop
from sensor_interface.sensors_calibration import sensor_calibration
from utils.force_visualizer import ForceVisualizer

class MainLoop(RTLoop):
    def __init__(self, nano_port, freq=100):
        super().__init__(freq=freq)
        self.nano_port = nano_port

    def setup(self):
        ENCODER_DIR = [1, 1, 1, -1, -1, -1]

        # Perform sensor calibration
        sensor_calibration(nano_port=self.nano_port)

        # Initialize the encoder loop
        self.read_encoder_loop = ReadEncoderLoop(nano_port=self.nano_port, encoder_dir=ENCODER_DIR)
        self.read_encoder_loop.loop_spin(frequency=self.freq)
        self.Delta6 = DeltaRobot()

        time.sleep(1)
        print("Setup completed.")

        # Initialize force visualization
        self.force_visualizer = ForceVisualizer(
            title="EE Wrench Visualizer",
            width=800,
            height=600,
            freq=30,
            num_sets=1,
            set_names=['Delta6 Wrench']
        )
        self.force_visualizer.start()

        super().setup()
        print("MainLoop setup done.")

    def loop(self):
        encoder_reading = self.read_encoder_loop.get_encoder_reading()
        self.Delta6.update(*encoder_reading)

        delta6_pose_reading = self.Delta6.get_FK_result()
        print(f"End-effector pose (x, y, z, roll, pitch, yaw): {delta6_pose_reading}")

        delta6_end_force = self.Delta6.get_end_force()
        self.force_visualizer.update_forces([delta6_end_force])

    def shutdown(self):
        super().shutdown()
        self.force_visualizer.stop()
        print("Force visualizer shutdown.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Delta6 main loop with specified Nano port.")
    parser.add_argument("--port", type=str, required=True, help="Serial port name (e.g., COM6 or /dev/ttyACM0)")
    parser.add_argument("--freq", type=int, default=50, help="Loop frequency (default 50 Hz)")
    args = parser.parse_args()

    rt_loop = MainLoop(nano_port=args.port, freq=args.freq)
    rt_loop.setup()
    rt_loop.loop_spin()
