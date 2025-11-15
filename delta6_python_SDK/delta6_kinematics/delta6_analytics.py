"""
Using the method from code:
https://github.com/mhp/delta-bot/blob/main/kinematics.py
"""

import math
from scipy.optimize import fsolve
import numpy as np
import scipy.spatial.transform as tfm
from scipy.spatial.transform import Rotation as R

# Class representing a Delta Robot


class DeltaRobot:
    def __init__(self, short_arm_length=40.0, parallel_arm_length=120.0, base_radius=72.0, end_effector_radius=21.24, theta_offset=math.pi / 6, spring_coef=0.639236, version="original"):
        """
        Initialize the Delta Robot with given dimensions.

        Parameters:
        short_arm_length (float): Length of the short arms (rf)
        parallel_arm_length (float): Length of the parallel arms (re)
        base_radius (float): Radius of the base (f)
        end_effector_radius (float): Radius of the end effector (e)
        """
        # in mm
        self.e = end_effector_radius
        self.f = base_radius
        self.re = parallel_arm_length
        self.rf = short_arm_length

        self.z_offset_upper = 33  # mm
        self.z_offset_lower = 30  # mm
        self.z_offset = self.z_offset_upper + self.z_offset_lower  # mm

        self.theta_offset = theta_offset  # radian

        self.version = version

        self.theta1 = 0
        self.theta2 = 0
        self.theta3 = 0
        self.theta4 = 0
        self.theta5 = 0
        self.theta6 = 0

        self.torque1 = 0
        self.torque2 = 0
        self.torque3 = 0
        self.torque4 = 0
        self.torque5 = 0
        self.torque6 = 0

        self.spring_coef = spring_coef

    def update(self, theta1, theta2, theta3, theta4, theta5, theta6):
        self.update_angles(theta1, theta2, theta3, theta4, theta5, theta6)
        self.update_torques(theta1, theta2, theta3, theta4, theta5, theta6)

    def update_angles(self, theta1, theta2, theta3, theta4, theta5, theta6):
        self.theta1 = theta1
        self.theta2 = theta2
        self.theta3 = theta3
        self.theta4 = theta4
        self.theta5 = theta5
        self.theta6 = theta6

    def update_torques(self, theta1, theta2, theta3, theta4, theta5, theta6):
        self.torque1 = theta1 * self.spring_coef
        self.torque2 = theta2 * self.spring_coef
        self.torque3 = theta3 * self.spring_coef
        self.torque6 = theta6 * self.spring_coef
        if self.version == "double-springs-roll-pitch":
            self.torque4 = 2 * theta4 * self.spring_coef
            self.torque5 = 2 * theta5 * self.spring_coef
        else:
            self.torque4 = theta4 * self.spring_coef
            self.torque5 = theta5 * self.spring_coef

    def get_end_force(self):
        return self.calculate_end_force(self.torque1, self.torque2, self.torque3, self.torque4, self.torque5, self.torque6)

    def calculate_end_force(self, torque1, torque2, torque3, torque4, torque5, torque6):
        Fx, Fy, Fz = self.calculate_force_xyz(
            torque1, torque2, torque3)
        Mx, My, Mz = torque4, torque5, torque6

        pose_trans = self.get_FK_result()
        rotate_trans = [0, 0, 0, pose_trans[3], pose_trans[4], pose_trans[5]]
        transfered_wrench = represent_wrench_to_B(
            [Fx, Fy, Fz, Mx, My, Mz], rotate_trans)
        # transfered_wrench = compute_force_at_B([Fx, Fy, Fz, Mx, My, Mz], rotate_trans)
        # transfered_wrench = [Fx, Fy, Fz, 0, 0, 0]
        return transfered_wrench[0], transfered_wrench[1], transfered_wrench[2], transfered_wrench[3], transfered_wrench[4], transfered_wrench[5]

    def get_FK_result(self):
        return self.forward_kinematics(self.theta1, self.theta2, self.theta3, self.theta4, self.theta5, self.theta6)

    def forward_kinematics(self, theta1, theta2, theta3, theta4, theta5, theta6):
        """
        Calculate the (x, y, z) position of the end effector given the short angles.

        Parameters:
        theta1, theta2, theta3 (float): Angles of the shorts in radians.

        Returns:
        tuple: (x, y, z) coordinates of the end effector if valid, None otherwise.
        """

        theta1 = theta1 + self.theta_offset
        theta2 = theta2 + self.theta_offset
        theta3 = theta3 + self.theta_offset

        t = self.f - self.e

        # Calculate position of leg 1's joint (x1 is implicitly zero - along the axis)
        y1 = -(t + self.rf * math.cos(theta1))
        z1 = -self.rf * math.sin(theta1)

        # Calculate position of leg 2's joint
        y2 = (t + self.rf * math.cos(theta2)) * math.sin(math.pi / 6)
        x2 = y2 * math.tan(math.pi / 3)
        z2 = -self.rf * math.sin(theta2)

        # Calculate position of leg 3's joint
        y3 = (t + self.rf * math.cos(theta3)) * math.sin(math.pi / 6)
        x3 = -y3 * math.tan(math.pi / 3)
        z3 = -self.rf * math.sin(theta3)

        # Calculate the determinant of the matrix formed by the three positions
        dnm = (y2 - y1) * x3 - (y3 - y1) * x2

        # Intermediate calculations for determining the position of the end effector
        w1 = y1 ** 2 + z1 ** 2
        w2 = x2 ** 2 + y2 ** 2 + z2 ** 2
        w3 = x3 ** 2 + y3 ** 2 + z3 ** 2

        a1 = (z2 - z1) * (y3 - y1) - (z3 - z1) * (y2 - y1)
        b1 = -((w2 - w1) * (y3 - y1) - (w3 - w1) * (y2 - y1)) / 2.0

        a2 = -(z2 - z1) * x3 + (z3 - z1) * x2
        b2 = ((w2 - w1) * x3 - (w3 - w1) * x2) / 2.0

        # Coefficients for the quadratic equation az^2 + bz + c = 0
        a = a1 ** 2 + a2 ** 2 + dnm ** 2
        b = 2 * (a1 * b1 + a2 * (b2 - y1 * dnm) - z1 * dnm ** 2)
        c = (b2 - y1 * dnm) ** 2 + b1 ** 2 + \
            dnm ** 2 * (z1 ** 2 - self.re ** 2)

        # Calculate discriminant
        discriminant = b ** 2 - 4.0 * a * c
        if discriminant < 0:
            return None  # No valid solution

        # Calculate z0, x0, and y0 (coordinates of the end effector)
        z0 = (-0.5 * (b + math.sqrt(discriminant)) / a)
        x0 = (a1 * z0 + b1) / dnm
        y0 = (a2 * z0 + b2) / dnm

        # shift to defination
        x = -y0 / 1000.0
        y = x0 / 1000.0
        z = -(z0 - self.z_offset) / 1000.0

        # Convert extrinsic rotation angles to intrinsic roll, pitch, yaw
        ZXY = [theta6, theta4, theta5]
        r = tfm.Rotation.from_euler('ZXY', ZXY, degrees=False)
        roll, pitch, yaw = map(float, r.as_euler('XYZ', degrees=False))
        # roll, pitch, yaw = theta4, theta5, theta6
        return x, y, z, roll, pitch, yaw

    def _calculate_angle_yz(self, x0, y0, z0):
        """
        Helper function to calculate the angle for a given (x, y, z) position.

        Parameters:
        x0, y0, z0 (float): Coordinates of the end effector.

        Returns:
        float: Angle in radians if valid, None otherwise.
        """
        y1 = -self.f
        y0 -= self.e

        a = (x0 ** 2 + y0 ** 2 + z0 ** 2 + self.rf **
             2 - self.re ** 2 - y1 ** 2) / (2 * z0)
        b = (y1 - y0) / z0
        discriminant = -(a + b * y1) ** 2 + self.rf * \
            (b ** 2 * self.rf + self.rf)

        if discriminant < 0:
            return None

        yj = (y1 - a * b - math.sqrt(discriminant)) / (b ** 2 + 1)
        zj = a + b * yj

        # Calculate theta in radians
        theta = math.atan(-zj / (y1 - yj))
        if yj > y1:
            theta += math.pi

        return theta

    def inverse_kinematics(self, x, y, z, roll, pitch, yaw):
        """
        Calculate the short angles for a given (x, y, z) position of the end effector in m.

        Parameters:
        x0, y0, z0 (float): Coordinates of the end effector.

        Returns:
        tuple: Angles (theta1, theta2, theta3) in radians if valid, None otherwise.
        """
        cos120 = math.cos(2.0 * math.pi / 3.0)
        sin120 = math.sin(2.0 * math.pi / 3.0)

        x0 = y * 1000.0
        y0 = -x * 1000.0
        z0 = -z * 1000 + self.z_offset

        # Calculate the three short angles
        theta1 = self._calculate_angle_yz(x0, y0, z0)
        if theta1 is None:
            return None

        theta2 = self._calculate_angle_yz(
            x0 * cos120 + y0 * sin120, y0 * cos120 - x0 * sin120, z0)  # Rotate +120 degrees
        if theta2 is None:
            return None

        theta3 = self._calculate_angle_yz(
            x0 * cos120 - y0 * sin120, y0 * cos120 + x0 * sin120, z0)  # Rotate -120 degrees
        if theta3 is None:
            return None

        theta1 -= self.theta_offset
        theta2 -= self.theta_offset
        theta3 -= self.theta_offset

        # Convert intrinsic roll, pitch, yaw to ZXY rotation angles
        XYZ = [roll, pitch, yaw]
        r = tfm.Rotation.from_euler('XYZ', XYZ, degrees=False)
        theta6, theta4, theta5 = map(float, r.as_euler('ZXY', degrees=False))
        # theta4, theta5, theta6 = roll, pitch, yaw
        return theta1, theta2, theta3, theta4, theta5, theta6

    def calculate_force_xyz(self, torque1, torque2, torque3):

        theta1 = torque1/self.spring_coef + self.theta_offset
        theta2 = torque2/self.spring_coef + self.theta_offset
        theta3 = torque3/self.spring_coef + self.theta_offset

        a = self.f/1000  # mm to m
        b = self.e/1000
        la = self.rf/1000
        lb = self.re/1000

        cos120 = -0.5
        sin120 = math.sqrt(3)/2

        cos240 = -0.5
        sin240 = -math.sqrt(3)/2

        sin_theta1 = math.sin(theta1)
        cos_theta1 = math.cos(theta1)
        sin_theta2 = math.sin(theta2)
        cos_theta2 = math.cos(theta2)
        sin_theta3 = math.sin(theta3)
        cos_theta3 = math.cos(theta3)
        # a. find px py pz
        px, py, pz, _, _, _ = self.forward_kinematics(
            torque1/self.spring_coef, torque2/self.spring_coef, torque3/self.spring_coef, 0, 0, 0)

        pz = pz - self.z_offset/1000
        # b.calculate unit vector of AiPi for each branch refer to main
        k = b-a
        m2 = cos120*(b-a)
        n2 = sin120*(b-a)
        m3 = cos240*(b-a)
        n3 = sin240*(b-a)

        A_1P_1 = np.array([px-cos_theta1*la+k, py, pz-la*sin_theta1])
        A_2P_2 = np.array([px-cos120*cos_theta2*la + m2,
                           py-sin120*cos_theta2*la + n2,
                           pz-la*sin_theta2])
        A_3P_3 = np.array([px-cos240*cos_theta3*la + m3,
                           py-sin240*cos_theta3*la + n3,
                           pz-la*sin_theta3])

        A_1P_1_unit = A_1P_1 / lb
        A_2P_2_unit = A_2P_2 / lb
        A_3P_3_unit = A_3P_3 / lb

        # c. find rotation matrix
        rot_neg_120 = tfm.Rotation.from_euler('Z', -120, degrees=True)
        mat_neg_120_3d = rot_neg_120.as_matrix()  # 3x3 matrix

        rot_neg_240 = tfm.Rotation.from_euler('Z', -240, degrees=True)
        mat_neg_240_3d = rot_neg_240.as_matrix()  # 3x3 matrix

        # d.convert unit vector of AiPi from each branch to branch coordinates
        A_1P_1_unit_O1 = A_1P_1_unit
        A_2P_2_unit_O2 = mat_neg_120_3d @ A_2P_2_unit
        A_3P_3_unit_O3 = mat_neg_240_3d @ A_3P_3_unit

        # e. calculate force magnitudes Fa1 Fa2 Fa3

        Fa1_mag = torque1 / \
            (sin_theta1*la*A_1P_1_unit_O1[0] - cos_theta1*la*A_1P_1_unit_O1[2])
        Fa2_mag = torque2 / \
            (sin_theta2*la*A_2P_2_unit_O2[0] - cos_theta2*la*A_2P_2_unit_O2[2])
        Fa3_mag = torque3 / \
            (sin_theta3*la*A_3P_3_unit_O3[0] - cos_theta3*la*A_3P_3_unit_O3[2])

        # f. calculate force on each branch refer to main coordinates
        Fa1 = Fa1_mag * A_1P_1_unit
        Fa2 = Fa2_mag * A_2P_2_unit
        Fa3 = Fa3_mag * A_3P_3_unit

        F = Fa1 + Fa2 + Fa3
        Fx = -F[0]
        Fy = -F[1]
        Fz = -F[2]

        return Fx, Fy, Fz

    def calculate_torques(self, Fx_target, Fy_target, Fz_target, Mx_target, My_target, Mz_target):

        def residuals(torques):
            t1, t2, t3, t4, t5, t6 = torques
            Fx, Fy, Fz, Mx, My, Mz = self.calculate_end_force(
                t1, t2, t3, t4, t5, t6)

            return [
                Fx - Fx_target,
                Fy - Fy_target,
                Fz - Fz_target,
                Mx - Mx_target,
                My - My_target,
                Mz - Mz_target
            ]

        initial_guess = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        solution = fsolve(residuals, initial_guess, xtol=1e-5)
        return solution

    def calculate_euler_pose(self, Fx, Fy, Fz, Mx, My, Mz):
        torque1, torque2, torque3, torque4, torque5, torque6 = self.calculate_torques(
            Fx, Fy, Fz, Mx, My, Mz)

        theta1 = torque1/self.spring_coef
        theta2 = torque2/self.spring_coef
        theta3 = torque3/self.spring_coef

        if self.version == "double-springs-roll-pitch":
            theta4 = torque4/(2*self.spring_coef)
            theta5 = torque5/(2*self.spring_coef)
            theta6 = torque6/(2*self.spring_coef)
        else:
            theta4 = torque4/self.spring_coef
            theta5 = torque5/self.spring_coef
            theta6 = torque6/self.spring_coef

        thetas = np.array([theta1, theta2, theta3, theta4,
                          theta5, theta6], dtype=float)
        thetas = np.round(thetas, 5)

        return self.forward_kinematics(*thetas)


