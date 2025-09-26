# -*- coding: utf-8 -*-
from naoqi import ALProxy

ROBOT_IP = "192.168.137.218"
PORT = 9559

try:
    tts = ALProxy("ALTextToSpeech", ROBOT_IP, PORT)
    tts.say("Hola, todo correcto")
    print("Conexión exitosa")
except Exception as e:
    print("Error de conexión:", e)
