"""DAO para la entidad Ejemplar."""
from typing import List
from sqlalchemy.orm import Session

from api.dao.base_dao import BaseDAO
from api.models import Ejemplar


class EjemplarDAO(BaseDAO[Ejemplar]):

    def __init__(self, session: Session):
        super().__init__(session, Ejemplar)

    def crear(self, entidad: Ejemplar) -> Ejemplar:
        """Persiste un nuevo ejemplar validando no duplicidad de código de inventario (RN-05)."""
        if entidad.codigo_inventario and self.obtener_por_codigo_inventario(entidad.codigo_inventario):
            raise ValueError(
                f"Ya existe un ejemplar registrado con el código de inventario '{entidad.codigo_inventario}' (RN-05)."
            )
        return super().crear(entidad)

    def obtener_por_sede(self, sede_id: int) -> List[Ejemplar]:
        """Retorna todos los ejemplares asignados a una sede."""
        return self.session.query(Ejemplar).filter(
            Ejemplar.sede_id == sede_id
        ).all()

    def obtener_disponibles_por_sede(self, sede_id: int) -> List[Ejemplar]:
        """Retorna los ejemplares con estado 'Disponible' en una sede."""
        return self.session.query(Ejemplar).filter(
            Ejemplar.sede_id == sede_id,
            Ejemplar.estado_fisico == "Disponible"
        ).all()

    def obtener_por_codigo_inventario(self, codigo: str) -> Ejemplar | None:
        """Busca un ejemplar por su código de inventario único."""
        return self.session.query(Ejemplar).filter(
            Ejemplar.codigo_inventario == codigo
        ).first()

    def obtener_por_libro(self, libro_id: int) -> List[Ejemplar]:
        """Retorna todos los ejemplares de un libro del catálogo."""
        return self.session.query(Ejemplar).filter(
            Ejemplar.libro_id == libro_id
        ).all()
