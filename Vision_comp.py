import cv2
import mediapipe as mp
import socket
import json
import time
from holistic_data import HolisticData, JointType
from body_angles import getBodyAngles
from elbows_angles import Elbows
import threading
import queue
import tkinter as tk
import hand_status

angle_queue = queue.Queue()
elbows = Elbows()

# Función para limitar valores
def clamp(val, min_val, max_val):
    return max(min(val, max_val), min_val)

def clamp_angles_for_nao(angles):
    clamped = {}
    for key, value in angles.items():
        if key.endswith("KNEE_PITCH"):
            clamped[key] = clamp(value, 0, 120)
        elif key.endswith("HIP_PITCH"):
            clamped[key] = clamp(value, -45, 30)
        elif key == "LElbowRoll":
            clamped[key] = clamp(value, -88.5, -2)
        elif key == "RElbowRoll":
            clamped[key] = clamp(value, 2, 88.5)
        elif key.endswith("SHOULDER_PITCH"):
            clamped[key] = clamp(value, -90, 90)
        elif key.endswith("SHOULDER_ROLL"):  # 
            if key.startswith("R"):
                clamped[key] = clamp(value, -18, 76)
            else:
                clamped[key] = clamp(value, -76, 18)
        elif key == "HEAD_PITCH":
            clamped[key] = clamp(value, -40, 30)
        elif key == "HEAD_YAW":
            clamped[key] = clamp(value, -120, 120)
        elif key == "VAREPSILON":
            clamped[key] = clamp(value, -60, 40)
        else:
            clamped[key] = value
    return clamped


# Suavizado exponencial
class AngleSmoother:
    def __init__(self, alpha=0.2):
        self.previous = {}
        self.alpha = alpha

    def smooth(self, angles):
        smoothed = {}
        for key, new_val in angles.items():
            if key in ["LHand", "RHand"]:
                smoothed[key] = float(new_val)
                continue

            if key in self.previous:
                prev_val = self.previous[key]
                smoothed_val = self.alpha * new_val + (1 - self.alpha) * prev_val
            else:
                smoothed_val = new_val
            smoothed[key] = smoothed_val
            self.previous[key] = smoothed_val
        return smoothed

# Validación

def is_body_fully_detected(data):
    joints = data.bodyJointsArray
    required = [
        JointType.LeftShoulder, JointType.LeftElbow, JointType.LeftWrist,
        JointType.RightShoulder, JointType.RightElbow, JointType.RightWrist,
        JointType.LeftHip, JointType.LeftKnee, JointType.LeftAnkle,
        JointType.RightHip, JointType.RightKnee, JointType.RightAnkle,
        JointType.SpineMid, JointType.SpineShoulder, JointType.nose
    ]
    return all(j in joints for j in required)

# Conexión al socket del NAO
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 6000))

mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic
mp_face_mesh = mp.solutions.face_mesh

cap = cv2.VideoCapture(0) #usar 0 para la camara web
smoother = AngleSmoother(alpha=0.2)
start_time = time.time()

with mp_holistic.Holistic(static_image_mode=False, model_complexity=1) as holistic, \
     mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True) as face_mesh:
    
    cv2.namedWindow("NAO Tracker", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("NAO Tracker", 960, 540)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        holistic_results = holistic.process(image_rgb)
        face_mesh_results = face_mesh.process(image_rgb)
        multi_hand_landmarks, multi_handedness = hand_status.create_multi_hand_structures(holistic_results)

        annotated = frame.copy()
        mp_drawing.draw_landmarks(annotated, holistic_results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)
        if holistic_results.left_hand_landmarks:
            mp_drawing.draw_landmarks(annotated, holistic_results.left_hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
        if holistic_results.right_hand_landmarks:
            mp_drawing.draw_landmarks(annotated, holistic_results.right_hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)

        results_wrapper = hand_status.ResultsWrapper()
        results_wrapper.multi_hand_landmarks = multi_hand_landmarks
        results_wrapper.multi_handedness = multi_handedness
        status = hand_status.get_hand_status(frame, results_wrapper, show_text=True)
        lhand_state = status.get("Left", {}).get("is_open")
        rhand_state = status.get("Right", {}).get("is_open")

        if holistic_results.pose_landmarks and face_mesh_results.multi_face_landmarks:
            data = HolisticData(holistic_results, face_mesh_results, frame)

            if is_body_fully_detected(data) and time.time() - start_time > 2:
                angles = getBodyAngles(data.bodyJointsArray)
                if not angles:  # Verifica si es None o dict vacío
                    print("No se pudieron calcular los ángulos del cuerpo.")
                    continue  # Salta este frame y no intenta enviar nada
                elbow_angles = elbows.get_elbow_angles_for_nao(data.bodyJointsArray)
                angles.update(elbow_angles)
                angles = clamp_angles_for_nao(angles)
                #print("ÁNGULOS DE LOS CODOS (GRADOS):")
                #print("  LElbowRoll:", elbow_angles.get("LElbowRoll"))
                #print("  RElbowRoll:", elbow_angles.get("RElbowRoll"))

     
                body_landmarks_list = {idx: [jp.x, jp.y, jp.z] for idx, jp in data.bodyJointsArray.items()}

                angles["HeadPitch"] = -(data.headRotationAngle["Pitch"]["Degree"] if data.headRotationAngle["Pitch"]["Degree"] is not None else 0)
                angles["HeadYaw"] = data.headRotationAngle["Yaw"]["Degree"] if data.headRotationAngle["Pitch"]["Degree"] is not None else 0
                angles["LHand"] = 1.0 if lhand_state == 1 else 0.0
                angles["RHand"] = 1.0 if rhand_state == 1 else 0.0

                angles = smoother.smooth(angles)




                try:
                    payload = json.dumps(angles)
                    #print("Enviando al NAO:", payload)
                    sock.sendall(payload.encode("utf-8"))
                    #print("-->>> Ángulos enviados.")
                except Exception as e:
                    print("Error al enviar ángulos:", e)
            else:
                cv2.putText(annotated, "Cuerpo no detectado", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            cv2.putText(annotated, "No se detecta cuerpo", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("NAO Tracker", cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
sock.close()
