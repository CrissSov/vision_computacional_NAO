import cv2
import numpy as np
from collections import namedtuple
import mediapipe as mp

mp_hands = mp.solutions.hands

# Estructuras para simular salida de MediaPipe Hands en Holistic
Classification = namedtuple('Classification', ['label', 'score', 'index'])
Handedness = namedtuple('Handedness', ['classification'])

class ResultsWrapper:
    def __init__(self):
        self.multi_hand_landmarks = None
        self.multi_handedness = None

def create_multi_hand_structures(holistic_results):
    multi_hand_landmarks = []
    multi_handedness = []

    if holistic_results.left_hand_landmarks:
        multi_hand_landmarks.append(holistic_results.left_hand_landmarks)
        multi_handedness.append(Handedness([Classification('Left', 1.0, 0)]))
    if holistic_results.right_hand_landmarks:
        multi_hand_landmarks.append(holistic_results.right_hand_landmarks)
        multi_handedness.append(Handedness([Classification('Right', 1.0, 1)]))

    return multi_hand_landmarks, multi_handedness

# Lista de joints para ángulos (dedos)
joint_list = [[8,5,0], [12,9,0], [16,13,0], [20,17,0]]

def get_angles(image, hand, joint_combinations):
    angle_list = []
    for joint in joint_combinations:
        a = np.array([hand.landmark[joint[0]].x, hand.landmark[joint[0]].y])
        b = np.array([hand.landmark[joint[1]].x, hand.landmark[joint[1]].y])
        c = np.array([hand.landmark[joint[2]].x, hand.landmark[joint[2]].y])

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360 - angle
        angle_list.append(angle)
    return angle_list

def get_hand_status(image, results, show_text=True):
    output = {
        "Left": {"is_open": False},
        "Right": {"is_open": False}
    }

    original_image = image
    image = cv2.flip(image, 1)

    if results.multi_hand_landmarks is not None:
        number_of_hands = len(results.multi_hand_landmarks)
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            if handedness.classification[0].label == "Left":
                angles = get_angles(image, hand_landmarks, joint_list)
                output["Left"]["is_open"] = 1 if all(i > 80 for i in angles) else 0
                if number_of_hands != 2:
                    output["Right"]["is_open"] = None

            if handedness.classification[0].label == "Right":
                angles = get_angles(image, hand_landmarks, joint_list)
                output["Right"]["is_open"] = 1 if all(i > 80 for i in angles) else 0
                if number_of_hands != 2:
                    output["Left"]["is_open"] = None
    else:
        output["Left"]["is_open"] = None
        output["Right"]["is_open"] = None

    if show_text:
        # Mostrar estado manos en la imagen
        texts = {
            True: "open",
            False: "closed",
            None: "No Hand"
        }

        left_text = texts.get(output["Left"]["is_open"], "Unknown")
        right_text = texts.get(output["Right"]["is_open"], "Unknown")

        cv2.putText(original_image, f"Left Hand: {left_text}", (original_image.shape[1] - 220, original_image.shape[0] // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.putText(original_image, f"Right Hand: {right_text}", (20, original_image.shape[0] // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    return output
