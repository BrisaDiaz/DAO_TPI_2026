"""
DAO Base genérico con operaciones CRUD reutilizables.
Todos los DAOs específicos heredan de esta clase.
"""
from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy.orm import Session
from api.database import Base

T = TypeVar("T", bound=Base)


class BaseDAO(Generic[T]):
    """Clase base que provee operaciones CRUD genéricas para cualquier entidad."""

    def __init__(self, session: Session, modelo: Type[T]):
        self.session = session
        self.modelo = modelo

    def crear(self, entidad: T) -> T:
        """Persiste una nueva entidad en la base de datos."""
        self.session.add(entidad)
        self.session.commit()
        self.session.refresh(entidad)
        return entidad

    def obtener_por_id(self, id: int) -> Optional[T]:
        """Retorna una entidad por su ID o None si no existe."""
        return self.session.query(self.modelo).filter(self.modelo.id == id).first()

    def obtener_todos(self) -> List[T]:
        """Retorna todas las entidades de este tipo."""
        return self.session.query(self.modelo).all()

    def actualizar(self) -> None:
        """Confirma los cambios pendientes en la sesión."""
        self.session.commit()

    def eliminar(self, entidad: T) -> None:
        """Elimina una entidad de la base de datos."""
        self.session.delete(entidad)
        self.session.commit()
