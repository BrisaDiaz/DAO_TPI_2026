"""DAO para la entidad Sede."""
from typing import List
from sqlalchemy.orm import Session

from api.dao.base_dao import BaseDAO
from api.models import Sede


class SedeDAO(BaseDAO[Sede]):

    def __init__(self, session: Session):
        super().__init__(session, Sede)

    def obtener_activas(self) -> List[Sede]:
        """Retorna únicamente las sedes con estado 'activo'."""
        return self.session.query(Sede).filter(Sede.estado == "activo").all()

    def obtener_por_direccion(self, direccion: str) -> Sede | None:
        """Busca una sede por su dirección."""
        return self.session.query(Sede).filter(Sede.direccion == direccion).first()