def represent_wrench_to_B(wrench_a, transform_6d):

    T_AB = position_to_trans_matrix(transform_6d)
    R_AB = T_AB[:3, :3]
    t_AB = T_AB[:3, 3]

    f_a = np.array(wrench_a[:3])
    tau_a = np.array(wrench_a[3:])

    cross_term = np.cross(t_AB, tau_a)

    f_b = R_AB.T @ f_a - R_AB.T @ cross_term
    tau_b = R_AB.T @ tau_a

    wrench_b = np.concatenate([f_b, tau_b])
    return wrench_b


def position_to_trans_matrix(transform):
    """
    Converts position [x, y, z] and Euler angles [roll, pitch, yaw] (in radians)
    into a 4x4 homogeneous transformation matrix T_AB.

    Here, 'transform' describes the pose of frame B relative to frame A.
    i.e., T_AB transforms coordinates from A to B.

    :param transform: [x, y, z, roll, pitch, yaw]
    :return: a 4x4 numpy array, T_AB
    """
    if len(transform) != 6:
        raise ValueError(
            "Transform must have 6 elements: [x, y, z, roll, pitch, yaw].")

    x, y, z, roll, pitch, yaw = transform

    # Rotation from Euler angles (in radians, 'XYZ' convention)
    rot = R.from_euler('XYZ', [roll, pitch, yaw], degrees=False)
    R_mat = rot.as_matrix()  # 3x3

    # Build the 4x4 homogeneous transform
    T_AB = np.eye(4)
    T_AB[0:3, 0:3] = R_mat
    T_AB[0:3, 3] = [x, y, z]

    return T_AB


