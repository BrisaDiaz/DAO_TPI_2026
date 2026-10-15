"""
Tests para el Patrón Strategy - Cálculo de Multas.
Valida las diferentes estrategias de cálculo y la generación automática de multas.
"""
import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.database import Base
from api.models import Sede, Socio, Libro, Ejemplar, Prestamo, Multa
from api.services.multa_service import (
    MultaService, MultaEstandar, MultaReducidaEstudiante,
    SinMultaPromocional, ESTRATEGIAS,
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
    """Carga datos mínimos para testear multas."""
    sede = Sede(direccion="Sede Centro", contacto="011-3333", horarios="9-18", estado="activo")
    session.add(sede)
    session.commit()

    socio = Socio(numero_socio="SOC-010", documento="33000010", nombre="Carlos", apellido="Ruiz",
                  email="carlos@mail.com", telefono="351-0010")
    session.add(socio)
    session.commit()

    libro = Libro(isbn="978-444-555-666-7", titulo="Redes de Computadoras", editorial="Ed. Sur", anio=2023)
    session.add(libro)
    session.commit()

    ejemplar = Ejemplar(codigo_inventario="EJ-010", estado_fisico="Prestado",
                        libro_id=libro.id, sede_id=sede.id)
    session.add(ejemplar)
    session.commit()

    return {"sede": sede, "socio": socio, "libro": libro, "ejemplar": ejemplar}


def crear_prestamo_vencido(session, datos, dias_retraso: int):
    """Helper: crea un préstamo que venció hace N días."""
    prestamo = Prestamo(
        socio_id=datos["socio"].id,
        ejemplar_id=datos["ejemplar"].id,
        sede_origen_id=datos["sede"].id,
        fecha_prestamo=date.today() - timedelta(days=30),
        fecha_devolucion_estimada=date.today() - timedelta(days=dias_retraso),
        fecha_devolucion_real=date.today(),
        estado="Devuelto",
    )
    session.add(prestamo)
    session.commit()
    return prestamo


# ─────────────────────────────────────────────────────────────────────────────
# Tests de las Estrategias de Cálculo
# ─────────────────────────────────────────────────────────────────────────────
class TestEstrategiasMulta:
    """Tests para las estrategias concretas de cálculo de multas."""

    def test_multa_estandar_5_dias(self):
        """Multa estándar de 5 días: 5 x $150 = $750."""
        estrategia = MultaEstandar()
        assert estrategia.calcular_multa(5) == 750.0

    def test_multa_estandar_0_dias(self):
        """Sin retraso: $0."""
        estrategia = MultaEstandar()
        assert estrategia.calcular_multa(0) == 0.0

    def test_multa_estudiante_5_dias(self):
        """Multa estudiante de 5 días: 5 x $75 = $375."""
        estrategia = MultaReducidaEstudiante()
        assert estrategia.calcular_multa(5) == 375.0

    def test_multa_promocional_siempre_cero(self):
        """La estrategia promocional siempre retorna $0."""
        estrategia = SinMultaPromocional()
        assert estrategia.calcular_multa(100) == 0.0

    def test_diccionario_estrategias(self):
        """El diccionario de estrategias debe contener las 3 opciones."""
        assert "estandar" in ESTRATEGIAS
        assert "estudiante" in ESTRATEGIAS
        assert "promocional" in ESTRATEGIAS

    def test_seleccion_por_diccionario(self):
        """La selección por diccionario debe retornar el cálculo correcto."""
        resultado = ESTRATEGIAS["estudiante"].calcular_multa(10)
        assert resultado == 750.0  # 10 x $75


# ─────────────────────────────────────────────────────────────────────────────
# Tests del Servicio de Multas
# ─────────────────────────────────────────────────────────────────────────────
class TestMultaService:
    """Tests para el servicio de multas (generación, pago, condonación)."""

    def test_generar_multa_con_retraso(self, session, datos_base):
        """Un préstamo con 10 días de retraso debe generar multa de $1500."""
        prestamo = crear_prestamo_vencido(session, datos_base, dias_retraso=10)
        service = MultaService(session)
        multa = service.generar_multa(prestamo, "estandar")

        assert multa is not None
        assert multa.monto == 1500.0  # 10 x $150
        assert multa.estado == "Pendiente"

    def test_no_generar_multa_sin_retraso(self, session, datos_base):
        """Un préstamo sin retraso no debe generar multa."""
        prestamo = Prestamo(
            socio_id=datos_base["socio"].id,
            ejemplar_id=datos_base["ejemplar"].id,
            sede_origen_id=datos_base["sede"].id,
            fecha_devolucion_estimada=date.today() + timedelta(days=5),
            fecha_devolucion_real=date.today(),
            estado="Devuelto",
        )
        session.add(prestamo)
        session.commit()

        service = MultaService(session)
        multa = service.generar_multa(prestamo)
        assert multa is None

    def test_registrar_pago(self, session, datos_base):
        """Al pagar una multa, su estado debe cambiar a 'Pagada'."""
        prestamo = crear_prestamo_vencido(session, datos_base, dias_retraso=5)
        service = MultaService(session)
        multa = service.generar_multa(prestamo)

        multa_pagada = service.registrar_pago(multa.id)
        assert multa_pagada.estado == "Pagada"

    def test_condonar_multa(self, session, datos_base):
        """Al condonar una multa, su estado debe cambiar a 'Condonada'."""
        prestamo = crear_prestamo_vencido(session, datos_base, dias_retraso=3)
        service = MultaService(session)
        multa = service.generar_multa(prestamo)

        multa_condonada = service.condonar_multa(multa.id)
        assert multa_condonada.estado == "Condonada"

    def test_reactivacion_socio_al_pagar(self, session, datos_base):
        """Al pagar la última multa pendiente, el socio se reactiva."""
        socio = datos_base["socio"]
        socio.activo = 0
        session.commit()

        prestamo = crear_prestamo_vencido(session, datos_base, dias_retraso=7)
        service = MultaService(session)
        multa = service.generar_multa(prestamo)

        service.registrar_pago(multa.id)
        session.refresh(socio)
        assert socio.activo == 1
