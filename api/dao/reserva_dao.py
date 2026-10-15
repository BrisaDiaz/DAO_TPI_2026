"""DAO para la entidad Reserva."""
from typing import List
from sqlalchemy.orm import Session

from api.dao.base_dao import BaseDAO
from api.models import Reserva


class ReservaDAO(BaseDAO[Reserva]):

    def __init__(self, session: Session):
        super().__init__(session, Reserva)

    def obtener_por_socio(self, socio_id: int) -> List[Reserva]:
        """Retorna todas las reservas de un socio."""
        return self.session.query(Reserva).filter(
            Reserva.socio_id == socio_id
        ).all()

    def obtener_pendientes_por_libro(self, libro_id: int) -> List[Reserva]:
        """Retorna las reservas pendientes para un libro del catálogo."""
        return self.session.query(Reserva).filter(
            Reserva.libro_id == libro_id,
            Reserva.estado == "Pendiente"
        ).all()

    def obtener_pendientes_por_socio(self, socio_id: int) -> List[Reserva]:
        """Retorna las reservas pendientes de un socio."""
        return self.session.query(Reserva).filter(
            Reserva.socio_id == socio_id,
            Reserva.estado == "Pendiente"
        ).all()
