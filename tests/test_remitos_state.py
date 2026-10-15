"""
Tests para el Patrón State - Ciclo de vida del Remito.
Valida las transiciones: Empaquetado -> Despachado -> Recibido
y el manejo de incidencias.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.database import Base
from api.models import Sede, Socio, Libro, Ejemplar, Prestamo, Remito
from api.services.logistica_service import (
    LogisticaService, RemitoContexto,
    EstadoEmpaquetado, EstadoDespachado, EstadoRecibido, EstadoConIncidencias,
)


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
def datos_base(session):
    """Carga los datos mínimos necesarios para testear remitos."""
    sede_origen = Sede(direccion="Sede Norte", contacto="011-1111", horarios="9-18", estado="activo")
    sede_destino = Sede(direccion="Sede Sur", contacto="011-2222", horarios="9-18", estado="activo")
    session.add_all([sede_origen, sede_destino])
    session.commit()

    socio = Socio(numero_socio="SOC-001", documento="30000001", nombre="Ana", apellido="Gómez",
                  email="ana@mail.com", telefono="351-0001")
    session.add(socio)
    session.commit()

    libro = Libro(isbn="978-111-222-333-4", titulo="Arquitectura de Software", editorial="Ed. UTN", anio=2024)
    session.add(libro)
    session.commit()

    ejemplar = Ejemplar(codigo_inventario="EJ-001", estado_fisico="Disponible",
                        libro_id=libro.id, sede_id=sede_origen.id)
    session.add(ejemplar)
    session.commit()

    return {
        "sede_origen": sede_origen,
        "sede_destino": sede_destino,
        "socio": socio,
        "libro": libro,
        "ejemplar": ejemplar,
    }


@pytest.fixture
def prestamo_inter(session, datos_base):
    """Crea un préstamo interbibliotecario para asociar remitos."""
    from datetime import date, timedelta
    prestamo = Prestamo(
        socio_id=datos_base["socio"].id,
        ejemplar_id=datos_base["ejemplar"].id,
        sede_origen_id=datos_base["sede_origen"].id,
        sede_destino_id=datos_base["sede_destino"].id,
        fecha_devolucion_estimada=date.today() + timedelta(days=15),
        estado="Activo",
    )
    session.add(prestamo)
    session.commit()
    return prestamo


# ─────────────────────────────────────────────────────────────────────────────
# Tests del Patrón State
# ─────────────────────────────────────────────────────────────────────────────
class TestStateRemito:
    """Tests para las transiciones de estado del remito."""

    def test_estado_inicial_empaquetado(self, session, prestamo_inter):
        """Un remito nuevo debe iniciar en estado Empaquetado."""
        service = LogisticaService(session)
        remito = service.crear_remito(prestamo_inter, "REM-TEST-001")
        assert remito.estado == "Empaquetado"

    def test_transicion_empaquetado_a_despachado(self, session, prestamo_inter):
        """Avanzar desde Empaquetado debe llevar a Despachado."""
        service = LogisticaService(session)
        remito = service.crear_remito(prestamo_inter, "REM-TEST-002")
        service.avanzar_estado(remito.id)
        assert remito.estado == "Despachado"

    def test_transicion_despachado_a_recibido(self, session, prestamo_inter):
        """Avanzar desde Despachado debe llevar a Recibido."""
        service = LogisticaService(session)
        remito = service.crear_remito(prestamo_inter, "REM-TEST-003")
        service.avanzar_estado(remito.id)  # -> Despachado
        service.avanzar_estado(remito.id)  # -> Recibido
        assert remito.estado == "Recibido"

    def test_ciclo_completo(self, session, prestamo_inter):
        """El ciclo completo debe ser Empaquetado -> Despachado -> Recibido."""
        service = LogisticaService(session)
        remito = service.crear_remito(prestamo_inter, "REM-TEST-004")

        assert remito.estado == "Empaquetado"
        service.avanzar_estado(remito.id)
        assert remito.estado == "Despachado"
        service.avanzar_estado(remito.id)
        assert remito.estado == "Recibido"

    def test_no_avanzar_desde_recibido(self, session, prestamo_inter):
        """Intentar avanzar desde Recibido debe lanzar un error."""
        service = LogisticaService(session)
        remito = service.crear_remito(prestamo_inter, "REM-TEST-005")
        service.avanzar_estado(remito.id)  # -> Despachado
        service.avanzar_estado(remito.id)  # -> Recibido

        with pytest.raises(ValueError, match="ya fue recibido"):
            service.avanzar_estado(remito.id)

    def test_incidencia_en_transito(self, session, prestamo_inter):
        """Se puede reportar incidencia cuando el remito está Despachado."""
        service = LogisticaService(session)
        remito = service.crear_remito(prestamo_inter, "REM-TEST-006")
        service.avanzar_estado(remito.id)  # -> Despachado
        service.reportar_incidencia(remito.id)
        assert remito.estado == "Con incidencias"

    def test_resolver_incidencia(self, session, prestamo_inter):
        """Desde Con incidencias se puede avanzar a Recibido."""
        service = LogisticaService(session)
        remito = service.crear_remito(prestamo_inter, "REM-TEST-007")
        service.avanzar_estado(remito.id)       # -> Despachado
        service.reportar_incidencia(remito.id)   # -> Con incidencias
        service.avanzar_estado(remito.id)        # -> Recibido
        assert remito.estado == "Recibido"

    def test_no_incidencia_desde_empaquetado(self, session, prestamo_inter):
        """No se puede reportar incidencia desde el estado Empaquetado."""
        service = LogisticaService(session)
        remito = service.crear_remito(prestamo_inter, "REM-TEST-008")

        with pytest.raises(ValueError, match="No se puede reportar incidencia"):
            service.reportar_incidencia(remito.id)

    def test_contexto_reconstruye_estado_desde_bd(self, session, prestamo_inter):
        """El contexto debe reconstruir correctamente el estado desde la BD."""
        service = LogisticaService(session)
        remito = service.crear_remito(prestamo_inter, "REM-TEST-009")
        service.avanzar_estado(remito.id)  # -> Despachado

        # Simular reconstrucción desde la BD
        contexto = RemitoContexto(remito)
        assert contexto.obtener_estado() == "Despachado"
