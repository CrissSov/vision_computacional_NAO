#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
nao_control.py

Controla al robot NAO recibiendo ángulos por socket y ejecutando movimientos.
Usa setAngles con velocidad limitada para evitar exceder la velocidad máxima.
Guarda en CSV los ángulos recibidos.
"""

import sys
import socket
import json
import time
import csv
from datetime import datetime
from naoqi import ALProxy

# ======================
# Configuración del robot
# ======================
NAO_IP = "192.168.137.115"   # cámbialo a la IP de tu robot
NAO_PORT = 9559
SOCKET_PORT = 6000
SPEED = 0.2  # 20% de la velocidad máxima

# ======================
# Logger CSV
# ======================
class CSVLogger:
    def __init__(self, filename_prefix="nao_angles"):
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = "{}_{}.csv".format(filename_prefix, now_str)
        self.file = open(self.filename, mode="wb")
        self.writer = csv.writer(self.file)

        self.joints = [
            "HeadYaw", "HeadPitch",
            "LShoulderPitch", "LShoulderRoll",
            "RShoulderPitch", "RShoulderRoll",
            "LElbowRoll", "RElbowRoll",
            "LHand", "RHand"
        ]
        self.writer.writerow(["timestamp"] + self.joints)

    def log(self, angles):
        ts = time.time()
        row = [ts] + [angles.get(j, None) for j in self.joints]
        self.writer.writerow(row)

    def close(self):
        self.file.close()

# ======================
# Conexión al NAO
# ======================
try:
    motionProxy = ALProxy("ALMotion", NAO_IP, NAO_PORT)
    postureProxy = ALProxy("ALRobotPosture", NAO_IP, NAO_PORT)
except Exception as e:
    print("Error al conectar con NAO:", e)
    sys.exit(1)

motionProxy.setStiffnesses("Body", 1.0)
postureProxy.goToPosture("StandInit", 0.5)

# ======================
# Socket servidor
# ======================
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("0.0.0.0", SOCKET_PORT))
server_socket.listen(1)
print("Esperando conexión en el puerto", SOCKET_PORT)

conn, addr = server_socket.accept()
print("Conectado con:", addr)

logger = CSVLogger()

try:
    while True:
        data = conn.recv(4096)
        if not data:
            break

        try:
            angles = json.loads(data)
        except Exception as e:
            print("Error al decodificar JSON:", e)
            continue

        # Ejecutar movimiento en NAO con límite de velocidad
        for joint, angle in angles.items():
            try:
                motionProxy.setAngles(joint, angle * 3.14159 / 180.0, SPEED)  # a radianes
            except Exception as e:
                print("Error moviendo", joint, ":", e)

        # Guardar en CSV
        logger.log(angles)

except KeyboardInterrupt:
    print("Interrumpido por el usuario")

finally:
    logger.close()
    conn.close()
    server_socket.close()
    motionProxy.setStiffnesses("Body", 0.0)
    print("Conexión cerrada y rigidez desactivada.")
