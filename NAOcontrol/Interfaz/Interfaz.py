# -*- coding: utf-8 -*-
import threading
import Tkinter as tk
import tkMessageBox
import json
import time
from naoqi import ALProxy
import threading

# Configuración del robot
ROBOT_IP = "192.168.137.134"  # Cambiar a la IP real del NAO
PORT = 9559 #9559

# Cargar ejercicios desde JSON
with open("comportamientos.json", "r") as f:
    ejercicios = json.load(f)

    rutina = []  # Lista de la rutina seleccionada
    basicos=["saludar-909889/BienvenidaTerapia","despedida-afd07c/behavior_1"]
arm_joints = [
    "RShoulderPitch",
    "RShoulderRoll",
    "RElbowYaw",
    "RElbowRoll",
    "RWristYaw"
]


def agregar_ejercicio(ejercicio, spinbox, listbox):
    repeticiones = int(spinbox.get())
    # Convertir todo a UTF-8 para Python 2.7
    item = {
        "id": ejercicio["id"].encode('utf-8'),
        "nombre": ejercicio["nombre"].encode('utf-8'),
        "descripcion": ejercicio["descripcion"].encode('utf-8'),
        "repeticiones": repeticiones
    }
    rutina.append(item)
    listbox.insert(tk.END, "%s (x%d)" % (item["nombre"], repeticiones))
    print ("Agregado:", item["nombre"], "x", repeticiones)


def remover_ejercicio(listbox):
    seleccionado = listbox.curselection()
    if seleccionado:
        idx = seleccionado[0]
        eliminado = rutina.pop(idx)
        listbox.delete(idx)
        print("Eliminado:", eliminado["nombre"])
    else:
        tkMessageBox.showinfo("Info", "Selecciona un ejercicio para remover.")

def mostrar_rutina():
    if not rutina:
        tkMessageBox.showinfo("Info", "No hay ejercicios en la rutina.")
        return
    resumen = "\n".join(["- %s x%d" % (r["nombre"], r["repeticiones"]) for r in rutina])
    tkMessageBox.showinfo("Rutina Final", resumen)
    print("\n=== Rutina Final ===\n" + resumen)


def ejecutar_rutina():
    if not rutina:
        tkMessageBox.showinfo("Info", "No hay ejercicios en la rutina para ejecutar.")
        return
    try:
        bm = ALProxy("ALBehaviorManager", ROBOT_IP, PORT)
        tts = ALProxy("ALTextToSpeech", ROBOT_IP, PORT)

        # === SALUDO (primer elemento de basicos) ===
        saludo = basicos[0]
        if bm.isBehaviorInstalled(saludo):
            if not bm.isBehaviorRunning(saludo):      
                bm.runBehavior(saludo)
                while bm.isBehaviorRunning(saludo):
                    time.sleep(1)
        else:
            print("[!] El comportamiento de saludo no está instalado:", saludo)

        # === EJECUTAR RUTINA DE EJERCICIOS ===
        for r in rutina:
            behavior_name = r["id"]         
            repeticiones = r.get("repeticiones", 1)
            nombre = r.get("nombre", "ejercicio")

            if not bm.isBehaviorInstalled(behavior_name):
                print("[!] No está instalado:", behavior_name)
                continue

            try:
                tts.say("Iniciamos el ejercicio {}".format(nombre))
                time.sleep(1)
            except Exception as e:
                print("Error TTS:", e)

            for i in range(repeticiones):
                print("Repeticion {}".format(i+1))
                # Iniciar registro de ángulos en paralelo
                t_registro = threading.Thread(target=registrar_angulos,
                                              args=(5, "ejercicio{}_rep{}.csv".format(nombre, i+1)))
                t_registro.start()

                # Ejecutar comportamiento
                bm.post.runBehavior(behavior_name)

                try:
                    tts.say("Muy bien, repetición número {}".format(i+1))
                except Exception as e:
                    print("Error TTS:", e)

                # Esperar a que termine
                while bm.isBehaviorRunning(behavior_name):
                    time.sleep(0.5)
                t_registro.join()

            try:
                tts.say("Has terminado {}".format(nombre))
                time.sleep(2)
            except Exception as e:
                print("Error TTS:", e)

        # === DESPEDIDA (último elemento de basicos) ===
        despedida = basicos[-1]
        if bm.isBehaviorInstalled(despedida):
            if bm.isBehaviorRunning(despedida):
                bm.stopBehavior(despedida)
            bm.runBehavior(despedida)
        else:
            print("[!] El comportamiento de despedida no está instalado:", despedida)

    except Exception as e:
        tkMessageBox.showerror("Error", "No se pudo conectar con el robot:\n{}".format(e))


def registrar_angulos(duracion=10.0, filename="angulos.csv"):
    """
    Registra los ángulos del brazo durante 'duracion' segundos.
    Guarda resultados en un CSV con columnas: Tiempo, articulaciones.
    """
    


# Crear ventana principal
root = tk.Tk()
root.title("Configurar Rutina de Terapia")

# Crear un frame para cada ejercicio
for idx, ejercicio in enumerate(ejercicios):
    frame = tk.Frame(root, bd=2, relief="groove", padx=10, pady=10, bg="#e6e6e6")
    frame.pack(fill="x", padx=10, pady=5)

    # Nombre del ejercicio
    tk.Label(frame, text=ejercicio["nombre"], font=("Arial", 10, "bold"), bg="#e6e6e6").grid(row=0, column=0, sticky="w")

    # Descripción
    tk.Label(frame, text=ejercicio["descripcion"], width=40, anchor="w", bg="white", relief="solid").grid(row=0, column=1, padx=5, sticky="w")

    # Spinbox para repeticiones
    tk.Label(frame, text="Número de repeticiones", bg="#e6e6e6").grid(row=1, column=0, sticky="w")
    spin = tk.Spinbox(frame, from_=1, to=20, width=5)
    spin.grid(row=1, column=1, sticky="w")

    # Botón agregar
    tk.Button(frame, text="Agregar", bg="#2d89ef", fg="white",
              command=lambda e=ejercicio, s=spin: agregar_ejercicio(e, s, listbox)).grid(row=1, column=2, padx=10)

# Frame para la lista de rutina
frame_rutina = tk.Frame(root, bd=2, relief="ridge", padx=10, pady=10, bg="#f0f0f0")
frame_rutina.pack(fill="both", expand=True, padx=10, pady=10)

tk.Label(frame_rutina, text="Rutina seleccionada:", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(anchor="w")

listbox = tk.Listbox(frame_rutina, width=50, height=8)
listbox.pack(pady=5)

# Botones para manejar la rutina
btns = tk.Frame(frame_rutina, bg="#f0f0f0")
btns.pack()

tk.Button(btns, text="Remover seleccionado", command=lambda: remover_ejercicio(listbox), bg="red", fg="white").grid(row=0, column=0, padx=5)
tk.Button(btns, text="Mostrar Rutina Final", command=mostrar_rutina, bg="black", fg="white").grid(row=0, column=1, padx=5)
tk.Button(btns, text="Ejecutar en Robot", command=ejecutar_rutina, bg="blue", fg="white").grid(row=0, column=2, padx=5)

root.mainloop()
