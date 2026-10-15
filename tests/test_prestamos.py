"""
Tests para las Reglas de Negocio de Préstamos (RN-01 a RN-04).
Valida las restricciones obligatorias del sistema antes de autorizar un préstamo.
"""
import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.database import Base
from api.models import Sede, Socio, Libro, Ejemplar, Prestamo, Multa
from api.services.prestamo_service import PrestamoService


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
def datos_completos(session):
    """Carga un conjunto completo de datos para testear préstamos."""
    sede_a = Sede(direccion="Sede Norte", contacto="011-1111", horarios="9-18", estado="activo")
    sede_b = Sede(direccion="Sede Sur", contacto="011-2222", horarios="9-18", estado="activo")
    sede_baja = Sede(direccion="Sede Cerrada", contacto="011-3333", horarios="-", estado="baja")
    session.add_all([sede_a, sede_b, sede_baja])
    session.commit()

    socio_ok = Socio(numero_socio="SOC-100", documento="40000100", nombre="Laura", apellido="Martínez",
                     email="laura@mail.com", telefono="351-0100", activo=1)
    socio_inhabilitado = Socio(numero_socio="SOC-101", documento="40000101", nombre="Pedro", apellido="López",
                               email="pedro@mail.com", telefono="351-0101", activo=0)
    session.add_all([socio_ok, socio_inhabilitado])
    session.commit()

    libro = Libro(isbn="978-999-888-777-6", titulo="Sistemas Operativos", editorial="Ed. Pearson", anio=2022)
    session.add(libro)
    session.commit()

    ej_disponible = Ejemplar(codigo_inventario="EJ-100", estado_fisico="Disponible",
                             libro_id=libro.id, sede_id=sede_a.id)
    ej_prestado = Ejemplar(codigo_inventario="EJ-101", estado_fisico="Prestado",
                           libro_id=libro.id, sede_id=sede_a.id)
    ej_otra_sede = Ejemplar(codigo_inventario="EJ-102", estado_fisico="Disponible",
                            libro_id=libro.id, sede_id=sede_b.id)
    session.add_all([ej_disponible, ej_prestado, ej_otra_sede])
    session.commit()

    return {
        "sede_a": sede_a, "sede_b": sede_b, "sede_baja": sede_baja,
        "socio_ok": socio_ok, "socio_inhabilitado": socio_inhabilitado,
        "libro": libro,
        "ej_disponible": ej_disponible, "ej_prestado": ej_prestado,
        "ej_otra_sede": ej_otra_sede,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tests de Reglas de Negocio
# ─────────────────────────────────────────────────────────────────────────────
class TestReglasNegocioPrestamos:
    """Tests para las reglas de negocio obligatorias del sistema de préstamos."""

    def test_prestamo_local_exitoso(self, session, datos_completos):
        """Un préstamo local válido debe crearse correctamente."""
        d = datos_completos
        service = PrestamoService(session)

        prestamo = service.registrar_prestamo(
            socio_id=d["socio_ok"].id,
            ejemplar_id=d["ej_disponible"].id,
            sede_origen_id=d["sede_a"].id,
        )
        assert prestamo.estado == "Activo"
        assert prestamo.sede_destino_id is None  # Es local

    def test_prestamo_interbibliotecario_exitoso(self, session, datos_completos):
        """Un préstamo interbibliotecario válido debe crearse con remito asociado."""
        d = datos_completos
        service = PrestamoService(session)

        prestamo = service.registrar_prestamo(
            socio_id=d["socio_ok"].id,
            ejemplar_id=d["ej_disponible"].id,
            sede_origen_id=d["sede_a"].id,
            sede_destino_id=d["sede_b"].id,
        )
        assert prestamo.estado == "Activo"
        assert prestamo.sede_destino_id == d["sede_b"].id
        assert prestamo.remito is not None  # Se genera automáticamente
        assert prestamo.remito.estado == "Empaquetado"

    def test_rn01_ejemplar_no_disponible(self, session, datos_completos):
        """RN-01: No se puede prestar un ejemplar que no esté disponible."""
        d = datos_completos
        service = PrestamoService(session)

        with pytest.raises(ValueError, match="no se encuentra disponible"):
            service.registrar_prestamo(
                socio_id=d["socio_ok"].id,
                ejemplar_id=d["ej_prestado"].id,
                sede_origen_id=d["sede_a"].id,
            )

    def test_rn02_socio_inhabilitado(self, session, datos_completos):
        """RN-02: No se puede prestar a un socio inhabilitado."""
        d = datos_completos
        service = PrestamoService(session)

        with pytest.raises(ValueError, match="inhabilitado"):
            service.registrar_prestamo(
                socio_id=d["socio_inhabilitado"].id,
                ejemplar_id=d["ej_disponible"].id,
                sede_origen_id=d["sede_a"].id,
            )

    def test_rn02_socio_con_multas_pendientes(self, session, datos_completos):
        """RN-02: No se puede prestar a un socio con multas pendientes."""
        d = datos_completos
        multa = Multa(monto=500, estado="Pendiente",
                      prestamo_id=1, socio_id=d["socio_ok"].id)
        # Necesitamos un préstamo para asociar la multa
        prestamo_previo = Prestamo(
            socio_id=d["socio_ok"].id, ejemplar_id=d["ej_prestado"].id,
            sede_origen_id=d["sede_a"].id,
            fecha_devolucion_estimada=date.today() - timedelta(days=5),
            estado="Devuelto",
        )
        session.add(prestamo_previo)
        session.commit()
        multa.prestamo_id = prestamo_previo.id
        session.add(multa)
        session.commit()

        service = PrestamoService(session)
        with pytest.raises(ValueError, match="multa"):
            service.registrar_prestamo(
                socio_id=d["socio_ok"].id,
                ejemplar_id=d["ej_disponible"].id,
                sede_origen_id=d["sede_a"].id,
            )

    def test_rn03_ejemplar_de_otra_sede(self, session, datos_completos):
        """RN-03: Un préstamo local no puede usar ejemplares de otra sede."""
        d = datos_completos
        service = PrestamoService(session)

        with pytest.raises(ValueError, match="misma sede"):
            service.registrar_prestamo(
                socio_id=d["socio_ok"].id,
                ejemplar_id=d["ej_otra_sede"].id,  # Pertenece a sede_b
                sede_origen_id=d["sede_a"].id,       # Procesado en sede_a
            )

    def test_rn04_sede_origen_dada_de_baja(self, session, datos_completos):
        """RN-04: No se permite operar desde una sede dada de baja."""
        d = datos_completos
        service = PrestamoService(session)

        with pytest.raises(ValueError, match="dada de baja"):
            service.registrar_prestamo(
                socio_id=d["socio_ok"].id,
                ejemplar_id=d["ej_disponible"].id,
                sede_origen_id=d["sede_baja"].id,
            )

    def test_rn04_sede_destino_dada_de_baja(self, session, datos_completos):
        """RN-04: No se permite enviar material a una sede dada de baja."""
        d = datos_completos
        service = PrestamoService(session)

        with pytest.raises(ValueError, match="dada de baja"):
            service.registrar_prestamo(
                socio_id=d["socio_ok"].id,
                ejemplar_id=d["ej_disponible"].id,
                sede_origen_id=d["sede_a"].id,
                sede_destino_id=d["sede_baja"].id,
            )

    def test_ejemplar_cambia_a_prestado(self, session, datos_completos):
        """Al registrar un préstamo, el ejemplar debe pasar a estado 'Prestado'."""
        d = datos_completos
        service = PrestamoService(session)

        service.registrar_prestamo(
            socio_id=d["socio_ok"].id,
            ejemplar_id=d["ej_disponible"].id,
            sede_origen_id=d["sede_a"].id,
        )
        session.refresh(d["ej_disponible"])
        assert d["ej_disponible"].estado_fisico == "Prestado"


# ─────────────────────────────────────────────────────────────────────────────
# Tests de Devolución
# ─────────────────────────────────────────────────────────────────────────────
class TestDevolucionPrestamos:
    """Tests para el proceso de devolución de préstamos."""

    def test_devolucion_sin_retraso(self, session, datos_completos):
        """Una devolución a tiempo no debe generar multa."""
        d = datos_completos
        service = PrestamoService(session)

        prestamo = service.registrar_prestamo(
            socio_id=d["socio_ok"].id,
            ejemplar_id=d["ej_disponible"].id,
            sede_origen_id=d["sede_a"].id,
            dias_prestamo=30,
        )
        prestamo_devuelto = service.registrar_devolucion(prestamo.id)

        assert prestamo_devuelto.estado == "Devuelto"
        assert prestamo_devuelto.multa is None

    def test_devolucion_con_retraso_genera_multa(self, session, datos_completos):
        """Una devolución con retraso debe generar multa automáticamente."""
        d = datos_completos
        service = PrestamoService(session)

        # Crear préstamo ya vencido (fecha estimada en el pasado)
        prestamo = Prestamo(
            socio_id=d["socio_ok"].id,
            ejemplar_id=d["ej_disponible"].id,
            sede_origen_id=d["sede_a"].id,
            fecha_devolucion_estimada=date.today() - timedelta(days=5),
            estado="Activo",
        )
        session.add(prestamo)
        d["ej_disponible"].estado_fisico = "Prestado"
        session.commit()

        prestamo_devuelto = service.registrar_devolucion(prestamo.id)

        assert prestamo_devuelto.estado == "Devuelto"
        assert prestamo_devuelto.multa is not None
        assert prestamo_devuelto.multa.monto == 750.0  # 5 x $150
