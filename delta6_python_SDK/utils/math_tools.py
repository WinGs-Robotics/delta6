import numpy as np
from scipy.spatial.transform import Rotation as R


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


def trans_matrix_to_position(T_AB):
    """
    Converts a 4x4 homogeneous transformation matrix back into
    position [x, y, z] and Euler angles [roll, pitch, yaw] (in radians).

    :param T_AB: 4x4 numpy array
    :return: [x, y, z, roll, pitch, yaw]
    """
    if T_AB.shape != (4, 4):
        raise ValueError("Input matrix must be 4x4.")

    # Extract translation
    x, y, z = T_AB[0:3, 3]

    # Extract rotation part and convert to Euler angles
    R_mat = T_AB[0:3, 0:3]
    rot = R.from_matrix(R_mat)
    roll, pitch, yaw = rot.as_euler('XYZ', degrees=False)

    return np.array([x, y, z, roll, pitch, yaw])


def parent_to_child(parent_cartesian_position, delta_position):
    """
    Given a parent frame pose and a relative delta pose, compute
    the resulting child frame pose.

    :param parent_cartesian_position: [x, y, z, roll, pitch, yaw] of the parent frame
    :param delta_position: [x, y, z, roll, pitch, yaw] relative transform from the parent frame
    :return: [x, y, z, roll, pitch, yaw] of the child frame
    """
    # 1. Convert input vectors to 4x4 transforms
    ParentPositionMatrix = position_to_trans_matrix(parent_cartesian_position)
    DeltaPositionMatrix = position_to_trans_matrix(delta_position)

    # 2. Multiply to get the child's transform matrix
    ChildPositionMatrix = np.dot(ParentPositionMatrix, DeltaPositionMatrix)

    # 3. Convert back to [x, y, z, roll, pitch, yaw]
    ChildPosition = trans_matrix_to_position(ChildPositionMatrix)

    return ChildPosition


def child_to_parent(child_cartesian_position, delta_position):
    """
    Computes the parent's pose in the world frame, given:
      - child's pose in the world frame (child_cartesian_position)
      - the transform from the parent to the child (delta_position).

    Go counterpart for reference:
        ChildPositionMatrix := PositionToTransMatrix(childCartesianPosition)
        DeltaPositionMatrix := PositionToTransMatrix(deltaPosition)

        invDeltaPositionMatrix := Inverse(DeltaPositionMatrix)
        ParentPositionMatrix := ChildPositionMatrix * invDeltaPositionMatrix
        ParentPosition := MatrixToPosition(ParentPositionMatrix)
    """
    # 1. Convert to 4x4 homogeneous transformation matrices
    child_position_matrix = position_to_trans_matrix(child_cartesian_position)
    delta_position_matrix = position_to_trans_matrix(delta_position)

    # 2. Invert the delta_position_matrix
    inv_delta_position_matrix = np.linalg.inv(delta_position_matrix)

    # 3. Compute the parent's matrix
    parent_position_matrix = np.dot(
        child_position_matrix, inv_delta_position_matrix)

    # 4. Convert back to [x, y, z, roll, pitch, yaw]
    parent_position = trans_matrix_to_position(parent_position_matrix)

    return parent_position


def calculate_delta_position(parent_cartesian_position, child_cartesian_position):
    """
    Computes the transform from the parent frame to the child frame (delta_position),
    given:
      - parent's pose in the world frame (parent_cartesian_position)
      - child's pose in the world frame (child_cartesian_position).

    Go counterpart for reference:
        parentPositionMatrix := PositionToTransMatrix(parentCartesianPosition)
        childPositionMatrix := PositionToTransMatrix(childCartesianPosition)

        invParentPositionMatrix := Inverse(parentPositionMatrix)
        deltaPositionMatrix := invParentPositionMatrix * childPositionMatrix
        deltaPosition := MatrixToPosition(deltaPositionMatrix)
    """
    # 1. Convert to 4x4 homogeneous transformation matrices
    parent_position_matrix = position_to_trans_matrix(
        parent_cartesian_position)
    child_position_matrix = position_to_trans_matrix(child_cartesian_position)

    # 2. Invert the parent_position_matrix
    inv_parent_position_matrix = np.linalg.inv(parent_position_matrix)

    # 3. Compute the matrix that transforms from parent to child
    delta_position_matrix = np.dot(
        inv_parent_position_matrix, child_position_matrix)

    # 4. Convert back to [x, y, z, roll, pitch, yaw]
    delta_position = trans_matrix_to_position(delta_position_matrix)

    return delta_position


def compute_force_at_B(measured_force_moment_A, transform):
    """
    Given a wrench measured at point A (in A-coords), find the equivalent wrench
    at point B (expressed in B-coords).

    :param measured_force_moment_A: [Fx_A, Fy_A, Fz_A, Mx_A, My_A, Mz_A],
                                    measured about point A, in A's coordinate system.
    :param transform: [x, y, z, roll, pitch, yaw],
                      describing the transformation from A to B.
                      That is, T_AB transforms vectors from A-coords to B-coords,
                      and [x,y,z] is the position of B in A-coords.
    :return: [Fx_B, Fy_B, Fz_B, Mx_B, My_B, Mz_B],
             i.e. the force & torque about B, in B-coords.
    """
    # Build the homogeneous transformation from A to B
    T_AB = position_to_trans_matrix(transform)

    # Extract rotation and translation
    R_AB = T_AB[0:3, 0:3]   # from A-coords -> B-coords
    r_AB = T_AB[0:3, 3]     # position of B w.r.t. A, in A-coords

    # Convert input to numpy arrays
    measured_force_moment_A = np.asarray(
        measured_force_moment_A, dtype=float).reshape(6,)
    F_A = measured_force_moment_A[0:3]  # Force at A (A-coords)
    M_A = measured_force_moment_A[3:6]  # Torque about A (A-coords)

    # 1) Force in B-coords
    F_B = R_AB @ F_A

    # 2) Torque about B, in B-coords
    #    M_B = R_AB [ M_A - ( r_AB x F_A ) ]
    M_B = R_AB @ (M_A - np.cross(r_AB, F_A))

    # Combine
    force_moment_B = np.concatenate([F_B, M_B])
    return force_moment_B.tolist()


def quantize_to_resolution(value, resolution):

    sign = 1 if value >= 0 else -1

    x = abs(value)

    multiple = int(x // resolution)
    base = multiple * resolution
    remainder = x - base

    if remainder >= 0.5:
        quantized = base + resolution
    else:
        quantized = base

    return sign * quantized


def unwrap_angle(angle_now, angle_prev):

    delta = angle_now - (angle_prev % (2*np.pi))
    while delta < -np.pi:
        delta += 2*np.pi
    while delta > np.pi:
        delta -= 2*np.pi

    return angle_prev + delta


def unwrap_rpy(new, old):

    new = np.array(new)
    old = np.array(old)
    result = new.copy()
    for i in [3, 4, 5]:  # roll, pitch, yaw
        delta = new[i] - old[i]
        if delta > np.pi:
            result[i] -= 2 * np.pi
        elif delta < -np.pi:
            result[i] += 2 * np.pi
    return result


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


if __name__ == "__main__":

    wrenchA = [0, 0, 0, 0.0, 0.0, 0.2669428476]
    transform_BA = [0, 0, 0, np.pi, 0.0, np.pi/2]

    wrenchA_B = represent_wrench_to_B(wrenchA, transform_BA)
    print("Force & Moment at B (in B-frame):", wrenchA_B)
