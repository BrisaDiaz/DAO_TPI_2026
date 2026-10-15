"""
Servicio de Préstamos - Lógica de negocio y validaciones.

Orquesta el proceso de alta de préstamos (locales e interbibliotecarios),
devoluciones y todas las reglas de negocio obligatorias (RN-01 a RN-05).
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from api.models import Prestamo, Ejemplar, Socio, Sede
from api.dao.prestamo_dao import PrestamoDAO
from api.dao.ejemplar_dao import EjemplarDAO
from api.dao.socio_dao import SocioDAO
from api.dao.sede_dao import SedeDAO
from api.dao.multa_dao import MultaDAO
from api.services.multa_service import MultaService
from api.services.logistica_service import LogisticaService


class PrestamoService:
    """Servicio de negocio para gestión integral de préstamos."""

    DIAS_PRESTAMO_DEFAULT = 15  # Días por defecto para la devolución

    def __init__(self, session: Session):
        self.session = session
        self.prestamo_dao = PrestamoDAO(session)
        self.ejemplar_dao = EjemplarDAO(session)
        self.socio_dao = SocioDAO(session)
        self.sede_dao = SedeDAO(session)
        self.multa_dao = MultaDAO(session)
        self.multa_service = MultaService(session)
        self.logistica_service = LogisticaService(session)

    # ─────────────────────────────────────────────────────────────────────────
    # Alta de Préstamo
    # ─────────────────────────────────────────────────────────────────────────
    def registrar_prestamo(
        self,
        socio_id: int,
        ejemplar_id: int,
        sede_origen_id: int,
        sede_destino_id: int | None = None,
        dias_prestamo: int | None = None,
    ) -> Prestamo:
        """
        Registra un nuevo préstamo validando todas las reglas de negocio.

        Args:
            socio_id: ID del socio solicitante.
            ejemplar_id: ID del ejemplar físico a prestar.
            sede_origen_id: ID de la sede donde se procesa el préstamo.
            sede_destino_id: ID de la sede destino (None = préstamo local).
            dias_prestamo: Días para la devolución (default: 15).

        Returns:
            El préstamo creado.

        Raises:
            ValueError: Si alguna regla de negocio no se cumple.
        """
        socio = self.socio_dao.obtener_por_id(socio_id)
        ejemplar = self.ejemplar_dao.obtener_por_id(ejemplar_id)
        sede_origen = self.sede_dao.obtener_por_id(sede_origen_id)

        # ── Validaciones de negocio ──────────────────────────────────────
        if not socio:
            raise ValueError(f"No se encontró el socio con ID {socio_id}.")
        if not ejemplar:
            raise ValueError(f"No se encontró el ejemplar con ID {ejemplar_id}.")
        if not sede_origen:
            raise ValueError(f"No se encontró la sede con ID {sede_origen_id}.")

        # RN-04: Sede origen activa
        if sede_origen.estado != "activo":
            raise ValueError(
                f"La sede '{sede_origen.direccion}' se encuentra dada de baja. "
                "No se permiten operaciones en sedes inactivas."
            )

        # RN-02: Socio habilitado (sin multas pendientes ni préstamos vencidos)
        if socio.activo == 0:
            raise ValueError(
                f"El socio '{socio.nombre} {socio.apellido}' se encuentra inhabilitado. "
                "Debe regularizar sus multas pendientes antes de solicitar un préstamo."
            )

        multas_pendientes = self.multa_dao.obtener_pendientes_por_socio(socio_id)
        if multas_pendientes:
            raise ValueError(
                f"El socio '{socio.nombre} {socio.apellido}' posee "
                f"{len(multas_pendientes)} multa(s) pendiente(s) de pago."
            )

        # RN-01: Ejemplar disponible
        if ejemplar.estado_fisico != "Disponible":
            raise ValueError(
                f"El ejemplar '{ejemplar.codigo_inventario}' no se encuentra disponible. "
                f"Estado actual: {ejemplar.estado_fisico}."
            )

        # RN-03: Pertenencia de sede (préstamo local)
        es_interbibliotecario = (
            sede_destino_id is not None and sede_destino_id != sede_origen_id
        )
        if not es_interbibliotecario and ejemplar.sede_id != sede_origen_id:
            raise ValueError(
                "Un préstamo local solo puede realizarse con ejemplares pertenecientes "
                f"a la misma sede. El ejemplar pertenece a la sede ID {ejemplar.sede_id}."
            )

        # RN-04: Sede destino activa (si es interbibliotecario)
        if es_interbibliotecario:
            sede_destino = self.sede_dao.obtener_por_id(sede_destino_id)
            if not sede_destino:
                raise ValueError(f"No se encontró la sede destino con ID {sede_destino_id}.")
            if sede_destino.estado != "activo":
                raise ValueError(
                    f"La sede destino '{sede_destino.direccion}' se encuentra dada de baja."
                )

        # ── Crear el préstamo ────────────────────────────────────────────
        dias = dias_prestamo or self.DIAS_PRESTAMO_DEFAULT
        prestamo = Prestamo(
            socio_id=socio_id,
            ejemplar_id=ejemplar_id,
            sede_origen_id=sede_origen_id,
            sede_destino_id=sede_destino_id if es_interbibliotecario else None,
            fecha_prestamo=date.today(),
            fecha_devolucion_estimada=date.today() + timedelta(days=dias),
            estado="Activo",
        )
        self.prestamo_dao.crear(prestamo)

        # Actualizar el estado del ejemplar
        ejemplar.estado_fisico = "Prestado"
        self.session.commit()

        # Si es interbibliotecario, generar el remito automáticamente
        if es_interbibliotecario:
            codigo_remito = f"REM-{date.today().year}-{prestamo.id:04d}"
            self.logistica_service.crear_remito(prestamo, codigo_remito)

        return prestamo

    # ─────────────────────────────────────────────────────────────────────────
    # Devolución de Préstamo
    # ─────────────────────────────────────────────────────────────────────────
    def registrar_devolucion(
        self,
        prestamo_id: int,
        estado_fisico_ejemplar: str = "Disponible",
        tipo_estrategia_multa: str = "estandar",
    ) -> Prestamo:
        """
        Registra la devolución de un préstamo.
        Si hay retraso, genera una multa automáticamente usando la estrategia indicada.
        Actualiza el estado del ejemplar según su condición física al momento de la devolución.

        Args:
            prestamo_id: ID del préstamo a devolver.
            estado_fisico_ejemplar: Estado físico del ejemplar devuelto.
            tipo_estrategia_multa: Estrategia de cálculo de multa ('estandar', 'estudiante', etc.)

        Returns:
            El préstamo actualizado.
        """
        prestamo = self.prestamo_dao.obtener_por_id(prestamo_id)
        if not prestamo:
            raise ValueError(f"No se encontró el préstamo con ID {prestamo_id}.")
        if prestamo.estado != "Activo":
            raise ValueError(
                f"El préstamo {prestamo_id} no se encuentra activo. "
                f"Estado actual: {prestamo.estado}."
            )

        # Registrar la devolución
        prestamo.fecha_devolucion_real = date.today()
        prestamo.estado = "Devuelto"

        # Actualizar el estado físico del ejemplar devuelto
        ejemplar = self.ejemplar_dao.obtener_por_id(prestamo.ejemplar_id)
        if ejemplar:
            ejemplar.estado_fisico = estado_fisico_ejemplar

        self.session.commit()

        # SUP-01: Generar multa automáticamente si hay retraso
        if prestamo.fecha_devolucion_real > prestamo.fecha_devolucion_estimada:
            multa = self.multa_service.generar_multa(prestamo, tipo_estrategia_multa)
            if multa:
                # Inhabilitación automática del socio por deuda
                socio = self.socio_dao.obtener_por_id(prestamo.socio_id)
                if socio:
                    socio.activo = 0
                    self.session.commit()

        return prestamo
