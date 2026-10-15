"""DAO para la entidad Prestamo."""
from typing import List
from sqlalchemy.orm import Session

from api.dao.base_dao import BaseDAO
from api.models import Prestamo


class PrestamoDAO(BaseDAO[Prestamo]):

    def __init__(self, session: Session):
        super().__init__(session, Prestamo)

    def obtener_activos(self) -> List[Prestamo]:
        """Retorna todos los préstamos con estado 'Activo'."""
        return self.session.query(Prestamo).filter(
            Prestamo.estado == "Activo"
        ).all()

    def obtener_por_socio(self, socio_id: int) -> List[Prestamo]:
        """Retorna todos los préstamos de un socio (historial)."""
        return self.session.query(Prestamo).filter(
            Prestamo.socio_id == socio_id
        ).all()

    def obtener_activos_por_socio(self, socio_id: int) -> List[Prestamo]:
        """Retorna los préstamos activos de un socio."""
        return self.session.query(Prestamo).filter(
            Prestamo.socio_id == socio_id,
            Prestamo.estado == "Activo"
        ).all()

    def obtener_vencidos(self) -> List[Prestamo]:
        """Retorna todos los préstamos con estado 'Vencido'."""
        return self.session.query(Prestamo).filter(
            Prestamo.estado == "Vencido"
        ).all()

    def obtener_interbibliotecarios(self) -> List[Prestamo]:
        """Retorna los préstamos que involucran traslado entre sedes."""
        return self.session.query(Prestamo).filter(
            Prestamo.sede_destino_id.isnot(None),
            Prestamo.sede_origen_id != Prestamo.sede_destino_id
        ).all()
