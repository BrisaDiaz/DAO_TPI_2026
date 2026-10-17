"""
Tests para el Servicio de Reservas y Supuestos del Dominio (SUP-04 a SUP-06).
Valida la creación de reservas, límites de préstamos simultáneos, stock agotado
y caducidad automática por tiempo.
"""
import pytest
from datetime import datetime, timedelta, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.database import Base
from api.models import Sede, Socio, Libro, Ejemplar, Prestamo, Reserva
from api.services.reserva_service import ReservaService


@pytest.fixture
def session():
    """Crea una base de datos en memoria para cada test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def datos_reservas(session):
    """Carga datos iniciales para testear reservas."""
    sede_a = Sede(direccion="Sede Central", contacto="011-4444", horarios="9-18", estado="activo")
    sede_inactiva = Sede(direccion="Sede Cerrada", contacto="011-5555", horarios="-", estado="baja")
    session.add_all([sede_a, sede_inactiva])
    session.commit()

    socio_ok = Socio(
        numero_socio="SOC-200", documento="50000200", nombre="Lucía", apellido="Fernández",
        email="lucia@mail.com", telefono="351-0200", activo=1
    )
    socio_inhabilitado = Socio(
        numero_socio="SOC-201", documento="50000201", nombre="Marcos", apellido="Pérez",
        email="marcos@mail.com", telefono="351-0201", activo=0
    )
    session.add_all([socio_ok, socio_inhabilitado])
    session.commit()

    libro = Libro(isbn="978-888-777-666-5", titulo="Patrones de Diseño", editorial="Ed. O'Reilly", anio=2021)
    session.add(libro)
    session.commit()

    return {
        "sede_a": sede_a,
        "sede_inactiva": sede_inactiva,
        "socio_ok": socio_ok,
        "socio_inhabilitado": socio_inhabilitado,
        "libro": libro,
    }


class TestReservaService:
    """Tests para las validaciones y lógica de negocio del servicio de reservas."""

    def test_crear_reserva_exitosa(self, session, datos_reservas):
        """Una reserva es exitosa si el stock disponible en la sede es cero y el socio está habilitado."""
        d = datos_reservas
        service = ReservaService(session)

        reserva = service.crear_reserva(
            socio_id=d["socio_ok"].id,
            libro_id=d["libro"].id,
            sede_id=d["sede_a"].id,
        )

        assert reserva is not None
        assert reserva.estado == "Pendiente"
        assert reserva.socio_id == d["socio_ok"].id

    def test_sup06_condicion_stock_disponible(self, session, datos_reservas):
        """SUP-06: No se puede reservar si existen ejemplares físicos con estado 'Disponible' en la sede."""
        d = datos_reservas
        service = ReservaService(session)

        ejemplar = Ejemplar(
            codigo_inventario="EJ-RES-01",
            estado_fisico="Disponible",
            libro_id=d["libro"].id,
            sede_id=d["sede_a"].id,
        )
        session.add(ejemplar)
        session.commit()

        with pytest.raises(ValueError, match="existen.*ejemplar.*disponible"):
            service.crear_reserva(
                socio_id=d["socio_ok"].id,
                libro_id=d["libro"].id,
                sede_id=d["sede_a"].id,
            )

    def test_sup04_limite_prestamos_simultaneos(self, session, datos_reservas):
        """SUP-04: El socio no puede superar el límite máximo de préstamos activos (3)."""
        d = datos_reservas
        service = ReservaService(session)

        for i in range(3):
            ej = Ejemplar(
                codigo_inventario=f"EJ-LIM-{i}",
                estado_fisico="Prestado",
                libro_id=d["libro"].id,
                sede_id=d["sede_a"].id,
            )
            session.add(ej)
            session.commit()

            prestamo = Prestamo(
                socio_id=d["socio_ok"].id,
                ejemplar_id=ej.id,
                sede_origen_id=d["sede_a"].id,
                fecha_devolucion_estimada=date.today() + timedelta(days=15),
                estado="Activo",
            )
            session.add(prestamo)
        session.commit()

        with pytest.raises(ValueError, match="alcanzó el límite máximo"):
            service.crear_reserva(
                socio_id=d["socio_ok"].id,
                libro_id=d["libro"].id,
                sede_id=d["sede_a"].id,
            )

    def test_socio_inhabilitado_no_puede_reservar(self, session, datos_reservas):
        """RN-02: Un socio inhabilitado no puede generar reservas."""
        d = datos_reservas
        service = ReservaService(session)

        with pytest.raises(ValueError, match="inhabilitado"):
            service.crear_reserva(
                socio_id=d["socio_inhabilitado"].id,
                libro_id=d["libro"].id,
                sede_id=d["sede_a"].id,
            )

    def test_sede_inactiva_no_permite_reservar(self, session, datos_reservas):
        """RN-04: No se puede reservar en una sede dada de baja."""
        d = datos_reservas
        service = ReservaService(session)

        with pytest.raises(ValueError, match="dada de baja"):
            service.crear_reserva(
                socio_id=d["socio_ok"].id,
                libro_id=d["libro"].id,
                sede_id=d["sede_inactiva"].id,
            )

    def test_cancelar_reserva(self, session, datos_reservas):
        """Permite cancelar una reserva pendiente de forma exitosa."""
        d = datos_reservas
        service = ReservaService(session)

        reserva = service.crear_reserva(
            socio_id=d["socio_ok"].id,
            libro_id=d["libro"].id,
            sede_id=d["sede_a"].id,
        )

        reserva_cancelada = service.cancelar_reserva(reserva.id)
        assert reserva_cancelada.estado == "Cancelada"

    def test_sup05_caducidad_automatica_reservas(self, session, datos_reservas):
        """SUP-05: Una reserva pendiente caduca automáticamente tras transcurrir 48 horas."""
        d = datos_reservas
        service = ReservaService(session)

        reserva_vencida = Reserva(
            socio_id=d["socio_ok"].id,
            libro_id=d["libro"].id,
            sede_id=d["sede_a"].id,
            fecha_reserva=datetime.now() - timedelta(hours=50),
            estado="Pendiente"
        )
        session.add(reserva_vencida)
        session.commit()

        caducadas = service.procesar_caducidades()
        
        assert caducadas == 1
        session.refresh(reserva_vencida)
        assert reserva_vencida.estado == "Caducada"