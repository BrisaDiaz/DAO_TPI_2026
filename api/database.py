"""
Configuración del motor SQLAlchemy y gestión de sesiones.
Base de datos: SQLite local (biblioteca.db en la raíz del proyecto).
"""
from sqlalchemy import create_engine
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


def get_session():
    """Genera una sesión de base de datos para uso en la aplicación."""
    session = SessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise
