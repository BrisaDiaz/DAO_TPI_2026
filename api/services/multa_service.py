"""
Servicio de Multas - Patrón Strategy.

Implementa diferentes estrategias intercambiables para el cálculo de multas
por retraso en la devolución de préstamos, según el tipo de socio o política vigente.
"""
from abc import ABC, abstractmethod
from datetime import date

from sqlalchemy.orm import Session

from api.models import Multa, Prestamo, Socio
from api.dao.multa_dao import MultaDAO


# ─────────────────────────────────────────────────────────────────────────────
# Patrón Strategy: Interfaz y Estrategias Concretas
# ─────────────────────────────────────────────────────────────────────────────
class EstrategiaMulta(ABC):
    """Interfaz abstracta para estrategias de cálculo de multas."""

    @abstractmethod
    def calcular_multa(self, dias_retraso: int) -> float:
        pass


class MultaEstandar(EstrategiaMulta):
    """Tarifa fija estándar de $150 por día de retraso."""

    def calcular_multa(self, dias_retraso: int) -> float:
        tarifa_diaria = 150.0
        return dias_retraso * tarifa_diaria


class MultaReducidaEstudiante(EstrategiaMulta):
    """Tarifa reducida de $75 por día para socios estudiantes."""

    def calcular_multa(self, dias_retraso: int) -> float:
        tarifa_reducida = 75.0
        return dias_retraso * tarifa_reducida


class SinMultaPromocional(EstrategiaMulta):
    """Exención total de multa (promociones o condonaciones)."""

    def calcular_multa(self, dias_retraso: int) -> float:
        return 0.0


# Diccionario de estrategias (selección en tiempo de ejecución, alineado a la cátedra)
ESTRATEGIAS = {
    "estandar": MultaEstandar(),
    "estudiante": MultaReducidaEstudiante(),
    "promocional": SinMultaPromocional(),
}


# ─────────────────────────────────────────────────────────────────────────────
# Contexto del patrón Strategy + Servicio de negocio
# ─────────────────────────────────────────────────────────────────────────────
class MultaService:
    """Servicio de negocio para gestión de multas con estrategia intercambiable."""

    def __init__(self, session: Session, estrategia: EstrategiaMulta | None = None):
        self.session = session
        self.multa_dao = MultaDAO(session)
        self.estrategia = estrategia or MultaEstandar()

    def cambiar_estrategia(self, nueva_estrategia: EstrategiaMulta) -> None:
        """Permite cambiar la estrategia de cálculo en tiempo de ejecución."""
        self.estrategia = nueva_estrategia

    def calcular_dias_retraso(self, prestamo: Prestamo) -> int:
        """Calcula los días de retraso de un préstamo respecto a la fecha estimada."""
        fecha_ref = prestamo.fecha_devolucion_real or date.today()
        delta = (fecha_ref - prestamo.fecha_devolucion_estimada).days
        return max(0, delta)

    def generar_multa(self, prestamo: Prestamo, tipo_estrategia: str = "estandar") -> Multa | None:
        """
        Genera una multa por retraso en la devolución de un préstamo.
        Selecciona la estrategia de cálculo según el tipo recibido.
        Retorna None si no hay días de retraso.
        """
        dias_retraso = self.calcular_dias_retraso(prestamo)
        if dias_retraso <= 0:
            return None

        # Seleccionar estrategia del diccionario o usar la configurada
        estrategia = ESTRATEGIAS.get(tipo_estrategia, self.estrategia)
        monto = estrategia.calcular_multa(dias_retraso)

        if monto <= 0:
            return None

        multa = Multa(
            monto=monto,
            estado="Pendiente",
            prestamo_id=prestamo.id,
            socio_id=prestamo.socio_id,
        )
        return self.multa_dao.crear(multa)

    def registrar_pago(self, multa_id: int) -> Multa:
        """Registra el pago de una multa y reactiva al socio si no tiene más deudas."""
        multa = self.multa_dao.obtener_por_id(multa_id)
        if not multa:
            raise ValueError(f"No se encontró la multa con ID {multa_id}.")
        if multa.estado != "Pendiente":
            raise ValueError(f"La multa {multa_id} no se encuentra pendiente de pago.")

        multa.estado = "Pagada"
        self.multa_dao.actualizar()

        # Verificar si el socio puede ser reactivado
        self._verificar_reactivacion_socio(multa.socio_id)
        return multa

    def condonar_multa(self, multa_id: int) -> Multa:
        """Condona una multa pendiente y verifica la reactivación del socio."""
        multa = self.multa_dao.obtener_por_id(multa_id)
        if not multa:
            raise ValueError(f"No se encontró la multa con ID {multa_id}.")

        multa.estado = "Condonada"
        self.multa_dao.actualizar()

        self._verificar_reactivacion_socio(multa.socio_id)
        return multa

    def _verificar_reactivacion_socio(self, socio_id: int) -> None:
        """Si el socio no tiene más multas pendientes, lo reactiva automáticamente."""
        pendientes = self.multa_dao.obtener_pendientes_por_socio(socio_id)
        if not pendientes:
            socio = self.session.query(Socio).filter(Socio.id == socio_id).first()
            if socio and socio.activo == 0:
                socio.activo = 1
                self.session.commit()

    def generar_multa_por_dano_o_extravio(self, prestamo: Prestamo, monto_fijo: float = 5000.0) -> Multa:
        """
        SUP-07: Genera automáticamente un cargo por reposición económica 
        debido a la devolución de un ejemplar en estado 'Dañado' o 'Extraviado'.
        """
        multa = Multa(
            monto=monto_fijo,
            estado="Pendiente",
            prestamo_id=prestamo.id,
            socio_id=prestamo.socio_id,
        )
        return self.multa_dao.crear(multa)
