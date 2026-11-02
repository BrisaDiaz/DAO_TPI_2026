"""
Configuración del motor SQLAlchemy y gestión de sesiones.
Base de datos: SQLite local (biblioteca.db en la raíz del proyecto).
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Motor SQLite - el archivo se crea en la raíz del proyecto
DATABASE_URL = "sqlite:///biblioteca.db"

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM."""
    pass


def crear_tablas():
    """Crea todas las tablas definidas en los modelos si no existen."""
    from api.models import (Sede, Socio, Autor, Libro, Ejemplar,
                            Prestamo, Multa, Remito, Reserva)
    Base.metadata.create_all(bind=engine)
    migrar_columnas_faltantes()


def migrar_columnas_faltantes(eng=None) -> None:
    """
    Agrega columnas nuevas a tablas ya existentes (create_all no altera tablas creadas).
    Permite seguir usando un biblioteca.db generado con una version anterior del modelo.
    """
    eng = eng or engine
    inspector = inspect(eng)
    if "reservas" in inspector.get_table_names():
        columnas = {c["name"] for c in inspector.get_columns("reservas")}
        if "fecha_notificacion" not in columnas:
            with eng.begin() as conn:
                conn.execute(text("ALTER TABLE reservas ADD COLUMN fecha_notificacion DATETIME"))


def get_session():
    """Genera una sesión de base de datos para uso en la aplicación."""
    session = SessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise
