import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import datetime
from src.proctor_logic import Detector, DetectorMirada

class ProctorApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        
        # 1. Configuración de la Cámara y Detectores
        self.cap = cv2.VideoCapture(0)
        self.detector_trampas = Detector()
        self.detector_mirada = DetectorMirada()
        
        # 2. Variables de Estado
        self.examen_activo = False
        self.ventana_activa = True # Asumimos que empieza con foco
        
        self.stats = {
            "tiempo_total": 0,       # Frames totales del examen
            "tiempo_distraccion": 0, # Frames donde hubo anomalía
            "ventanas_cambiadas": 0, # Contador de eventos
            "tiempo_fuera_foco": 0,  # Frames mientras la ventana no estaba activa
            "mirada_izquierda": 0, 
            "mirada_derecha": 0,
            "mirada_arriba": 0,
            "mirada_abajo": 0,
            "uso_celular": 0
        }

        # Detección de cambio de ventana (Mouse/Teclado/Alt-Tab)
        self.window.bind("<FocusOut>", self.al_perder_foco)
        self.window.bind("<FocusIn>", self.al_ganar_foco)

        # 3. Interfaz Gráfica
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.canvas = tk.Canvas(window, width=self.width, height=self.height)
        self.canvas.pack(padx=10, pady=5)

        self.btn_frame = tk.Frame(window)
        self.btn_frame.pack(fill=tk.X, padx=10, pady=5)

        self.btn_start = tk.Button(self.btn_frame, text="INICIAR EXAMEN", width=20, 
                                   bg="green", fg="white", command=self.iniciar_examen)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(self.btn_frame, text="FINALIZAR", width=20, 
                                  bg="red", fg="white", state=tk.DISABLED, command=self.finalizar_examen)
        self.btn_stop.pack(side=tk.RIGHT, padx=5)
        
        self.lbl_status = tk.Label(window, text="Estado: Esperando inicio...", font=("Arial", 12))
        self.lbl_status.pack(pady=5)

        self.delay = 30 # ~33 FPS
        self.update()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def al_perder_foco(self, event):
        if self.examen_activo:
            self.ventana_activa = False
            self.stats["ventanas_cambiadas"] += 1
            print("¡Alerta! Cambio de ventana detectado.")

    def al_ganar_foco(self, event):
        if self.examen_activo:
            self.ventana_activa = True

    def iniciar_examen(self):
        self.examen_activo = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.lbl_status.config(text="Estado: MONITOREANDO 👁️", fg="green")
        
        # Reiniciar stats
        for k in self.stats: self.stats[k] = 0
        print(f"Examen iniciado: {datetime.datetime.now()}")

    def finalizar_examen(self):
        self.examen_activo = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.lbl_status.config(text="Estado: Finalizado", fg="blue")
        
        # Cálculo final
        total = self.stats["tiempo_total"] if self.stats["tiempo_total"] > 0 else 1
        distraccion = self.stats["tiempo_distraccion"]
        porcentaje = (distraccion / total) * 100
        
        veredicto = "APROBADO" if porcentaje <= 40 else "REVISIÓN (Sospechoso > 40%)"

        reporte = (
            f"\n--- REPORTE FINAL ---\n"
            f"Tiempo Total (frames): {total}\n"
            f"Tiempo Distraído: {distraccion} ({porcentaje:.2f}%)\n"
            f"Veredicto: {veredicto}\n"
            f"---------------------\n"
            f"DETALLE DE INCIDENCIAS:\n"
            f"- Cambios de Ventana: {self.stats['ventanas_cambiadas']}\n"
            f"- Tiempo fuera de app: {self.stats['tiempo_fuera_foco']}\n"
            f"- Mirada Izquierda: {self.stats['mirada_izquierda']}\n"
            f"- Mirada Derecha: {self.stats['mirada_derecha']}\n"
            f"- Mirada Arriba: {self.stats['mirada_arriba']}\n"
            f"- Mirada Abajo: {self.stats['mirada_abajo']}\n"
            f"- Uso de Celular: {self.stats['uso_celular']}\n"
        )
        print(reporte)
        messagebox.showinfo("Reporte de Examen", reporte)

    def update(self):
        ret, frame = self.cap.read()
        
        if ret:
            if self.examen_activo:
                self.stats["tiempo_total"] += 1
                
                texto_estado = "CORRECTO"
                color_texto = (0, 255, 0)
                es_distraccion = False

                # 1. Checar Ventana Activa (Prioridad Alta)
                if not self.ventana_activa:
                    self.stats["tiempo_fuera_foco"] += 1
                    es_distraccion = True
                    texto_estado = "ALERTA: VENTANA INACTIVA"
                    color_texto = (0, 0, 255)
                    # Opcional: Poner pantalla en gris o negro en el video
                    cv2.putText(frame, "REGRESA AL EXAMEN", (50, 200), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

                else:
                    # 2. Detectar Celular
                    frame, trampa, alerta_trampa = self.detector_trampas.detectar_trampas(frame)
                    
                    # 3. Detectar Mirada
                    frame, estado_mirada = self.detector_mirada.analizar_cabeza(frame)
                    
                    if trampa:
                        es_distraccion = True
                        self.stats["uso_celular"] += 1
                        texto_estado = alerta_trampa
                        color_texto = (0, 0, 255)
                    
                    elif estado_mirada != "Centro" and estado_mirada != "No detectado":
                        es_distraccion = True
                        if estado_mirada == "Izquierda": self.stats["mirada_izquierda"] += 1
                        elif estado_mirada == "Derecha": self.stats["mirada_derecha"] += 1
                        elif estado_mirada == "Arriba": self.stats["mirada_arriba"] += 1
                        elif estado_mirada == "Abajo": self.stats["mirada_abajo"] += 1
                        
                        texto_estado = f"MIRADA: {estado_mirada.upper()}"
                        color_texto = (0, 165, 255) # Naranja

                if es_distraccion:
                    self.stats["tiempo_distraccion"] += 1

                cv2.putText(frame, texto_estado, (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_texto, 2)

            # Convertir para Tkinter
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.window.after(self.delay, self.update)

    def on_closing(self):
        self.cap.release()
        self.window.destroy()