"""DAO para la entidad Remito."""
from typing import List
from sqlalchemy.orm import Session

from api.dao.base_dao import BaseDAO
from api.models import Remito


class RemitoDAO(BaseDAO[Remito]):

    def __init__(self, session: Session):
        super().__init__(session, Remito)

    def obtener_por_prestamo(self, prestamo_id: int) -> Remito | None:
        """Retorna el remito asociado a un préstamo interbibliotecario."""
        return self.session.query(Remito).filter(
            Remito.prestamo_id == prestamo_id
        ).first()

    def obtener_por_codigo(self, codigo_remito: str) -> Remito | None:
        """Busca un remito por su código único."""
        return self.session.query(Remito).filter(
            Remito.codigo_remito == codigo_remito
        ).first()

    def obtener_en_transito(self) -> List[Remito]:
        """Retorna los remitos que aún no fueron recibidos."""
        return self.session.query(Remito).filter(
            Remito.estado.in_(["Empaquetado", "Despachado"])
        ).all()
