"""
Tests para el Patrón Observer - Notificación de Disponibilidad de Ejemplares Reservados.
Valida las clases Subject y Observer alineadas a la cátedra, así como la integración
con PrestamoService y ReservaService al devolver ejemplares con reservas pendientes.
"""
import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.database import Base
from api.models import Sede, Socio, Libro, Ejemplar
from api.services.notificacion_service import (
    Subject,
    Observer,
    SocioObserver,
    DisponibilidadEjemplarSubject,
    NotificacionService,
)
from api.services.prestamo_service import PrestamoService
from api.services.reserva_service import ReservaService


@pytest.fixture
def session():
    """Crea una base de datos en memoria limpia para cada test."""
    NotificacionService.limpiar_historial()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def escenario_reserva(session):
    """Configura una sede, un libro con 1 ejemplar y 3 socios habilitados."""
    sede = Sede(direccion="Sede Centro", contacto="0351-4444", horarios="8-20", estado="activo")
    session.add(sede)
    session.commit()

    socio_prestamo = Socio(
        numero_socio="SOC-301", documento="31000301", nombre="Martín", apellido="Castro",
        email="martin@mail.com", telefono="351-0301", activo=1,
    )
    socio_espera_1 = Socio(
        numero_socio="SOC-302", documento="31000302", nombre="Ana", apellido="Gómez",
        email="ana@mail.com", telefono="351-0302", activo=1,
    )
    socio_espera_2 = Socio(
        numero_socio="SOC-303", documento="31000303", nombre="Carlos", apellido="Ruiz",
        email="carlos@mail.com", telefono="351-0303", activo=1,
    )
    session.add_all([socio_prestamo, socio_espera_1, socio_espera_2])
    session.commit()

    libro = Libro(
        isbn="978-987-654-321-0",
        titulo="Diseño Orientado a Objetos",
        editorial="Ed. UTN",
        anio=2025,
    )
    session.add(libro)
    session.commit()

    ejemplar = Ejemplar(
        codigo_inventario="EJ-OBS-01",
        estado_fisico="Disponible",
        libro_id=libro.id,
        sede_id=sede.id,
    )
    session.add(ejemplar)
    session.commit()

    return {
        "sede": sede,
        "socio_prestamo": socio_prestamo,
        "socio_espera_1": socio_espera_1,
        "socio_espera_2": socio_espera_2,
        "libro": libro,
        "ejemplar": ejemplar,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tests Unitarios de la Estructura del Patrón Observer (Cátedra DAO)
# ─────────────────────────────────────────────────────────────────────────────
class TestPatronObserverUnitario:
    """Valida el funcionamiento puro de Subject, Observer, attach, detach y notify."""

    def test_attach_y_notify_observadores(self):
        """Al cambiar el sujeto a Disponible, todos los observadores suscriptos reciben update()."""
        sujeto = DisponibilidadEjemplarSubject("EJ-999", "Arquitectura de Software", "Sede Centro")
        obs1 = SocioObserver("Ana Gómez", "ana@mail.com", titulo_libro="Arquitectura de Software", codigo_ejemplar="EJ-999")
        obs2 = SocioObserver("Carlos Ruiz", "carlos@mail.com", titulo_libro="Arquitectura de Software", codigo_ejemplar="EJ-999")

        sujeto.attach(obs1)
        sujeto.attach(obs2)

        sujeto.cambiar_estado("Disponible")

        assert obs1.notificado is True
        assert obs2.notificado is True
        assert "Ana Gómez" in obs1.ultimo_mensaje
        assert "Carlos Ruiz" in obs2.ultimo_mensaje

    def test_detach_desuscribe_observador(self):
        """Un observador desuscripto mediante detach() no debe recibir notificaciones."""
        sujeto = DisponibilidadEjemplarSubject("EJ-999", "Arquitectura de Software")
        obs1 = SocioObserver("Ana Gómez", "ana@mail.com")
        obs2 = SocioObserver("Carlos Ruiz", "carlos@mail.com")

        sujeto.attach(obs1)
        sujeto.attach(obs2)
        sujeto.detach(obs1)

        sujeto.cambiar_estado("Disponible")

        assert obs1.notificado is False
        assert obs2.notificado is True

    def test_cambio_a_estado_no_disponible_no_notifica(self):
        """Si el ejemplar pasa a estado 'Dañado' o 'Extraviado', no debe notificar."""
        sujeto = DisponibilidadEjemplarSubject("EJ-999", "Arquitectura de Software")
        obs = SocioObserver("Ana Gómez", "ana@mail.com")
        sujeto.attach(obs)

        sujeto.cambiar_estado("Dañado")

        assert obs.notificado is False
        assert len(obs.mensajes_recibidos) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Tests de Integración: Devolución de Préstamo + Reservas + Observer
# ─────────────────────────────────────────────────────────────────────────────
class TestObserverIntegracionDevolucion:
    """Valida que al devolver un ejemplar se dispare automáticamente el patrón Observer."""

    def test_devolucion_disponible_notifica_socios_con_reserva_pendiente(
        self, session, escenario_reserva
    ):
        """
        Cuando el único ejemplar prestado es devuelto en estado 'Disponible',
        los socios en lista de espera (Reserva Pendiente) son notificados automáticamente.
        """
        d = escenario_reserva
        prestamo_service = PrestamoService(session)
        reserva_service = ReservaService(session)

        # 1. Se presta el único ejemplar -> stock disponible en sede pasa a 0
        prestamo = prestamo_service.registrar_prestamo(
            socio_id=d["socio_prestamo"].id,
            ejemplar_id=d["ejemplar"].id,
            sede_origen_id=d["sede"].id,
        )

        # 2. Dos socios registran reservas pendientes sobre esa obra agotada
        reserva_service.crear_reserva(
            socio_id=d["socio_espera_1"].id,
            libro_id=d["libro"].id,
            sede_id=d["sede"].id,
        )
        reserva_service.crear_reserva(
            socio_id=d["socio_espera_2"].id,
            libro_id=d["libro"].id,
            sede_id=d["sede"].id,
        )

        # 3. Se registra la devolución del ejemplar en estado 'Disponible'
        prestamo_service.registrar_devolucion(
            prestamo_id=prestamo.id,
            estado_fisico_ejemplar="Disponible",
        )

        # 4. Verificar que el patrón Observer notificó a ambos socios
        notificaciones = prestamo_service.ultimas_notificaciones
        assert len(notificaciones) == 2
        emails_notificados = [n["email"] for n in notificaciones]
        assert "ana@mail.com" in emails_notificados
        assert "carlos@mail.com" in emails_notificados

        # Y quedó registrado en el historial global de notificaciones
        historial = NotificacionService.obtener_historial()
        assert len(historial) == 2

    def test_devolucion_danado_no_notifica_reservas(self, session, escenario_reserva):
        """
        Si el ejemplar se devuelve en estado 'Dañado', no queda disponible para préstamo
        y por lo tanto no debe disparar notificaciones a la lista de espera.
        """
        d = escenario_reserva
        prestamo_service = PrestamoService(session)
        reserva_service = ReservaService(session)

        prestamo = prestamo_service.registrar_prestamo(
            socio_id=d["socio_prestamo"].id,
            ejemplar_id=d["ejemplar"].id,
            sede_origen_id=d["sede"].id,
        )

        reserva_service.crear_reserva(
            socio_id=d["socio_espera_1"].id,
            libro_id=d["libro"].id,
            sede_id=d["sede"].id,
        )

        prestamo_service.registrar_devolucion(
            prestamo_id=prestamo.id,
            estado_fisico_ejemplar="Dañado",
        )

        assert len(prestamo_service.ultimas_notificaciones) == 0
        assert len(NotificacionService.obtener_historial()) == 0
