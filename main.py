"""
Punto de entrada principal del Sistema de Gestión de Bibliotecas.
Inicializa la base de datos (api) y lanza la interfaz gráfica de escritorio (src).
"""
from api.database import crear_tablas, SessionLocal
from api.seed import ejecutar_seed
from api.models import Sede

def main():
    # Inicializar base de datos SQLite y crear tablas si no existen
    crear_tablas()
    
    session = SessionLocal()
    try:
        # Verificar si la base de datos ya tiene sedes cargadas 
        # para evitar reinsertar datos y generar errores de clave única.
        if session.query(Sede).count() == 0:
            print("Base de datos vacía. Poblando con datos de prueba (seed)...")
            ejecutar_seed(session)
        else:
            print("La base de datos ya contiene registros. Omitiendo seed.")
    except Exception as e:
        session.rollback()
        print(f"Error durante la ejecución del seed: {e}")
    finally:
        session.close()

    # Iniciar la interfaz gráfica de usuario (Tkinter)
    from src.pages.main_window import MainWindow
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()