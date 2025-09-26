#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
Reproduce los movimientos grabados en CSV en el robot NAO,
respetando los tiempos originales de la grabación.
"""
import csv
import math
import time
from naoqi import ALProxy

NAO_IP = "localhost"  # Cambia a la IP de tu NAO
NAO_PORT = 50443

def reproducir_csv(filename):
    motion = ALProxy("ALMotion", NAO_IP, NAO_PORT)
    motion.setStiffnesses("Body", 1.0)

    with open(filename, "rb") as f:
        reader = csv.DictReader(f)
        prev_ts = None
        for row in reader:
            ts = float(row["timestamp"])
            if prev_ts is not None:
                delay = ts - prev_ts
                if delay > 0:
                    time.sleep(delay)  # espera el mismo tiempo que en la grabación
            prev_ts = ts

            # preparar movimientos
            for joint, val in row.items():
                if joint != "timestamp" and val not in [None, "", " "]:
                    try:
                        angle_rad = float(val) * math.pi / 180.0
                        motion.setAngles(joint, angle_rad, 0.2)  # velocidad = 20%
                    except Exception as e:
                        print("Error procesando {}: {}".format(joint, e))

    motion.setStiffnesses("Body", 0.0)

if __name__ == "__main__":
    reproducir_csv("imitacion_nao.csv")  # archivo CSV generado
