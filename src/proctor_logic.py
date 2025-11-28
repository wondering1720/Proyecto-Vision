import cv2
import mediapipe as mp
from ultralytics import YOLO

class Detector:
    def __init__(self):
        print("Cargando modelo YOLO...")
        self.model = YOLO("yolov8n.pt") 
        print("Modelo cargado.")

    def detectar_trampas(self, frame):
        # Solo buscamos celulares (clase 67)
        results = self.model(frame, stream=True, classes=[1], verbose=False)

        celular_detectado = False
        alerta = ""
        
        # deteccion de celular
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confianza = float(box.conf[0])
                if confianza > 0.4:
                    celular_detectado = True
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, "CELULAR", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        es_sospechoso = False
        if celular_detectado:
            alerta = "ALERTA: Uso de Celular"
            es_sospechoso = True

        return frame, es_sospechoso, alerta

class DetectorMirada:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def analizar_cabeza(self, frame):
        alto, ancho, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        estado = "Desconocido"
        
        if results.multi_face_landmarks:
            for landmarks in results.multi_face_landmarks:
                def obtener_coords(idx):
                    pt = landmarks.landmark[idx]
                    return int(pt.x * ancho), int(pt.y * alto)

                # Puntos clave
                p_nariz = obtener_coords(1)
                p_izq_cara = obtener_coords(234)
                p_der_cara = obtener_coords(454)
                p_barbilla = obtener_coords(152)
                p_frente = obtener_coords(10)

                # --- LOGICA HORIZONTAL (Izquierda/Derecha) ---
                dist_nariz_izq = p_nariz[0] - p_izq_cara[0]
                dist_nariz_der = p_der_cara[0] - p_nariz[0]
                if dist_nariz_der == 0: dist_nariz_der = 0.001
                ratio_h = dist_nariz_izq / dist_nariz_der

                # --- LOGICA VERTICAL (Arriba/Abajo) ---
                dist_nariz_frente = p_nariz[1] - p_frente[1]
                dist_nariz_barbilla = p_barbilla[1] - p_nariz[1]
                if dist_nariz_barbilla == 0: dist_nariz_barbilla = 0.001
                ratio_v = dist_nariz_frente / dist_nariz_barbilla

                # Umbrales
                if ratio_h < 0.4:
                    estado = "Izquierda"
                elif ratio_h > 2.5:
                    estado = "Derecha"
                elif ratio_v < 0.6: # Nariz muy cerca de la frente
                    estado = "Arriba"
                elif ratio_v > 1.8: # Nariz muy cerca de la barbilla
                    estado = "Abajo"
                else:
                    estado = "Centro"

                # Referencias visuales para depuración
                cv2.circle(frame, p_nariz, 3, (0, 255, 255), -1)
                cv2.line(frame, p_frente, p_barbilla, (200, 200, 200), 1)

        else:
            estado = "No detectado"

        return frame, estado