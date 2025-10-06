import numpy as np
from holistic_data import JointType

class Elbows:
    def __init__(self):
        # Rangos articulares del NAO en GRADOS
        self.LEFT_RANGE_DEG = (-88.5, -2.0)   # NAO: brazo izquierdo
        self.RIGHT_RANGE_DEG = (2.0, 88.5)    # NAO: brazo derecho

    def calculate_angle_yz_plane(self, p1, p2, p3):
        """Calcula el ángulo entre segmentos proyectados en el plano YZ (en grados)."""
        def to_yz(pt):
            return np.array([pt.y, pt.z])

        v1 = to_yz(p1) - to_yz(p2)
        v2 = to_yz(p3) - to_yz(p2)

        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        if norm_v1 == 0 or norm_v2 == 0:
            return 180.0  # por defecto brazo extendido

        dot = np.clip(np.dot(v1 / norm_v1, v2 / norm_v2), -1.0, 1.0)
        return np.degrees(np.arccos(dot))  # en grados

    def map_to_nao_deg(self, flex_angle_deg, side="Left"):
        # Asegurar que esté en el rango [0, 180]
        flex_angle_deg = max(0, min(180, flex_angle_deg))

        if side == "Left":
            return np.interp(flex_angle_deg, [180, 0], self.LEFT_RANGE_DEG)
        elif side == "Right":
            return np.interp(flex_angle_deg, [180, 0], self.RIGHT_RANGE_DEG)

    def get_elbow_angles_for_nao(self, bodyJointsArray):
        try:
            ls = bodyJointsArray[JointType.LeftShoulder]
            le = bodyJointsArray[JointType.LeftElbow]
            lw = bodyJointsArray[JointType.LeftWrist]

            rs = bodyJointsArray[JointType.RightShoulder]
            re = bodyJointsArray[JointType.RightElbow]
            rw = bodyJointsArray[JointType.RightWrist]

            l_flex_deg = self.calculate_angle_yz_plane(ls, le, lw)
            r_flex_deg = self.calculate_angle_yz_plane(rs, re, rw)

            # Imprimir para depurar
            #print("ÁNGULOS DE FLEXIÓN (reales en grados):")
            #print(f"  Izquierdo (YZ): {l_flex_deg:.2f}°")
            #print(f"  Derecho  (YZ): {r_flex_deg:.2f}°")

            # Mapea directamente al rango NAO (en grados)
            return {
                "LElbowRoll": self.map_to_nao_deg(l_flex_deg, "Left"),
                "RElbowRoll": self.map_to_nao_deg(r_flex_deg, "Right")
            }

        except KeyError as e:
            print("⚠️ Punto faltante para codo:", e)
            return {}
