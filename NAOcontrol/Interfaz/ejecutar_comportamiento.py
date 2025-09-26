# -*- coding: utf-8 -*-
from naoqi import ALProxy

ROBOT_IP = "192.168.137.7"  # Cambia esto si tu NAO tiene otra IP
PORT = 9559

behavior_name = "dancemoves-de295e/behavior_1"

try:
    # Crear proxy al BehaviorManager
    bm = ALProxy("ALBehaviorManager", ROBOT_IP, PORT)

    # Verificar si el comportamiento está cargado
    if not bm.isBehaviorInstalled(behavior_name):
        print("[!] El comportamiento no está instalado:", behavior_name)
    else:
        # Si el comportamiento está corriendo, lo detenemos primero
        if bm.isBehaviorRunning(behavior_name):
            print("[-] El comportamiento ya está en ejecución. Deteniéndolo...")
            bm.stopBehavior(behavior_name)

        # Ejecutar el comportamiento
        print("[+] Ejecutando:", behavior_name)
        bm.startBehavior(behavior_name)

except Exception as e:
    print("[!] Error al ejecutar el comportamiento:", e)
