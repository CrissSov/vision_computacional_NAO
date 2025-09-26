import numpy as np
import mediapipe as mp
from head_angles import get_head_positions

class JointPoint:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

class JointType:
    # MediaPipe Pose Landmarks 
    nose = 0 
    left_eye_inner = 1 
    left_eye = 2 
    left_eye_outer = 3 
    right_eye_inner = 4
    right_eye = 5
    right_eye_outer = 6
    left_ear = 7
    right_ear = 8 
    mouth_left = 9 
    mouth_right = 10 
    LeftShoulder = 11
    RightShoulder = 12
    LeftElbow = 13
    RightElbow = 14
    LeftWrist = 15
    RightWrist = 16
    LeftHip = 23 
    RightHip = 24
    LeftKnee = 25
    RightKnee = 26
    LeftAnkle = 27
    RightAnkle = 28
    LeftFootIndex = 31
    RightFootIndex = 32
    SpineBase = 23  # Aproximamos con LeftHip
    SpineMid = 0    # Se calcula como promedio
    SpineShoulder = 100  # Se calcula como promedio

class HolisticData:
    def __init__(self, holistic_result, face_mesh_results=None, image=None):
        self.bodyJointsArray = {}
        #self.handState = {"LEFT_HAND": False, "RIGHT_HAND": False}
        self.headRotationAngle = {
            "Pitch": {"Degree": None, "Radian": None},
            "Yaw": {"Degree": None, "Radian": None}
        }

        pose = holistic_result.pose_landmarks
        if pose:
            self._load_pose_data(pose)
            self._estimate_spine_points()

        #self.handState["LEFT_HAND"] = self._is_hand_open(holistic_result.left_hand_landmarks)
        #self.handState["RIGHT_HAND"] = self._is_hand_open(holistic_result.right_hand_landmarks)

        # Si tenemos FaceMesh y la imagen, calcular rotación de cabeza
        if face_mesh_results is not None and image is not None:
            self.headRotationAngle = get_head_positions(image, face_mesh_results, angle_type="Degree", show_text=False)
        else:
            self.headRotationAngle = {
                "Pitch": {"Degree": None, "Radian": None},
                "Yaw": {"Degree": None, "Radian": None}
            }


    def _load_pose_data(self, pose_landmarks):
        for idx, lm in enumerate(pose_landmarks.landmark):
            self.bodyJointsArray[idx] = JointPoint(lm.x, lm.y, lm.z)

    def _estimate_spine_points(self):
        # Promedio de hombros para SpineShoulder
        ls = self.bodyJointsArray.get(JointType.LeftShoulder)
        rs = self.bodyJointsArray.get(JointType.RightShoulder)
        if ls and rs:
            self.bodyJointsArray[JointType.SpineShoulder] = self._average_points([ls, rs])
        
        # Promedio de caderas para SpineMid
        lh = self.bodyJointsArray.get(JointType.LeftHip)
        rh = self.bodyJointsArray.get(JointType.RightHip)
        if lh and rh:
            self.bodyJointsArray[JointType.SpineMid] = self._average_points([lh, rh])

    def _average_points(self, points):
        x = sum(p.x for p in points) / len(points)
        y = sum(p.y for p in points) / len(points)
        z = sum(p.z for p in points) / len(points)
        return JointPoint(x, y, z)

    """def _is_hand_open(self, hand_landmarks):
        if not hand_landmarks:
            return False
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]
        dist = np.linalg.norm(
            np.array([thumb_tip.x, thumb_tip.y]) - 
            np.array([index_tip.x, index_tip.y])
        )
        return dist > 0.05
"""