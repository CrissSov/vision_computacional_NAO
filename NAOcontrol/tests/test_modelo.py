from naoqi import ALProxy
import math
import time

NAO_IP = "localhost"  # Cambia por IP correcta
NAO_PORT = 57056

motion = ALProxy("ALMotion", NAO_IP, NAO_PORT)
posture = ALProxy("ALRobotPosture", NAO_IP, NAO_PORT)

# Activar rigidez para brazos
motion.setStiffnesses(["LShoulderRoll", "RShoulderRoll", "LShoulderPitch", "RShoulderPitch", "LElbowRoll", "RElbowRoll"], 1.0)

# Postura Stand para movilidad
posture.goToPosture("Stand", 0.5)

names = ["LShoulderRoll", "RShoulderRoll", "LShoulderPitch", "RShoulderPitch", "LElbowRoll", "RElbowRoll"]
angles = [
    math.radians(50),    # LShoulderRoll abierto
    math.radians(-50),   # RShoulderRoll abierto
    0.0,                 # LShoulderPitch neutro
    0.0,                 # RShoulderPitch neutro
    math.radians(-2),                # LElbowRoll neutro
    math.radians(2),                   # RElbowRoll neutro
]
times = [1.0] * len(names)

motion.angleInterpolation(names, angles, times, True)

time.sleep(3)

motion.setStiffnesses("Body", 0.0)
