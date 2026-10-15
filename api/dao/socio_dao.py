"""DAO para la entidad Socio."""
from typing import List
from sqlalchemy.orm import Session

from api.dao.base_dao import BaseDAO
from api.models import Socio


class SocioDAO(BaseDAO[Socio]):

    def __init__(self, session: Session):
        super().__init__(session, Socio)

    def obtener_por_documento(self, documento: str) -> Socio | None:
        """Busca un socio por su número de documento (DNI)."""
        return self.session.query(Socio).filter(Socio.documento == documento).first()

    def obtener_por_numero_socio(self, numero_socio: str) -> Socio | None:
        """Busca un socio por su número identificatorio."""
        return self.session.query(Socio).filter(
            Socio.numero_socio == numero_socio
        ).first()

    def obtener_activos(self) -> List[Socio]:
        """Retorna todos los socios habilitados (activo=1)."""
        return self.session.query(Socio).filter(Socio.activo == 1).all()
