import cv2
from ultralytics import YOLO

class Detector:
    def __init__(self):
        # Cargamos el modelo YOLO nano (el más rápido/ligero)
        # La primera vez que corras esto, se descargará solo.
        print("Cargando modelo YOLO...")
        self.model = YOLO("yolov8n.pt") 
        print("Modelo cargado.")

    def detectar_alumno(self, frame):
        """
        Recibe: Un frame de video (imagen).
        Hace: Busca personas/caras.
        Devuelve: El frame pintado y datos de la detección.
        """
        # Ejecutamos YOLO sobre el frame
        # stream=True hace que sea más rápido para video en vivo
        # classes=[0] le dice que SOLO busque la clase 0 ('person')
        results = self.model(frame, stream=True, classes=[0], verbose=False)

        detectado = False
        coordenadas = None # (x1, y1, x2, y2)

        # Procesar los resultados
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Obtenemos las coordenadas del recuadro
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Guardamos las coordenadas de la primera persona que veamos
                coordenadas = (x1, y1, x2, y2)
                detectado = True

                # Dibujamos el recuadro en el frame directamente
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, "Alumno", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Solo nos interesa detectar una persona, así que rompemos el loop
                break 

        return frame, detectado, coordenadas