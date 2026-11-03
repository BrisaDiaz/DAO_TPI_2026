"""DAO para la entidad Socio."""
from typing import List
from sqlalchemy.orm import Session

from api.dao.base_dao import BaseDAO
from api.models import Socio


class SocioDAO(BaseDAO[Socio]):

    def __init__(self, session: Session):
        super().__init__(session, Socio)

    def crear(self, entidad: Socio) -> Socio:
        """Persiste un nuevo socio validando no duplicidad de documento y número de socio (RN-05)."""
        if entidad.documento and self.obtener_por_documento(entidad.documento):
            raise ValueError(
                f"Ya existe un socio registrado con el documento '{entidad.documento}' (RN-05)."
            )
        if entidad.numero_socio and self.obtener_por_numero_socio(entidad.numero_socio):
            raise ValueError(
                f"Ya existe un socio registrado con el número de socio '{entidad.numero_socio}' (RN-05)."
            )
        return super().crear(entidad)

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
