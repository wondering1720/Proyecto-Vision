import tkinter as tk
import cv2
from PIL import Image, ImageTk
import datetime
from src.proctor_logic import Detector

class ProctorApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        
        # 1. Configuración de la Cámara
        self.cap = cv2.VideoCapture(0)
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.detector = Detector()
        
        # 2. Variables de Estado del Examen
        self.examen_activo = False
        self.contador_frames = 0
        self.stats = {"tiempo_total": 0,"distraccion": 0,"ventanas_cambiadas": 0}

        # 3. Elementos de la Interfaz (GUI)
        self.canvas = tk.Canvas(window, width=self.width, height=self.height)
        self.canvas.pack(padx=10, pady=5)

        self.btn_frame = tk.Frame(window)
        self.btn_frame.pack(fill=tk.X, padx=10, pady=5)

        # Botón INICIO
        self.btn_start = tk.Button(self.btn_frame, text="INICIAR EXAMEN", width=20, bg="green", fg="white", command=self.iniciar_examen)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        # Botón DETENER
        self.btn_stop = tk.Button(self.btn_frame, text="FINALIZAR Y REPORTAR", width=20, bg="red", fg="white", state=tk.DISABLED, command=self.finalizar_examen)
        self.btn_stop.pack(side=tk.RIGHT, padx=5)
        
        # Label de Estado
        self.lbl_status = tk.Label(window, text="Estado: Esperando inicio...", font=("Arial", 12))
        self.lbl_status.pack(pady=5)

        # 4. Iniciar el bucle de actualización de video
        self.delay = 15
        self.update()

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def iniciar_examen(self):
        self.examen_activo = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.lbl_status.config(text="Estado: MONITOREANDO 👁️", fg="red")
        print(f"Examen iniciado: {datetime.datetime.now()}")

    def finalizar_examen(self):
        self.examen_activo = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.lbl_status.config(text="Estado: Examen Finalizado", fg="blue")
        print(f"Examen finalizado. Estadísticas: {self.stats}")
        print(f'Examen finalizado: {datetime.datetime.now()}')

    def update(self):
        ret, frame = self.cap.read()
        
        if ret:
            if self.examen_activo:
                self.stats["tiempo_total"] += 1
                
                # 1. Le pasamos el frame al cerebro
                frame, alumno_detectado, coords = self.detector.detectar_alumno(frame)
                
                # 2. Usamos la respuesta para actualizar estadísticas
                if not alumno_detectado:
                    self.stats["distraccion"] += 1
                    cv2.putText(frame, "ALERTA: NO DETECTADO", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                else:
                    # Aquí más adelante pondremos la lógica de si mira a los lados
                    pass
                # -------------------------------

            # Convertir imagen de OpenCV (BGR) a Tkinter (RGB)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.window.after(self.delay, self.update)

    def on_closing(self):
        self.cap.release()
        self.window.destroy()