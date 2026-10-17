"""
Tests para las Reglas de Negocio y Supuestos de Préstamos (RN-01 a RN-05, SUP-04, SUP-07, SUP-08).
Valida las restricciones obligatorias y los nuevos supuestos del dominio.
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

    # Varios ejemplares para probar límites simultáneos
    ej_disponible_1 = Ejemplar(codigo_inventario="EJ-100", estado_fisico="Disponible", libro_id=libro.id, sede_id=sede_a.id)
    ej_disponible_2 = Ejemplar(codigo_inventario="EJ-101", estado_fisico="Disponible", libro_id=libro.id, sede_id=sede_a.id)
    ej_disponible_3 = Ejemplar(codigo_inventario="EJ-102", estado_fisico="Disponible", libro_id=libro.id, sede_id=sede_a.id)
    ej_disponible_4 = Ejemplar(codigo_inventario="EJ-103", estado_fisico="Disponible", libro_id=libro.id, sede_id=sede_a.id)
    ej_prestado = Ejemplar(codigo_inventario="EJ-104", estado_fisico="Prestado", libro_id=libro.id, sede_id=sede_a.id)
    ej_otra_sede = Ejemplar(codigo_inventario="EJ-105", estado_fisico="Disponible", libro_id=libro.id, sede_id=sede_b.id)
    
    session.add_all([ej_disponible_1, ej_disponible_2, ej_disponible_3, ej_disponible_4, ej_prestado, ej_otra_sede])
    session.commit()

    return {
        "sede_a": sede_a, "sede_b": sede_b, "sede_baja": sede_baja,
        "socio_ok": socio_ok, "socio_inhabilitado": socio_inhabilitado,
        "libro": libro,
        "ej_disponible_1": ej_disponible_1, "ej_disponible_2": ej_disponible_2,
        "ej_disponible_3": ej_disponible_3, "ej_disponible_4": ej_disponible_4,
        "ej_prestado": ej_prestado, "ej_otra_sede": ej_otra_sede,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tests de Reglas de Negocio
# ─────────────────────────────────────────────────────────────────────────────
class TestReglasNegocioPrestamos:
    """Tests para las reglas de negocio obligatorias y nuevos supuestos del sistema de préstamos."""

    def test_prestamo_local_exitoso(self, session, datos_completos):
        """Un préstamo local válido debe crearse correctamente."""
        d = datos_completos
        service = PrestamoService(session)

        prestamo = service.registrar_prestamo(
            socio_id=d["socio_ok"].id,
            ejemplar_id=d["ej_disponible_1"].id,
            sede_origen_id=d["sede_a"].id,
        )
        assert prestamo.estado == "Activo"
        assert prestamo.sede_destino_id is None

    def test_prestamo_interbibliotecario_exitoso(self, session, datos_completos):
        """Un préstamo interbibliotecario válido debe crearse con remito asociado."""
        d = datos_completos
        service = PrestamoService(session)

        prestamo = service.registrar_prestamo(
            socio_id=d["socio_ok"].id,
            ejemplar_id=d["ej_disponible_1"].id,
            sede_origen_id=d["sede_a"].id,
            sede_destino_id=d["sede_b"].id,
        )
        assert prestamo.estado == "Activo"
        assert prestamo.sede_destino_id == d["sede_b"].id
        assert prestamo.remito is not None
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
                ejemplar_id=d["ej_disponible_1"].id,
                sede_origen_id=d["sede_a"].id,
            )

    def test_rn03_ejemplar_de_otra_sede(self, session, datos_completos):
        """RN-03: Un préstamo local no puede usar ejemplares de otra sede."""
        d = datos_completos
        service = PrestamoService(session)

        with pytest.raises(ValueError, match="misma sede"):
            service.registrar_prestamo(
                socio_id=d["socio_ok"].id,
                ejemplar_id=d["ej_otra_sede"].id,
                sede_origen_id=d["sede_a"].id,
            )

    def test_rn04_sede_origen_dada_de_baja(self, session, datos_completos):
        """RN-04: No se permite operar desde una sede dada de baja."""
        d = datos_completos
        service = PrestamoService(session)

        with pytest.raises(ValueError, match="dada de baja"):
            service.registrar_prestamo(
                socio_id=d["socio_ok"].id,
                ejemplar_id=d["ej_disponible_1"].id,
                sede_origen_id=d["sede_baja"].id,
            )

    # ────────────────────────────────────────────────────────────────────────
    # Nuevos Tests para Supuestos (SUP-04, SUP-07, SUP-08)
    # ────────────────────────────────────────────────────────────────────────
    def test_sup04_limite_prestamos_simultaneos(self, session, datos_completos):
        """SUP-04: Un socio activo no puede superar los 3 préstamos simultáneos."""
        d = datos_completos
        service = PrestamoService(session)

        # Realizar los 3 préstamos permitidos
        service.registrar_prestamo(d["socio_ok"].id, d["ej_disponible_1"].id, d["sede_a"].id)
        service.registrar_prestamo(d["socio_ok"].id, d["ej_disponible_2"].id, d["sede_a"].id)
        service.registrar_prestamo(d["socio_ok"].id, d["ej_disponible_3"].id, d["sede_a"].id)

        # Intentar realizar un cuarto préstamo debe fallar
        with pytest.raises(ValueError, match="límite máximo de 3 préstamos"):
            service.registrar_prestamo(
                socio_id=d["socio_ok"].id,
                ejemplar_id=d["ej_disponible_4"].id,
                sede_origen_id=d["sede_a"].id,
            )

    def test_sup07_cargo_por_dano_o_extravio(self, session, datos_completos):
        """SUP-07: Devolver un ejemplar dañado o extraviado genera cargo fijo e inhabilita al socio."""
        d = datos_completos
        service = PrestamoService(session)

        prestamo = service.registrar_prestamo(
            socio_id=d["socio_ok"].id,
            ejemplar_id=d["ej_disponible_1"].id,
            sede_origen_id=d["sede_a"].id,
        )

        # Registrar devolución con estado 'Dañado'
        service.registrar_devolucion(prestamo.id, estado_fisico_ejemplar="Dañado")

        # Verificar que se generó multa por daño y que el socio quedó inhabilitado (activo = 0)
        multas = session.query(Multa).filter(Multa.socio_id == d["socio_ok"].id).all()
        assert len(multas) == 1
        assert multas[0].monto == 5000.0
        
        session.refresh(d["socio_ok"])
        assert d["socio_ok"].activo == 0

    def test_sup08_prohibicion_renovaciones(self, session, datos_completos):
        """SUP-08: No se permiten extensiones ni renovaciones de préstamos."""
        d = datos_completos
        service = PrestamoService(session)

        prestamo = service.registrar_prestamo(
            socio_id=d["socio_ok"].id,
            ejemplar_id=d["ej_disponible_1"].id,
            sede_origen_id=d["sede_a"].id,
        )

        with pytest.raises(ValueError, match="No se permiten extensiones ni renovaciones"):
            service.renovar_prestamo(prestamo.id)


# ─────────────────────────────────────────────────────────────────────────────
# Tests de Devolución
# ─────────────────────────────────────────────────────────────────────────────
class TestDevolucionPrestamos:
    """Tests para el proceso estándar de devolución de préstamos."""

    def test_devolucion_sin_retraso(self, session, datos_completos):
        """Una devolución a tiempo no debe generar multa."""
        d = datos_completos
        service = PrestamoService(session)

        prestamo = service.registrar_prestamo(
            socio_id=d["socio_ok"].id,
            ejemplar_id=d["ej_disponible_1"].id,
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

        prestamo = Prestamo(
            socio_id=d["socio_ok"].id,
            ejemplar_id=d["ej_disponible_1"].id,
            sede_origen_id=d["sede_a"].id,
            fecha_devolucion_estimada=date.today() - timedelta(days=5),
            estado="Activo",
        )
        session.add(prestamo)
        d["ej_disponible_1"].estado_fisico = "Prestado"
        session.commit()

        prestamo_devuelto = service.registrar_devolucion(prestamo.id)

        assert prestamo_devuelto.estado == "Devuelto"
        assert prestamo_devuelto.multa is not None
        assert prestamo_devuelto.multa.monto == 750.0  # 5 x $150