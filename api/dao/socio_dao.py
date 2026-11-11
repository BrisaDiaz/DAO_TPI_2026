"""DAO para la entidad Socio."""
import re
from typing import List
from sqlalchemy.orm import Session

from api.dao.base_dao import BaseDAO
from api.models import Socio

# DNI argentino: solo dígitos, entre 7 y 8 caracteres.
PATRON_DNI = re.compile(r"\d{7,8}", re.ASCII)


def es_dni_valido(documento: str | None) -> bool:
    """Indica si el documento tiene formato de DNI válido (solo números, 7 u 8 dígitos)."""
    return bool(documento) and PATRON_DNI.fullmatch(documento) is not None


# Email: algo@dominio.ext, sin espacios.
PATRON_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def es_email_valido(email: str | None) -> bool:
    """Indica si el email no está vacío y tiene un formato básico válido (usuario@dominio.ext)."""
    return bool(email) and PATRON_EMAIL.fullmatch(email) is not None


class SocioDAO(BaseDAO[Socio]):

    def __init__(self, session: Session):
        super().__init__(session, Socio)

    def crear(self, entidad: Socio) -> Socio:
        """Persiste un nuevo socio validando formato de DNI y no duplicidad de documento y número de socio (RN-05)."""
        if not es_dni_valido(entidad.documento):
            raise ValueError(
                f"El documento '{entidad.documento}' no es válido: debe contener solo números (7 u 8 dígitos)."
            )
        if not es_email_valido(entidad.email):
            raise ValueError(
                f"El email '{entidad.email}' no es válido: es obligatorio y debe tener formato usuario@dominio.ext "
                "(requerido para las notificaciones a socios)."
            )
        if self.obtener_por_documento(entidad.documento):
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
