"""
Servicio de Notificaciones - Patrón Observer.

Implementa el patrón Observer alineado a las diapositivas de la cátedra (UTN FRC):
- Subject: Mantiene la lista de observadores (_observers) y provee attach(), detach() y notify().
- Observer (ABC): Interfaz abstracta con el método update().
- DisponibilidadEjemplarSubject: Sujeto concreto que observa el cambio de estado de un ejemplar.
- SocioObserver: Observador concreto que representa a un socio con reserva pendiente.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from api.models import Ejemplar
from api.dao.reserva_dao import ReservaDAO


# ─────────────────────────────────────────────────────────────────────────────
# Patrón Observer: Clases Base (según plantilla de la cátedra DAO UTN FRC)
# ─────────────────────────────────────────────────────────────────────────────
class Observer(ABC):
    """Interfaz para recibir actualizaciones del sujeto observable."""

    @abstractmethod
    def update(self) -> None:
        """
        Todas las clases derivadas deben definir este método
        para poder recibir notificaciones de actualización.
        """
        pass


class Subject:
    """Mantiene la lista de observadores y notifica cambios."""

    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        """Suscribe un observador a la lista de notificaciones."""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """Desuscribe un observador de la lista de notificaciones."""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self) -> None:
        """Notifica cambios a todos los observadores suscriptos."""
        for observer in self._observers:
            observer.update()


# ─────────────────────────────────────────────────────────────────────────────
# Sujeto y Observador Concretos del Dominio de Biblioteca
# ─────────────────────────────────────────────────────────────────────────────
class SocioObserver(Observer):
    """
    Observador concreto que representa a un socio en lista de espera (Reserva)
    aguardando la disponibilidad de un ejemplar.
    """

    def __init__(
        self,
        nombre: str,
        email: str,
        numero_socio: str = "",
        reserva_id: Optional[int] = None,
        titulo_libro: str = "",
        codigo_ejemplar: str = "",
        sede_direccion: str = "",
    ):
        super().__init__()
        self.nombre = nombre
        self.email = email
        self.numero_socio = numero_socio
        self.reserva_id = reserva_id
        self.titulo_libro = titulo_libro
        self.codigo_ejemplar = codigo_ejemplar
        self.sede_direccion = sede_direccion
        self.notificado: bool = False
        self.ultimo_mensaje: str = ""
        self.mensajes_recibidos: List[str] = []

    def update(self) -> None:
        """Recibe la notificación de disponibilidad del ejemplar."""
        sede_info = f" en '{self.sede_direccion}'" if self.sede_direccion else ""
        ejemplar_info = f" (Ejemplar: {self.codigo_ejemplar})" if self.codigo_ejemplar else ""
        mensaje = (
            f"Notificación enviada a {self.nombre} ({self.email}): "
            f"El libro '{self.titulo_libro}'{ejemplar_info} "
            f"ya se encuentra disponible{sede_info} para retiro."
        )
        self.notificado = True
        self.ultimo_mensaje = mensaje
        self.mensajes_recibidos.append(mensaje)
        print(mensaje)


class DisponibilidadEjemplarSubject(Subject):
    """
    Sujeto concreto observable que monitorea el estado físico de un ejemplar.
    Cuando su estado cambia a 'Disponible', notifica automáticamente a todos
    los socios suscriptos.
    """

    def __init__(
        self,
        codigo_inventario: str,
        titulo_libro: str,
        sede_direccion: str = "",
        estado_inicial: str = "Prestado",
    ):
        super().__init__()
        self.codigo_inventario = codigo_inventario
        self.titulo_libro = titulo_libro
        self.sede_direccion = sede_direccion
        self._estado = estado_inicial

    @property
    def estado(self) -> str:
        return self._estado

    def cambiar_estado(self, nuevo_estado: str) -> None:
        """
        Actualiza el estado del ejemplar y, si pasa a 'Disponible',
        dispara la notificación a todos los observadores suscriptos.
        """
        self._estado = nuevo_estado
        if self._estado == "Disponible":
            self.notify()


# Alias de compatibilidad con la documentación de Patrones.md
EjemplarObservable = DisponibilidadEjemplarSubject


# ─────────────────────────────────────────────────────────────────────────────
# Servicio Orquestador de Notificaciones
# ─────────────────────────────────────────────────────────────────────────────
class NotificacionService:
    """
    Orquesta la suscripción de socios con reservas pendientes y el disparo
    del patrón Observer cuando un ejemplar es devuelto y queda disponible.
    """

    _historial_notificaciones: List[Dict[str, Any]] = []

    def __init__(self, session: Session):
        self.session = session
        self.reserva_dao = ReservaDAO(session)

    def notificar_disponibilidad_ejemplar(self, ejemplar: Ejemplar) -> List[Dict[str, Any]]:
        """
        Busca las reservas pendientes asociadas al libro y sede del ejemplar devuelto,
        suscribe a cada socio como SocioObserver en DisponibilidadEjemplarSubject y,
        si el ejemplar está 'Disponible', ejecuta el cambio de estado que dispara notify().

        Retorna la lista de notificaciones emitidas en esta operación.
        """
        if not ejemplar or ejemplar.estado_fisico != "Disponible":
            return []

        reservas_pendientes = self.reserva_dao.obtener_pendientes_por_libro_y_sede(
            libro_id=ejemplar.libro_id,
            sede_id=ejemplar.sede_id,
        )
        if not reservas_pendientes:
            return []

        titulo_libro = ejemplar.libro.titulo if ejemplar.libro else f"Libro ID {ejemplar.libro_id}"
        sede_direccion = ejemplar.sede.direccion if ejemplar.sede else f"Sede ID {ejemplar.sede_id}"
        codigo_inv = ejemplar.codigo_inventario or f"ID-{ejemplar.id}"

        # 1. Crear el Sujeto Observable (Subject)
        sujeto = DisponibilidadEjemplarSubject(
            codigo_inventario=codigo_inv,
            titulo_libro=titulo_libro,
            sede_direccion=sede_direccion,
            estado_inicial="Prestado",
        )

        # 2. Crear y suscribir (attach) un Observador (SocioObserver) por cada reserva pendiente
        observadores: List[SocioObserver] = []
        for reserva in reservas_pendientes:
            socio = reserva.socio
            if not socio:
                continue
            obs = SocioObserver(
                nombre=f"{socio.nombre} {socio.apellido}",
                email=socio.email,
                numero_socio=socio.numero_socio,
                reserva_id=reserva.id,
                titulo_libro=titulo_libro,
                codigo_ejemplar=codigo_inv,
                sede_direccion=sede_direccion,
            )
            sujeto.attach(obs)
            observadores.append(obs)

        # 3. Cambiar el estado a 'Disponible' -> dispara sujeto.notify() -> obs.update()
        sujeto.cambiar_estado("Disponible")

        # Iniciar el plazo de caducidad (SUP-05): 48 horas hábiles desde la notificación.
        # Si la reserva ya había sido notificada se conserva la fecha original.
        momento_notificacion = datetime.now()
        reservas_por_id = {r.id: r for r in reservas_pendientes}
        for obs in observadores:
            reserva = reservas_por_id.get(obs.reserva_id)
            if obs.notificado and reserva and reserva.fecha_notificacion is None:
                reserva.fecha_notificacion = momento_notificacion
        self.session.commit()

        # 4. Registrar las notificaciones emitidas para consulta en UI y auditoría
        emitidas: List[Dict[str, Any]] = []
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for obs in observadores:
            if obs.notificado:
                registro = {
                    "fecha": ahora,
                    "reserva_id": obs.reserva_id,
                    "socio": obs.nombre,
                    "numero_socio": obs.numero_socio,
                    "email": obs.email,
                    "libro": obs.titulo_libro,
                    "ejemplar": obs.codigo_ejemplar,
                    "sede": obs.sede_direccion,
                    "mensaje": obs.ultimo_mensaje,
                }
                emitidas.append(registro)
                self._historial_notificaciones.append(registro)

        return emitidas

    @classmethod
    def obtener_historial(cls) -> List[Dict[str, Any]]:
        """Retorna el historial completo de notificaciones emitidas en la sesión."""
        return list(cls._historial_notificaciones)

    @classmethod
    def limpiar_historial(cls) -> None:
        """Limpia el historial de notificaciones en memoria (útil para pruebas unitarias)."""
        cls._historial_notificaciones.clear()
