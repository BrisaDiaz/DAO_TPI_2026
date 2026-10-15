"""DAO para la entidad Multa."""
from typing import List
from sqlalchemy.orm import Session

from api.dao.base_dao import BaseDAO
from api.models import Multa


class MultaDAO(BaseDAO[Multa]):

    def __init__(self, session: Session):
        super().__init__(session, Multa)

    def obtener_pendientes_por_socio(self, socio_id: int) -> List[Multa]:
        """Retorna las multas pendientes de pago de un socio."""
        return self.session.query(Multa).filter(
            Multa.socio_id == socio_id,
            Multa.estado == "Pendiente"
        ).all()

    def obtener_por_prestamo(self, prestamo_id: int) -> Multa | None:
        """Retorna la multa asociada a un préstamo (si existe)."""
        return self.session.query(Multa).filter(
            Multa.prestamo_id == prestamo_id
        ).first()
