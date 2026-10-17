"""
Script de Inicialización (Seed) de Datos de Prueba.
Pobla la base de datos con registros para probar todos los flujos del sistema.
"""
from datetime import date, timedelta
from sqlalchemy.orm import Session
from api.database import SessionLocal, crear_tablas
from api.models import Sede, Autor, Libro, Ejemplar, Socio, Prestamo, Remito, Multa, Reserva


def ejecutar_seed(session: Session) -> None:
    """Inserta datos iniciales de prueba en la base de datos."""
    print("🌱 Iniciando la carga de datos de prueba (Seed)...")

    # 1. Sedes
    sede_centro = Sede(
        direccion="Av. Corrientes 1234, CABA",
        contacto="011-4321-5678",
        horarios="Lunes a Viernes de 08:00 a 20:00 hs",
        estado="activo"
    )
    sede_norte = Sede(
        direccion="Av. San Martín 456, Córdoba",
        contacto="0351-456-7890",
        horarios="Lunes a Sábados de 09:00 a 18:00 hs",
        estado="activo"
    )
    sede_inactiva = Sede(
        direccion="Calle Falsa 999, Rosario",
        contacto="0341-000-0000",
        horarios="Lunes a Viernes de 10:00 a 16:00 hs",
        estado="baja"
    )
    session.add_all([sede_centro, sede_norte, sede_inactiva])
    session.commit()

    # 2. Autores
    autor_borges = Autor(nombre="Jorge Luis", apellido="Borges", nacionalidad="Argentina")
    autor_cortazar = Autor(nombre="Julio", apellido="Cortázar", nacionalidad="Argentina")
    autor_asimov = Autor(nombre="Isaac", apellido="Asimov", nacionalidad="Estadounidense")
    session.add_all([autor_borges, autor_cortazar, autor_asimov])
    session.commit()

    # 3. Libros
    libro_ficciones = Libro(isbn="978-987-566-000-1", titulo="Ficciones", editorial="Emecé", anio=1944)
    libro_ficciones.autores.append(autor_borges)

    libro_rayuela = Libro(isbn="978-950-03-9000-2", titulo="Rayuela", editorial="Sudamericana", anio=1963)
    libro_rayuela.autores.append(autor_cortazar)

    libro_fundacion = Libro(isbn="978-0-553-29335-7", titulo="Fundación", editorial="Bantam Books", anio=1951)
    libro_fundacion.autores.append(autor_asimov)

    session.add_all([libro_ficciones, libro_rayuela, libro_fundacion])
    session.commit()

    # 4. Ejemplares Físicos (Distribuidos por sede con varios estados)
    ej1 = Ejemplar(codigo_inventario="EJ-CEN-001", estado_fisico="Disponible", libro_id=libro_ficciones.id, sede_id=sede_centro.id)
    ej2 = Ejemplar(codigo_inventario="EJ-CEN-002", estado_fisico="Prestado", libro_id=libro_rayuela.id, sede_id=sede_centro.id)
    ej3 = Ejemplar(codigo_inventario="EJ-NOR-001", estado_fisico="Disponible", libro_id=libro_fundacion.id, sede_id=sede_norte.id)
    ej4 = Ejemplar(codigo_inventario="EJ-NOR-002", estado_fisico="Dañado", libro_id=libro_ficciones.id, sede_id=sede_norte.id)
    # Ejemplar sin stock disponible en sede_centro para probar reservas (SUP-06)
    ej5 = Ejemplar(codigo_inventario="EJ-CEN-003", estado_fisico="Prestado", libro_id=libro_fundacion.id, sede_id=sede_centro.id)

    session.add_all([ej1, ej2, ej3, ej4, ej5])
    session.commit()

    # 5. Socios (Habilitados e Inhabilitados)
    socio_activo1 = Socio(numero_socio="SOC-001", documento="35123456", nombre="Brisa", apellido="Díaz", email="brisa.diaz@example.com", telefono="351-555-1234", activo=1)
    socio_activo2 = Socio(numero_socio="SOC-002", documento="38987654", nombre="Carlos", apellido="Gómez", email="carlos.gomez@example.com", telefono="011-555-9876", activo=1)
    socio_inhabilitado = Socio(numero_socio="SOC-003", documento="28111222", nombre="María", apellido="Pérez", email="maria.perez@example.com", telefono="0351-555-4321", activo=0)

    session.add_all([socio_activo1, socio_activo2, socio_inhabilitado])
    session.commit()

    # 6. Préstamos (Activos, devueltos e interbibliotecarios con remitos)
    # Préstamo local activo
    prestamo_activo = Prestamo(
        socio_id=socio_activo1.id,
        ejemplar_id=ej2.id,
        sede_origen_id=sede_centro.id,
        sede_destino_id=sede_centro.id,
        fecha_prestamo=date.today() - timedelta(days=5),
        fecha_devolucion_estimada=date.today() + timedelta(days=10),
        estado="Activo"
    )

    # Préstamo interbibliotecario en tránsito con remito
    prestamo_inter = Prestamo(
        socio_id=socio_activo2.id,
        ejemplar_id=ej5.id,
        sede_origen_id=sede_centro.id,
        sede_destino_id=sede_norte.id,
        fecha_prestamo=date.today() - timedelta(days=2),
        fecha_devolucion_estimada=date.today() + timedelta(days=13),
        estado="Activo"
    )
    session.add_all([prestamo_activo, prestamo_inter])
    session.commit()

    # 7. Remito logístico asociado al préstamo interbibliotecario
    remito = Remito(
        codigo_remito="REM-2026-001",
        prestamo_id=prestamo_inter.id,
        estado="Despachado"
    )
    session.add_all([remito])
    session.commit()

    # 8. Multas y Sanciones para el socio inhabilitado
    multa = Multa(
        socio_id=socio_inhabilitado.id,
        prestamo_id=prestamo_activo.id,  # Referencia de ejemplo
        monto=2500.00,
        estado="Pendiente",
        fecha_emision=date.today() - timedelta(days=10)
    )
    session.add_all([multa])
    session.commit()

    # 9. Reservas (Obra con stock 0 en la sede)
    reserva = Reserva(
        socio_id=socio_activo1.id,
        libro_id=libro_fundacion.id,
        sede_id=sede_centro.id,
        estado="Pendiente"
    )
    session.add_all([reserva])
    session.commit()

    print("✅ ¡Datos de prueba insertados con éxito!")


if __name__ == "__main__":
    crear_tablas()
    db = SessionLocal()
    try:
        ejecutar_seed(db)
    except Exception as e:
        db.rollback()
        print(f"❌ Error al ejecutar el seed: {e}")
    finally:
        db.close()