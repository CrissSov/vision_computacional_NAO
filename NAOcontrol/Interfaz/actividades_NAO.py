from naoqi import ALProxy

ROBOT_IP = "localhost"  # Reemplaza con la IP real de tu NAO
PORT = 50588

try:
    # Crear proxy al BehaviorManager
    bm = ALProxy("ALBehaviorManager", ROBOT_IP, PORT)

    # Obtener todos los comportamientos instalados
    behaviors = bm.getInstalledBehaviors()

    # Escribir en un archivo de texto
    with open("comportamientos_nao.txt", "w") as f:
        f.write("Comportamientos instalados en NAO:\n\n")
        for behavior in behaviors:
            f.write(behavior + "\n")

    print("[+] Comportamientos guardados en 'comportamientos_nao.txt'.")

except Exception as e:
    print("[!] Error al conectar con el robot o exportar:", e)