# ---------------------------------------------------------------
# Main – quick round-trip test for FK ⇄ IK
# ---------------------------------------------------------------
if __name__ == "__main__":
    import numpy as np

    def pretty_print_pose(label, pose):
        """Pose: (x, y, z, roll, pitch, yaw)"""
        if pose is None:
            print(f"{label:<14}:  None / IK failed")
            return
        x, y, z, r, p, yaw = pose
        print(f"{label:<14}:  "
              f"x={x: .4f}  y={y: .4f}  z={z: .4f}  "
              f"r={r: .4f}  p={p: .4f}  y={yaw: .4f}")

    def pretty_print_wrench(label, wrench):
        """Wrench: (Fx, Fy, Fz, Tx, Ty, Tz)"""
        Fx, Fy, Fz, Tx, Ty, Tz = wrench
        print(f"{label:<14}:  "
              f"Fx={Fx: .4f}  Fy={Fy: .4f}  Fz={Fz: .4f}  "
              f"Tx={Tx: .4f}  Ty={Ty: .4f}  Tz={Tz: .4f}")

    # 1) Instantiate the robot
    robot = DeltaRobot()

    # 2) Choose a target pose (units: metres, radians)
    x_target, y_target, z_target = 0.005, -0.016, 0.155   # 5 mm, –6 mm, –150 mm
    roll_target = 0.03                                     # rad
    pitch_target = -0.01                                    # rad
    yaw_target = 0.04                                     # rad

    print("Target end-effector pose:")
    print(f"  xyz  = ({x_target:.4f}, {y_target:.4f}, {z_target:.4f})  [m]")
    print(
        f"  rpy  = ({roll_target:.4f}, {pitch_target:.4f}, {yaw_target:.4f})  [rad]")

    # 3) Inverse kinematics
    joint_angles = robot.inverse_kinematics(
        x_target, y_target, z_target, roll_target, pitch_target, yaw_target
    )
    if joint_angles is None:
        print("\n❌  Inverse kinematics failed - pose out of workspace.")
        raise SystemExit(1)

    # 4) Update robot state and run forward kinematics
    robot.update(*joint_angles)
    fk_pose = robot.get_FK_result()          # (x, y, z, roll, pitch, yaw)
    end_force = robot.get_end_force()

    # 5) Compare results
    fk = np.array(fk_pose)
    tgt = np.array([x_target, y_target, z_target,
                   roll_target, pitch_target, yaw_target])
    diff = fk - tgt

    print("\nJoint angles (rad):")
    print("  " + ", ".join(f"{a:.6f}" for a in joint_angles))

    print("\nPose returned by forward kinematics:")
    print(
        f"  xyz  = ({fk_pose[0]:.4f}, {fk_pose[1]:.4f}, {fk_pose[2]:.4f})  [m]")
    print(
        f"  rpy  = ({fk_pose[3]:.4f}, {fk_pose[4]:.4f}, {fk_pose[5]:.4f})  [rad]")

    print("\nResidual error  (FK – target):")
    print(f"  Δxyz = {diff[:3]}")
    print(f"  Δrpy = {diff[3:]}")

    pretty_print_wrench("\nEnd-effector force", end_force)

    # ---------------------------------------------------------------
    trans1 = [0, 0, 0.15, 0.3, 0,   0]
    trans2 = [0, 0, 0.15, 0.3, 0.2,   0]

    print("\n===== Pose 1 =================================================")
    enc1 = robot.inverse_kinematics(*trans1)
    print("Inverse kinematics  :", enc1)
    if enc1:
        robot.update(*enc1)
        pretty_print_pose("Forward kinematics", robot.get_FK_result())
        pretty_print_wrench("End-effector force", robot.get_end_force())

    print("\n===== Pose 2 =================================================")
    enc2 = robot.inverse_kinematics(*trans2)
    print("Inverse kinematics  :", enc2)
    if enc2:
        robot.update(*enc2)
        pretty_print_pose("Forward kinematics", robot.get_FK_result())
        pretty_print_wrench("End-effector force", robot.get_end_force())
