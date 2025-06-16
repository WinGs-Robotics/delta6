"""
Using the method from code:
https://github.com/mhp/delta-bot/blob/main/kinematics.py
"""

import math
from scipy.optimize import fsolve
import numpy as np
import scipy.spatial.transform as tfm

# Class representing a Delta Robot


class DeltaRobot:
    def __init__(self, short_arm_length=40.0, parallel_arm_length=120.0, base_radius=72.0, end_effector_radius=21.24):
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
        self.z_offset = self.z_offset_upper + self.z_offset_lower # mm

        self.theta_offset = math.pi / 6  # radian

        self.theta = [0.0] * 6  # theta1 ~ theta6
        self.torque = [0.0] * 6  # torque1 ~ torque6

        
        self.spring_coef = 0.723540

    def update(self, theta1, theta2, theta3, theta4, theta5, theta6):
        self.update_angles(theta1, theta2, theta3, theta4, theta5, theta6)
        self.update_torques(theta1, theta2, theta3, theta4, theta5, theta6)

    def update_angles(self, *thetas):
        """
        Update the joint angles.

        Parameters:
        thetas (float): A sequence of 6 angle values for theta1 to theta6.
        """
        if len(thetas) != 6:
            raise ValueError("Exactly 6 angles must be provided.")
        self.theta = list(thetas)

    def update_torques(self, *thetas):
        """
        Update the torques based on input angles and spring coefficient.

        Parameters:
        thetas (float): A sequence of 6 angle values for theta1 to theta6.
        """
        if len(thetas) != 6:
            raise ValueError("Exactly 6 angles must be provided.")
        self.torque = [theta * self.spring_coef for theta in thetas]

    def get_end_force(self):
        return self.calculate_end_force(*self.torque)

    def get_FK_result(self):
        return self.forward_kinematics(*self.theta)


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
        extrinsics = [theta4, theta5, theta6]
        r = tfm.Rotation.from_euler('xyz', extrinsics, degrees=False)
        roll, pitch, yaw = map(float, r.as_euler('XYZ', degrees=False))

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

        x0 = -y * 1000.0
        y0 = x * 1000.0
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

        # Convert intrinsic roll, pitch, yaw to extrinsic XYZ rotation angles
        intrinsics = [roll, pitch, yaw]
        r = tfm.Rotation.from_euler('XYZ', intrinsics, degrees=False)
        theta4, theta5, theta6 = map(float, r.as_euler('xyz', degrees=False))

        return theta1, theta2, theta3, theta4, theta5, theta6

    def calculate_end_force(self, torque1, torque2, torque3, torque4, torque5, torque6):
        Fx, Fy, Fz = self.calculate_force_xyz(
            torque1, torque2, torque3)
        Mx, My, Mz = torque4, torque5, torque6
        return Fx, Fy, Fz, Mx, My, Mz

    def calculate_force_xyz(self, torque1, torque2, torque3):
        
        theta1 = torque1/self.spring_coef + self.theta_offset
        theta2 = torque2/self.spring_coef + self.theta_offset
        theta3 = torque3/self.spring_coef + self.theta_offset

        a = self.f/1000 #mm to m
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
        px, py, pz, _, _, _ = self.forward_kinematics(torque1/self.spring_coef, torque2/self.spring_coef, torque3/self.spring_coef,0,0,0)

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
        A_3P_3_unit_O3 =  mat_neg_240_3d @ A_3P_3_unit

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

    def calculate_torque_123(self, Fx_target, Fy_target, Fz_target):

        def residuals(torques):
            t1, t2, t3 = torques
            Fx, Fy, Fz = self.calculate_force_xyz(t1, t2, t3)
            
            return [
                Fx - Fx_target,
                Fy - Fy_target,
                Fz - Fz_target
            ]
        
        initial_guess = [0.0, 0.0, 0.0]
        
        solution = fsolve(residuals, initial_guess, xtol=1e-5)
        return solution  
    
    def calculate_euler_pose(self,Fx,Fy,Fz,Mx,My,Mz):
        torque1, torque2, torque3 = self.calculate_torque_123(Fx,Fy,Fz)

        theta1 = torque1/self.spring_coef
        theta2 = torque2/self.spring_coef
        theta3 = torque3/self.spring_coef
        theta4 = Mx/self.spring_coef
        theta5 = My/self.spring_coef
        theta6 = Mz/self.spring_coef

        return self.forward_kinematics(theta1,theta2,theta3,theta4,theta5,theta6)


        