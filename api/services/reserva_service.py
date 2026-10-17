"""
Servicio de Reservas - Lógica de negocio y orquestación.

Orquesta la creación, cancelación y caducidad de reservas de material bibliográfico,
aplicando las reglas de negocio y supuestos del dominio:
- RN-01: Disponibilidad de ejemplar (solo se puede reservar si el stock en la sede es 0).
- RN-02 / RN-04: Socio habilitado y sedes activas.
- SUP-04: Límite de hasta 3 préstamos/reservas simultáneas activas.
- SUP-05: Caducidad automática de la reserva a las 48 horas de la notificación.
- SUP-06: Creación de reserva solo permitida cuando stock disponible = 0.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from api.models import Reserva, Ejemplar
from api.dao.reserva_dao import ReservaDAO
from api.dao.ejemplar_dao import EjemplarDAO
from api.dao.socio_dao import SocioDAO
from api.dao.sede_dao import SedeDAO
from api.dao.prestamo_dao import PrestamoDAO


class ReservaService:
    """Servicio de negocio para la gestión integral de reservas."""

    HORAS_CADUCIDAD_DEFAULT = 48  # SUP-05: 48 horas para caducidad
    LIMITE_PRESTAMOS_MAX = 3      # SUP-04: Máximo 3 préstamos/reservas activas

    def __init__(self, session: Session):
        self.session = session
        self.reserva_dao = ReservaDAO(session)
        self.ejemplar_dao = EjemplarDAO(session)
        self.socio_dao = SocioDAO(session)
        self.sede_dao = SedeDAO(session)
        self.prestamo_dao = PrestamoDAO(session)

    def crear_reserva(
        self,
        socio_id: int,
        libro_id: int,
        sede_id: int,
    ) -> Reserva:
        """
        Crea una nueva reserva de un libro en una sede específica.

        Validaciones:
        - Socio existente y habilitado (RN-02).
        - Sede existente y activa (RN-04).
        - SUP-04: El socio no debe superar el límite de 3 préstamos/reservas activos.
        - SUP-06: Solo se puede reservar si el stock disponible en la sede es 0.
        """
        socio = self.socio_dao.obtener_por_id(socio_id)
        sede = self.sede_dao.obtener_por_id(sede_id)

        if not socio:
            raise ValueError(f"No se encontró el socio con ID {socio_id}.")
        if not sede:
            raise ValueError(f"No se encontró la sede con ID {sede_id}.")

        # RN-04: Sede activa
        if sede.estado != "activo":
            raise ValueError(
                f"La sede '{sede.direccion}' se encuentra dada de baja."
            )

        # RN-02: Socio habilitado
        if socio.activo == 0:
            raise ValueError(
                f"El socio '{socio.nombre} {socio.apellido}' se encuentra inhabilitado."
            )

        # SUP-04: Control de límite máximo de préstamos activos
        prestamos_activos = self.session.query(PrestamoDAO).filter(
            PrestamoDAO.model.socio_id == socio_id,
            PrestamoDAO.model.estado == "Activo"
        ).count() if hasattr(PrestamoDAO, 'model') else 0
        
        # O mediante la query de sesión directa:
        from api.models import Prestamo
        prestamos_activos = self.session.query(Prestamo).filter(
            Prestamo.socio_id == socio_id,
            Prestamo.estado == "Activo"
        ).count()

        if prestamos_activos >= self.LIMITE_PRESTAMOS_MAX:
            raise ValueError(
                f"El socio alcanzó el límite máximo de {self.LIMITE_PRESTAMOS_MAX} "
                "préstamos activos simultáneos (SUP-04)."
            )

        # SUP-06: El stock de ejemplares disponibles en la sede debe ser igual a cero
        ejemplares_disponibles = self.session.query(Ejemplar).filter(
            Ejemplar.libro_id == libro_id,
            Ejemplar.sede_id == sede_id,
            Ejemplar.estado_fisico == "Disponible"
        ).count()

        if ejemplares_disponibles > 0:
            raise ValueError(
                f"No se puede realizar una reserva: existen {ejemplares_disponibles} "
                "ejemplar(es) disponible(s) en esta sede (SUP-06)."
            )

        # Verificar si el socio ya posee una reserva pendiente para la misma obra
        reservas_previas = self.reserva_dao.obtener_pendientes_por_socio(socio_id)
        if any(r.libro_id == libro_id for r in reservas_previas):
            raise ValueError(
                "El socio ya posee una reserva pendiente activa para esta obra."
            )

        # Crear entidad Reserva
        reserva = Reserva(
            socio_id=socio_id,
            libro_id=libro_id,
            sede_id=sede_id,
            fecha_reserva=datetime.now(),
            estado="Pendiente"
        )
        return self.reserva_dao.crear(reserva)

    def cancelar_reserva(self, reserva_id: int) -> Reserva:
        """Cancela una reserva pendiente."""
        reserva = self.reserva_dao.obtener_por_id(reserva_id)
        if not reserva:
            raise ValueError(f"No se encontró la reserva con ID {reserva_id}.")
        if reserva.estado != "Pendiente":
            raise ValueError(
                f"La reserva {reserva_id} no se encuentra pendiente. "
                f"Estado actual: {reserva.estado}."
            )

        reserva.estado = "Cancelada"
        self.reserva_dao.actualizar()
        return reserva

    def procesar_caducidades(self) -> int:
        """
        SUP-05: Revisa y caduca las reservas que superen las 48 horas pendientes.
        Retorna la cantidad de reservas caducadas.
        """
        limite_tiempo = datetime.now() - timedelta(hours=self.HORAS_CADUCIDAD_DEFAULT)
        reservas_vencidas = self.session.query(Reserva).filter(
            Reserva.estado == "Pendiente",
            Reserva.fecha_reserva <= limite_tiempo
        ).all()

        cant_caducadas = 0
        for reserva in reservas_vencidas:
            reserva.estado = "Caducada"
            cant_caducadas += 1

        if cant_caducadas > 0:
            self.session.commit()

        return cant_caducadas