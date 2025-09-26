# -*- coding: utf-8 -*-
from time import sleep
from flask import Flask, render_template_string, request, jsonify
from naoqi import ALProxy
import subprocess
import os
import threading

app = Flask(__name__)

# Configuración del robot NAO
ROBOT_IP = "localhost"  # Cambiar a la IP real del NAO
PORT = 9559

# Página HTML
HTML = u"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Control NAO</title>
</head>
<body>
    <h1>Panel de Control NAO</h1>
    <button onclick="ejecutar('saludo')">🤖 Saludo</button>
    <button onclick="ejecutar('imitacion')">🎥 Imitación</button>
    <button onclick="ejecutar('despedida')">👋 Despedida</button>

    <script>
    function ejecutar(accion) {
        fetch('/ejecutar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({accion: accion})
        })
        .then(res => res.json())
        .then(data => alert(data.mensaje))
        .catch(err => alert("Error: " + err));
    }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/ejecutar", methods=["POST"])
def ejecutar():
    data = request.get_json()
    accion = data.get("accion")

    try:
        if accion == "saludo":
            bm = ALProxy("ALBehaviorManager", ROBOT_IP, PORT)
            bm.runBehavior("saludar-909889/BienvenidaTerapia")
            return jsonify({"mensaje": "Saludo ejecutado en NAO"})

        elif accion == "despedida":
            bm = ALProxy("ALBehaviorManager", ROBOT_IP, PORT)
            bm.runBehavior("despedida-afd07c/behavior_1")
            return jsonify({"mensaje": "Despedida ejecutada en NAO"})

        elif accion == "imitacion":

            # Función que ejecuta ambos scripts en hilos
            def run_nao_and_vision():
                try:
                    base_path = os.path.dirname(os.path.abspath(__file__))

                    # Python 2.7 para NAO
                    nao_script = os.path.join(base_path, "Version2", "NAOcontrol", "Ejecutar_final.py")
                    python27 = r"C:\Python27\python.exe"
                    subprocess.Popen([python27, nao_script])

                    # Esperar un par de segundos para que NAO esté listo
                    sleep(3)

                    # Python 3.10 para Vision
                    vision_script = os.path.join(base_path, "Version2", "Vision_comp.py")
                    python310 = r"C:\Users\sover\.conda\envs\mi_entorno_310\python.exe"
                    subprocess.Popen([python310, vision_script])

                except Exception as e:
                    print("Error iniciando imitación:", e)

            # Lanzar en un hilo para no bloquear Flask
            threading.Thread(target=run_nao_and_vision).start()

            return jsonify({"mensaje": "Imitación iniciada"})

        else:
            return jsonify({"mensaje": "Acción desconocida"}), 400

    except Exception as e:
        mensaje = u"Error: {}".format(e)
        return jsonify({"mensaje": mensaje}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
