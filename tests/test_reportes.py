"""
Pruebas unitarias y de integración para el servicio de reportes (ReporteService).
Valida la correcta obtención de los 4 reportes analíticos del sistema.
"""
from datetime import date, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.database import Base
from api.models import (
    Sede, Socio, Autor, Libro, Ejemplar, Prestamo, Multa, Remito, Reserva
)
from api.services.reporte_service import ReporteService


@pytest.fixture
def db_session():
    """Configura una base de datos SQLite en memoria para cada test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def datos_prueba(db_session):
    """Inserta datos iniciales estándar para poblar los reportes."""
    # 1. Sede
    sede1 = Sede(direccion="Av. Corrientes 1000, CABA", contacto="1111", horarios="8 a 20", estado="activo")
    sede2 = Sede(direccion="Av. San Martin 500, Cordoba", contacto="2222", horarios="9 a 18", estado="activo")
    db_session.add_all([sede1, sede2])
    db_session.commit()

    # 2. Socio
    socio1 = Socio(numero_socio="S-001", documento="12345678", nombre="Ana", apellido="García", email="ana@mail.com", telefono="555-1111", activo=1)
    db_session.add(socio1)
    db_session.commit()

    # 3. Autor y Libro
    autor = Autor(nombre="Ernesto", apellido="Sábato", nacionalidad="Argentina")
    db_session.add(autor)
    db_session.commit()

    libro = Libro(isbn="978-950-16-0001-0", titulo="El Túnel", editorial="Seix Barral", anio=1948)
    libro.autores.append(autor)
    db_session.add(libro)
    db_session.commit()

    # 4. Ejemplar
    ejemplar = Ejemplar(codigo_inventario="EJ-001", estado_fisico="Prestado", libro_id=libro.id, sede_id=sede1.id)
    db_session.add(ejemplar)
    db_session.commit()

    # 5. Préstamo Activo e Interbibliotecario con Remito
    prestamo = Prestamo(
        socio_id=socio1.id,
        ejemplar_id=ejemplar.id,
        sede_origen_id=sede1.id,
        sede_destino_id=sede2.id,
        fecha_prestamo=date.today() - timedelta(days=5),
        fecha_devolucion_estimada=date.today() + timedelta(days=5),
        estado="Activo"
    )
    db_session.add(prestamo)
    db_session.commit()

    # 6. Remito
    remito = Remito(codigo_remito="REM-TEST-01", prestamo_id=prestamo.id, estado="Despachado")
    db_session.add(remito)
    db_session.commit()

    # 7. Multa
    multa = Multa(
        monto=1500.0,
        estado="Pendiente",
        prestamo_id=prestamo.id,
        socio_id=socio1.id
    )
    db_session.add(multa)
    db_session.commit()

    return {
        "sede1": sede1,
        "sede2": sede2,
        "socio1": socio1,
        "libro": libro,
        "ejemplar": ejemplar,
        "prestamo": prestamo,
        "multa": multa
    }


def test_reporte_prestamos_activos_y_transito(db_session, datos_prueba):
    """Verifica que el reporte 1 retorne correctamente los préstamos activos y su estado logístico."""
    service = ReporteService(db_session)
    resultado = service.reporte_prestamos_activos_y_transito()

    assert len(resultado) == 1
    item = resultado[0]
    assert item["titulo_libro"] == "El Túnel"
    assert item["tipo_prestamo"] == "Interbibliotecario"
    assert item["estado_logistico"] == "Despachado"
    assert item["socio_nombre"] == "Ana García"


def test_reporte_vencidos_y_multas(db_session, datos_prueba):
    """Verifica que el reporte 2 retorne las multas registradas con su socio y monto."""
    service = ReporteService(db_session)
    resultado = service.reporte_vencidos_y_multas()

    assert len(resultado) == 1
    item = resultado[0]
    assert item["numero_socio"] == "S-001"
    assert item["socio_nombre"] == "Ana García"
    assert item["titulo_libro"] == "El Túnel"
    assert item["multa_acumulada"] == 1500.0


def test_reporte_demanda_intersedes(db_session, datos_prueba):
    """Verifica el cálculo del ranking de libros más solicitados entre sedes."""
    service = ReporteService(db_session)
    resultado = service.reporte_demanda_intersedes()

    assert len(resultado) == 1
    item = resultado[0]
    assert item["isbn"] == "978-950-16-0001-0"
    assert item["titulo"] == "El Túnel"
    assert item["total_solicitudes_intersedes"] == 1


def test_reporte_disponibilidad_por_sede(db_session, datos_prueba):
    """Verifica el balance de inventario disponible y no disponible por sede."""
    service = ReporteService(db_session)
    resultado = service.reporte_disponibilidad_por_sede()

    # Como hay inventario radicado en sede1 con ejemplar 'Prestado', debe reflejar 1 no disponible
    assert len(resultado) >= 1
    sede_centro_item = next(r for r in resultado if "Corrientes" in r["sede"])
    assert sede_centro_item["ejemplares_totales"] == 1
    assert sede_centro_item["ejemplares_no_disponibles"] == 1
    assert sede_centro_item["ejemplares_disponibles"] == 0