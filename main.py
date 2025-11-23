import tkinter as tk
from src.interface import ProctorApp

def main():
    root = tk.Tk()
    
    # Instanciar nuestra aplicación
    app = ProctorApp(root, "Sistema de Monitoreo de Exámenes - Visión por Computadora")
    
    # Iniciar el bucle principal de la interfaz
    root.mainloop()

if __name__ == "__main__":
    main()