#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
nao_control.py

Script para controlar un robot NAO mediante NAOqi (Python 2.7).
Escucha ángulos corporales enviados en JSON por socket y mueve las articulaciones del robot.
"""
from __future__ import print_function
import sys
import socket
import json
import math
import time
from naoqi import ALProxy

# Mapeo de nombres de ángulos a nombres de articulaciones de NAO
ANGLE_MAP = {
    "LShoulderPitch": "LShoulderPitch",
    "RShoulderPitch": "RShoulderPitch",
    "LShoulderRoll": "LShoulderRoll",   # 
    "RShoulderRoll": "RShoulderRoll",   # 
    #"LElbowRoll": "LElbowRoll",
    #"RElbowRoll": "RElbowRoll",
    "LHipPitch": "LHipPitch",
    "RHipPitch": "RHipPitch",
    "LKneePitch": "LKneePitch",
    "RKneePitch": "RKneePitch",
    "HeadPitch": "HeadPitch",
    "HeadYaw": "HeadYaw",
    "HipYawPitch": "HipYawPitch",
    "LHand": "LHand",
    "RHand": "RHand"
}

# Rango físico (en radianes) de cada articulación NAO
JOINT_LIMITS_RAD = {
    "LShoulderPitch": (-2.0857,  2.0857),
    "RShoulderPitch": (-2.0857,  2.0857),
    "LShoulderRoll":  (-0.3142,  1.3265),
    "RShoulderRoll":  (-1.3265,  0.3142),
    "LElbowRoll":     (-1.5446, -0.0349),
    "RElbowRoll":     ( 0.0349,  1.5446),
    "LHipPitch":      (-0.7854,  0.4363),
    "RHipPitch":      (-0.7854,  0.4363),
    "LKneePitch":     ( 0.0000,  2.1125),
    "RKneePitch":     ( 0.0000,  2.1125),
    "HeadPitch":      (-0.6720,  0.5149),
    "HeadYaw":        (-2.0857,  2.0857),
    "HipYawPitch":    (-1.1453,  0.7408)
}
def clamp(val, lo, hi):
    return max(min(val, hi), lo)


NAO_IP = "192.168.137.115"  # Cambiar a la IP de tu robot NAO
NAO_PORT = 9559     # Puerto NAOqi (por defecto 9559)
SOCK_IP = "127.0.0.1"
SOCK_PORT = 6000       # Puerto para recibir ángulos JSON
BUFFER_SIZE = 4096

def deg2rad(deg):
    return deg * math.pi / 180.0

def main(robot_ip, robot_port, sock_ip, sock_port):
    # Conectar a los proxies de NAO
    try:
        motion = ALProxy("ALMotion", robot_ip, robot_port)
        posture = ALProxy("ALRobotPosture", robot_ip, robot_port)
        tts = ALProxy("ALTextToSpeech", robot_ip, robot_port)
        autonomousLifeProxy = ALProxy("ALAutonomousLife", robot_ip, robot_port)

    except Exception as e:
        print("Error al conectar con NAOqi:", e)
        sys.exit(1)
    autonomousLifeProxy.setState("disabled")
    motion.setStiffnesses("Body", 1.0)
    posture.goToPosture("Stand", 0.5)

    # Configurar socket TCP para escuchar ángulos
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((sock_ip, sock_port))
    s.listen(1)
    print("Esperando conexión en {}:{}...".format(sock_ip, sock_port))
    conn, addr = s.accept()
    print("Conectado desde", addr)
    # Hacer que NAO diga una frase
    tts.say("Estoy listo y preparado, realiza un movimiento con las extremidades")




    last_hand_state = {"LHand": None, "RHand": None}

    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                print("Conexión cerrada por cliente.")
                break
            try:
                angles_dict = json.loads(data)
            except ValueError:
                #print("Datos JSON inválidos recibidos:", data)
                continue

            joint_names = []
            target_angles = []

            # Ejecutar apertura/cierre de manos asincrónicamente (solo si cambió estado)
            for hand_key in ["LHand", "RHand"]:
                if hand_key in angles_dict:
                    current = angles_dict[hand_key] >= 0.5
                    if last_hand_state[hand_key] != current:
                        try:
                            if current:
                                motion.post.openHand(hand_key)
                            else:
                                motion.post.closeHand(hand_key)
                        except Exception as e:
                            print("Error con la mano {}: {}".format(hand_key, e))
                        last_hand_state[hand_key] = current

            # Procesar articulaciones (excluyendo manos)
            for key, joint in ANGLE_MAP.items():
                if key in angles_dict and key not in ["LHand", "RHand"]:
                    deg_val = angles_dict[key]            # llega en grados
                    rad_val = deg2rad(deg_val)  ##MATH.RADIANS????

                    
                    # ⬇️ Ajusta al rango físico
                    lo, hi = JOINT_LIMITS_RAD[joint]
                    rad_val = clamp(rad_val, lo, hi)

                    joint_names.append(joint)
                    target_angles.append(rad_val)

                    
            # Mover articulaciones (bloqueante para evitar conflictos)
            if joint_names:
                #print("Ángulos recibidos en radianes:")
                print("Ángulos (rad) enviados al NAO:")
                for n, a in zip(joint_names, target_angles):
                    print("  {}: {:.4f}".format(n, a))

                times = [0.5] * len(joint_names)  # Duración fija de 0.5s para suavidad
                try:
                    motion.angleInterpolation(joint_names, target_angles, times, True)
                except Exception as e:
                    print("Error moviendo articulaciones: {}".format(e))

            time.sleep(0.01)  # Pequeña pausa para evitar saturar CPU

    except KeyboardInterrupt:
        print("Interrupción por teclado.")
    finally:
        print("Cerrando conexión y bajando rigidez.")
        conn.close()
        s.close()
        motion.setStiffnesses("Body", 0.0)
        print("Robot en reposo.")


if __name__ == '__main__':
    ip = NAO_IP
    port = NAO_PORT
    if len(sys.argv) >= 2:
        ip = sys.argv[1]
    if len(sys.argv) >= 3:
        port = int(sys.argv[2])

    print("Iniciando control NAO en {}:{}".format(ip, port))
    main(ip, port, SOCK_IP, SOCK_PORT)
