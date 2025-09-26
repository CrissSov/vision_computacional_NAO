import numpy as np
import math
from holistic_data import JointType

# --- Utilidades ---

def calculate_angle_2d(p1, p2, p3, dimension="YZ"):
    if dimension == "YZ":
        a = np.array([p1.y, p1.z])
        b = np.array([p2.y, p2.z])
        c = np.array([p3.y, p3.z])
    elif dimension == "XY":
        a = np.array([p1.x, p1.y])
        b = np.array([p2.x, p2.y])
        c = np.array([p3.x, p3.y])
    else:
        raise ValueError("Dimension must be 'YZ' or 'XY'")
    
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    angle_rad = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    angle_deg = np.degrees(angle_rad)
    return angle_deg

def calculate_roll(p_shoulder, p_elbow):
    """
    Calcula el ángulo de roll (abrir los brazos hacia los lados) en el plano XZ.
    """
    dx = p_elbow.x - p_shoulder.x
    dz = p_elbow.z - p_shoulder.z
    angle_rad = np.arctan2(dx, dz)
    angle_deg = np.degrees(angle_rad)
    return angle_deg

def correct_roll(roll_angle, pitch_angle, point_elbow, point_shoulder):
    """
    Corrige el roll si el brazo se levanta al frente (no al lado).
    """
    if abs(point_elbow.x - point_shoulder.x) < 0.08:
        if pitch_angle > 70:
            return 10
    return roll_angle

def correct_pitch(pitch_angle, point_elbow, point_shoulder):
    """
    Corrige el pitch si el brazo está abierto hacia el costado.
    """
    if abs(point_elbow.x - point_shoulder.x) > 0.15:
        if pitch_angle > 40:
            return 20
    return pitch_angle

def clamp_deg(val, lo, hi):
    return max(lo, min(hi, val))

# --- Cálculo de ángulos principales ---

def get_shoulder_angles(joints):
    angles = {}

    # --- Right Shoulder ---
    E = joints[JointType.RightElbow]
    S = joints[JointType.RightShoulder]
    H = joints[JointType.RightHip]

    pitch_r = calculate_angle_2d(E, S, H, dimension="YZ")
    roll_r = calculate_roll(S, E)

    pitch_r = correct_pitch(pitch_r, E, S)
    roll_r = correct_roll(roll_r, pitch_r, E, S)

    # --- Left Shoulder ---
    E2 = joints[JointType.LeftElbow]
    S2 = joints[JointType.LeftShoulder]
    H2 = joints[JointType.LeftHip]

    pitch_l = calculate_angle_2d(E2, S2, H2, dimension="YZ")
    roll_l = calculate_roll(S2, E2)

    pitch_l = correct_pitch(pitch_l, E2, S2)
    roll_l = correct_roll(roll_l, pitch_l, E2, S2)

    # --- Ajuste para NAO ---
    angles["RShoulderPitch"] = -pitch_r + 90
    angles["LShoulderPitch"] = -pitch_l + 90
    angles["RShoulderRoll"] = roll_r
    angles["LShoulderRoll"] = roll_l


    return angles

# --- Función pública ---

def getBodyAngles(joints):
    return get_shoulder_angles(joints)
