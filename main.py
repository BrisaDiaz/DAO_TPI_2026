"""
Punto de entrada principal del Sistema de Gestión de Bibliotecas.
Inicializa la base de datos (api) y lanza la interfaz gráfica de escritorio (src).
"""
from api.database import crear_tablas


def main():
    # Inicializar base de datos SQLite y crear tablas si no existen
    crear_tablas()

    # Iniciar la interfaz gráfica de usuario (Tkinter)
    from src.pages.main_window import MainWindow
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
