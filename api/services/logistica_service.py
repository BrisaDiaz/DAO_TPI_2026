"""
Servicio de Logística - Patrón State.

Implementa el ciclo de vida del remito interbibliotecario mediante el patrón State.
Cada estado del remito es una clase independiente que encapsula las transiciones
permitidas: Empaquetado -> Despachado -> Recibido (con manejo de incidencias).
"""
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from api.models import Remito, Prestamo
from api.dao.remito_dao import RemitoDAO


# ─────────────────────────────────────────────────────────────────────────────
# Patrón State: Interfaz y Estados Concretos del Remito
# ─────────────────────────────────────────────────────────────────────────────
class EstadoRemito(ABC):
    """Interfaz abstracta para los estados del ciclo de vida del remito."""

    @abstractmethod
    def siguiente(self, contexto: "RemitoContexto") -> None:
        """Ejecuta la transición al siguiente estado."""
        pass

    @abstractmethod
    def obtener_nombre(self) -> str:
        """Retorna el nombre del estado actual."""
        pass

    def reportar_incidencia(self, contexto: "RemitoContexto") -> None:
        """Reporta una incidencia en el trayecto (disponible en ciertos estados)."""
        raise ValueError(
            f"No se puede reportar incidencia en el estado '{self.obtener_nombre()}'."
        )


class EstadoEmpaquetado(EstadoRemito):
    """Estado inicial: el material fue empaquetado en la sede de origen."""

    def siguiente(self, contexto: "RemitoContexto") -> None:
        print(f"Remito {contexto.remito.codigo_remito}: Empaquetado -> Despachado.")
        contexto.remito.estado = "Despachado"
        contexto.estado_actual = EstadoDespachado()

    def obtener_nombre(self) -> str:
        return "Empaquetado"


class EstadoDespachado(EstadoRemito):
    """Estado intermedio: el material se encuentra en tránsito entre sedes."""

    def siguiente(self, contexto: "RemitoContexto") -> None:
        print(f"Remito {contexto.remito.codigo_remito}: Despachado -> Recibido.")
        contexto.remito.estado = "Recibido"
        contexto.estado_actual = EstadoRecibido()

    def obtener_nombre(self) -> str:
        return "Despachado"

    def reportar_incidencia(self, contexto: "RemitoContexto") -> None:
        """Permite reportar incidencia mientras el remito está en tránsito."""
        print(f"Remito {contexto.remito.codigo_remito}: Incidencia reportada en tránsito.")
        contexto.remito.estado = "Con incidencias"
        contexto.estado_actual = EstadoConIncidencias()


class EstadoRecibido(EstadoRemito):
    """Estado final: el material fue recibido en la sede de destino."""

    def siguiente(self, contexto: "RemitoContexto") -> None:
        raise ValueError(
            f"El remito {contexto.remito.codigo_remito} ya fue recibido. "
            "No hay más transiciones posibles."
        )

    def obtener_nombre(self) -> str:
        return "Recibido"


class EstadoConIncidencias(EstadoRemito):
    """Estado excepcional: se reportó un problema durante el tránsito."""

    def siguiente(self, contexto: "RemitoContexto") -> None:
        """Permite retomar el flujo desde la incidencia hacia Recibido."""
        print(f"Remito {contexto.remito.codigo_remito}: Incidencia resuelta -> Recibido.")
        contexto.remito.estado = "Recibido"
        contexto.estado_actual = EstadoRecibido()

    def obtener_nombre(self) -> str:
        return "Con incidencias"


# Mapeo de nombre de estado a clase de estado (para reconstruir desde la BD)
ESTADOS_MAP = {
    "Empaquetado": EstadoEmpaquetado,
    "Despachado": EstadoDespachado,
    "Recibido": EstadoRecibido,
    "Con incidencias": EstadoConIncidencias,
}


# ─────────────────────────────────────────────────────────────────────────────
# Contexto del patrón State
# ─────────────────────────────────────────────────────────────────────────────
class RemitoContexto:
    """
    Contexto del patrón State para el ciclo de vida del remito.
    Envuelve al modelo ORM Remito y delega las transiciones al estado actual.
    """

    def __init__(self, remito: Remito):
        self.remito = remito
        # Reconstruir el estado actual a partir del valor persistido en la BD
        clase_estado = ESTADOS_MAP.get(remito.estado, EstadoEmpaquetado)
        self.estado_actual: EstadoRemito = clase_estado()

    def avanzar(self) -> None:
        """Solicita al estado actual que ejecute la transición al siguiente."""
        self.estado_actual.siguiente(self)

    def reportar_incidencia(self) -> None:
        """Solicita al estado actual que registre una incidencia."""
        self.estado_actual.reportar_incidencia(self)

    def obtener_estado(self) -> str:
        """Retorna el nombre descriptivo del estado actual."""
        return self.estado_actual.obtener_nombre()


# ─────────────────────────────────────────────────────────────────────────────
# Servicio de Logística
# ─────────────────────────────────────────────────────────────────────────────
class LogisticaService:
    """Servicio de negocio para la gestión logística de remitos interbibliotecarios."""

    def __init__(self, session: Session):
        self.session = session
        self.remito_dao = RemitoDAO(session)

    def crear_remito(self, prestamo: Prestamo, codigo_remito: str) -> Remito:
        """
        Genera un nuevo remito para un préstamo interbibliotecario.
        Valida que el préstamo sea efectivamente interbibliotecario.
        """
        if not prestamo.sede_destino_id or prestamo.sede_origen_id == prestamo.sede_destino_id:
            raise ValueError(
                "Solo se pueden generar remitos para préstamos interbibliotecarios "
                "(sede origen ≠ sede destino)."
            )

        existente = self.remito_dao.obtener_por_prestamo(prestamo.id)
        if existente:
            raise ValueError(
                f"El préstamo {prestamo.id} ya tiene un remito asociado: "
                f"{existente.codigo_remito}."
            )

        remito = Remito(
            codigo_remito=codigo_remito,
            estado="Empaquetado",
            prestamo_id=prestamo.id,
        )
        return self.remito_dao.crear(remito)

    def avanzar_estado(self, remito_id: int) -> Remito:
        """
        Avanza el remito al siguiente estado de su ciclo de vida.
        Delega la transición al patrón State.
        """
        remito = self.remito_dao.obtener_por_id(remito_id)
        if not remito:
            raise ValueError(f"No se encontró el remito con ID {remito_id}.")

        contexto = RemitoContexto(remito)
        contexto.avanzar()
        self.remito_dao.actualizar()
        return remito

    def reportar_incidencia(self, remito_id: int) -> Remito:
        """Reporta una incidencia en un remito que se encuentra en tránsito."""
        remito = self.remito_dao.obtener_por_id(remito_id)
        if not remito:
            raise ValueError(f"No se encontró el remito con ID {remito_id}.")

        contexto = RemitoContexto(remito)
        contexto.reportar_incidencia()
        self.remito_dao.actualizar()
        return remito
