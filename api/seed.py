"""
Script de Inicialización (Seed) de Datos de Prueba.
Pobla la base de datos con registros para probar todos los flujos del sistema.
"""
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from api.database import SessionLocal, crear_tablas
from api.models import Sede, Autor, Libro, Ejemplar, Socio, Prestamo, Remito, Multa, Reserva


def ejecutar_seed(session: Session) -> None:
    """Inserta datos iniciales de prueba en la base de datos."""
    print("[Seed] Iniciando la carga de datos de prueba...")

    # 1. Sedes (3 originales + 5 nuevas = 8 sedes)
    sede_centro = Sede(
        direccion="Av. Corrientes 1234, CABA",
        contacto="011-4321-5678",
        horarios="Lunes a Viernes de 08:00 a 20:00 hs",
        estado="activo",
    )
    sede_norte = Sede(
        direccion="Av. San Martín 456, Córdoba",
        contacto="0351-456-7890",
        horarios="Lunes a Sábados de 09:00 a 18:00 hs",
        estado="activo",
    )
    sede_inactiva = Sede(
        direccion="Calle Falsa 999, Rosario",
        contacto="0341-000-0000",
        horarios="Lunes a Viernes de 10:00 a 16:00 hs",
        estado="baja",
    )
    sede_rosario = Sede(
        direccion="Bv. Oroño 820, Rosario",
        contacto="0341-425-8899",
        horarios="Lunes a Viernes de 08:00 a 19:00 hs",
        estado="activo",
    )
    sede_mendoza = Sede(
        direccion="Av. Libertador 750, Mendoza",
        contacto="0261-429-3344",
        horarios="Lunes a Sábados de 09:00 a 20:00 hs",
        estado="activo",
    )
    sede_laplata = Sede(
        direccion="Calle 7 N° 1145, La Plata",
        contacto="0221-483-2211",
        horarios="Lunes a Viernes de 08:30 a 18:30 hs",
        estado="activo",
    )
    sede_sur_cba = Sede(
        direccion="Av. Vélez Sarsfield 2100, Córdoba",
        contacto="0351-468-9012",
        horarios="Lunes a Sábados de 08:00 a 21:00 hs",
        estado="activo",
    )
    sede_palermo = Sede(
        direccion="Av. Santa Fe 3250, CABA",
        contacto="011-4822-7766",
        horarios="Lunes a Viernes de 09:00 a 17:00 hs",
        estado="baja",
    )
    session.add_all([
        sede_centro,
        sede_norte,
        sede_inactiva,
        sede_rosario,
        sede_mendoza,
        sede_laplata,
        sede_sur_cba,
        sede_palermo,
    ])
    session.commit()

    # 2. Autores (3 originales + 5 nuevos = 8 autores)
    autor_borges = Autor(nombre="Jorge Luis", apellido="Borges", nacionalidad="Argentina")
    autor_cortazar = Autor(nombre="Julio", apellido="Cortázar", nacionalidad="Argentina")
    autor_asimov = Autor(nombre="Isaac", apellido="Asimov", nacionalidad="Estadounidense")
    autor_sabato = Autor(nombre="Ernesto", apellido="Sábato", nacionalidad="Argentina")
    autor_garcia_marquez = Autor(nombre="Gabriel", apellido="García Márquez", nacionalidad="Colombiana")
    autor_orwell = Autor(nombre="George", apellido="Orwell", nacionalidad="Británica")
    autor_enriquez = Autor(nombre="Mariana", apellido="Enríquez", nacionalidad="Argentina")
    autor_martin = Autor(nombre="Robert C.", apellido="Martin", nacionalidad="Estadounidense")
    session.add_all([
        autor_borges,
        autor_cortazar,
        autor_asimov,
        autor_sabato,
        autor_garcia_marquez,
        autor_orwell,
        autor_enriquez,
        autor_martin,
    ])
    session.commit()

    # 3. Libros (3 originales + 5 nuevos = 8 libros)
    libro_ficciones = Libro(isbn="978-987-566-000-1", titulo="Ficciones", editorial="Emecé", anio=1944)
    libro_ficciones.autores.append(autor_borges)

    libro_rayuela = Libro(isbn="978-950-03-9000-2", titulo="Rayuela", editorial="Sudamericana", anio=1963)
    libro_rayuela.autores.append(autor_cortazar)

    libro_fundacion = Libro(isbn="978-0-553-29335-7", titulo="Fundación", editorial="Bantam Books", anio=1951)
    libro_fundacion.autores.append(autor_asimov)

    libro_tunel = Libro(isbn="978-950-731-656-2", titulo="El Túnel", editorial="Seix Barral", anio=1948)
    libro_tunel.autores.append(autor_sabato)

    libro_soledad = Libro(isbn="978-950-07-2879-9", titulo="Cien Años de Soledad", editorial="Sudamericana", anio=1967)
    libro_soledad.autores.append(autor_garcia_marquez)

    libro_1984 = Libro(isbn="978-987-566-928-4", titulo="1984", editorial="Debolsillo", anio=1949)
    libro_1984.autores.append(autor_orwell)

    libro_noche = Libro(isbn="978-987-712-192-6", titulo="Nuestra Parte de Noche", editorial="Anagrama", anio=2019)
    libro_noche.autores.append(autor_enriquez)

    libro_cleancode = Libro(isbn="978-0-13-235088-4", titulo="Clean Code", editorial="Prentice Hall", anio=2008)
    libro_cleancode.autores.append(autor_martin)

    session.add_all([
        libro_ficciones,
        libro_rayuela,
        libro_fundacion,
        libro_tunel,
        libro_soledad,
        libro_1984,
        libro_noche,
        libro_cleancode,
    ])
    session.commit()

    # 4. Ejemplares Físicos (5 originales + 10 nuevos = 15 ejemplares)
    ej1 = Ejemplar(codigo_inventario="EJ-CEN-001", estado_fisico="Disponible", libro_id=libro_ficciones.id, sede_id=sede_centro.id)
    ej2 = Ejemplar(codigo_inventario="EJ-CEN-002", estado_fisico="Prestado", libro_id=libro_rayuela.id, sede_id=sede_centro.id)
    ej3 = Ejemplar(codigo_inventario="EJ-NOR-001", estado_fisico="Disponible", libro_id=libro_fundacion.id, sede_id=sede_norte.id)
    ej4 = Ejemplar(codigo_inventario="EJ-NOR-002", estado_fisico="Dañado", libro_id=libro_ficciones.id, sede_id=sede_norte.id)
    ej5 = Ejemplar(codigo_inventario="EJ-CEN-003", estado_fisico="Prestado", libro_id=libro_fundacion.id, sede_id=sede_centro.id)
    ej6 = Ejemplar(codigo_inventario="EJ-ROS-001", estado_fisico="Disponible", libro_id=libro_tunel.id, sede_id=sede_rosario.id)
    ej7 = Ejemplar(codigo_inventario="EJ-ROS-002", estado_fisico="Prestado", libro_id=libro_soledad.id, sede_id=sede_rosario.id)
    ej8 = Ejemplar(codigo_inventario="EJ-MZA-001", estado_fisico="Disponible", libro_id=libro_1984.id, sede_id=sede_mendoza.id)
    ej9 = Ejemplar(codigo_inventario="EJ-MZA-002", estado_fisico="Prestado", libro_id=libro_noche.id, sede_id=sede_mendoza.id)
    ej10 = Ejemplar(codigo_inventario="EJ-LPL-001", estado_fisico="Disponible", libro_id=libro_cleancode.id, sede_id=sede_laplata.id)
    ej11 = Ejemplar(codigo_inventario="EJ-LPL-002", estado_fisico="Prestado", libro_id=libro_tunel.id, sede_id=sede_laplata.id)
    ej12 = Ejemplar(codigo_inventario="EJ-CBA-001", estado_fisico="Disponible", libro_id=libro_soledad.id, sede_id=sede_sur_cba.id)
    ej13 = Ejemplar(codigo_inventario="EJ-CBA-002", estado_fisico="Prestado", libro_id=libro_cleancode.id, sede_id=sede_sur_cba.id)
    ej14 = Ejemplar(codigo_inventario="EJ-CEN-004", estado_fisico="Disponible", libro_id=libro_1984.id, sede_id=sede_centro.id)
    ej15 = Ejemplar(codigo_inventario="EJ-NOR-003", estado_fisico="Extraviado", libro_id=libro_noche.id, sede_id=sede_norte.id)

    session.add_all([ej1, ej2, ej3, ej4, ej5, ej6, ej7, ej8, ej9, ej10, ej11, ej12, ej13, ej14, ej15])
    session.commit()

    # 5. Socios (3 originales + 6 adicionales = 9 socios)
    socio_activo1 = Socio(numero_socio="SOC-001", documento="35123456", nombre="Brisa", apellido="Díaz", email="brisa.diaz@example.com", telefono="0351-555-1234", activo=1)
    socio_activo2 = Socio(numero_socio="SOC-002", documento="38987654", nombre="Carlos", apellido="Gómez", email="carlos.gomez@example.com", telefono="011-555-9876", activo=1)
    socio_inhabilitado = Socio(numero_socio="SOC-003", documento="28111222", nombre="María", apellido="Pérez", email="maria.perez@example.com", telefono="0351-555-4321", activo=0)
    socio_4 = Socio(numero_socio="SOC-004", documento="41234567", nombre="Valentina", apellido="Lucero", email="valentina.lucero@example.com", telefono="0351-555-6789", activo=1)
    socio_5 = Socio(numero_socio="SOC-005", documento="39876543", nombre="Mateo", apellido="Fernández", email="mateo.fernandez@example.com", telefono="011-555-3456", activo=1)
    socio_6 = Socio(numero_socio="SOC-006", documento="42567890", nombre="Sofía", apellido="Martínez", email="sofia.martinez@example.com", telefono="0341-555-7890", activo=1)
    socio_7 = Socio(numero_socio="SOC-007", documento="34654321", nombre="Lucas", apellido="Rodríguez", email="lucas.rodriguez@example.com", telefono="0261-555-2345", activo=0)
    socio_8 = Socio(numero_socio="SOC-008", documento="44112233", nombre="Camila", apellido="Sánchez", email="camila.sanchez@example.com", telefono="0221-555-8901", activo=1)
    socio_9 = Socio(numero_socio="SOC-009", documento="46510634", nombre="Enzo", apellido="Cardelli", email="enzo.cardelli@example.com", telefono="0351-555-9012", activo=1)

    session.add_all([
        socio_activo1,
        socio_activo2,
        socio_inhabilitado,
        socio_4,
        socio_5,
        socio_6,
        socio_7,
        socio_8,
        socio_9,
    ])
    session.commit()

    # 6. Préstamos (2 originales + 5 nuevos = 7 préstamos)
    prestamo_activo = Prestamo(
        socio_id=socio_activo1.id,
        ejemplar_id=ej2.id,
        sede_origen_id=sede_centro.id,
        sede_destino_id=sede_centro.id,
        fecha_prestamo=date.today() - timedelta(days=5),
        fecha_devolucion_estimada=date.today() + timedelta(days=10),
        estado="Activo",
    )
    prestamo_inter = Prestamo(
        socio_id=socio_activo2.id,
        ejemplar_id=ej5.id,
        sede_origen_id=sede_centro.id,
        sede_destino_id=sede_norte.id,
        fecha_prestamo=date.today() - timedelta(days=2),
        fecha_devolucion_estimada=date.today() + timedelta(days=13),
        estado="Activo",
    )
    prestamo_3 = Prestamo(
        socio_id=socio_4.id,
        ejemplar_id=ej7.id,
        sede_origen_id=sede_rosario.id,
        sede_destino_id=sede_centro.id,
        fecha_prestamo=date.today() - timedelta(days=4),
        fecha_devolucion_estimada=date.today() + timedelta(days=11),
        estado="Activo",
    )
    prestamo_4 = Prestamo(
        socio_id=socio_5.id,
        ejemplar_id=ej9.id,
        sede_origen_id=sede_mendoza.id,
        sede_destino_id=sede_laplata.id,
        fecha_prestamo=date.today() - timedelta(days=19),
        fecha_devolucion_estimada=date.today() - timedelta(days=4),
        estado="Activo",
    )
    prestamo_5 = Prestamo(
        socio_id=socio_6.id,
        ejemplar_id=ej11.id,
        sede_origen_id=sede_laplata.id,
        sede_destino_id=sede_mendoza.id,
        fecha_prestamo=date.today() - timedelta(days=3),
        fecha_devolucion_estimada=date.today() + timedelta(days=12),
        estado="Activo",
    )
    prestamo_6 = Prestamo(
        socio_id=socio_7.id,
        ejemplar_id=ej13.id,
        sede_origen_id=sede_sur_cba.id,
        sede_destino_id=sede_norte.id,
        fecha_prestamo=date.today() - timedelta(days=23),
        fecha_devolucion_estimada=date.today() - timedelta(days=8),
        estado="Activo",
    )
    prestamo_7 = Prestamo(
        socio_id=socio_8.id,
        ejemplar_id=ej1.id,
        sede_origen_id=sede_centro.id,
        sede_destino_id=sede_rosario.id,
        fecha_prestamo=date.today() - timedelta(days=16),
        fecha_devolucion_estimada=date.today() - timedelta(days=1),
        fecha_devolucion_real=date.today() - timedelta(days=1),
        estado="Devuelto",
    )
    session.add_all([
        prestamo_activo,
        prestamo_inter,
        prestamo_3,
        prestamo_4,
        prestamo_5,
        prestamo_6,
        prestamo_7,
    ])
    session.commit()

    # 7. Remitos logísticos (1 original + 5 nuevos = 6 remitos)
    remito_1 = Remito(codigo_remito="REM-2026-001", prestamo_id=prestamo_inter.id, estado="Despachado")
    remito_2 = Remito(codigo_remito="REM-2026-002", prestamo_id=prestamo_3.id, estado="Empaquetado")
    remito_3 = Remito(codigo_remito="REM-2026-003", prestamo_id=prestamo_4.id, estado="Recibido")
    remito_4 = Remito(codigo_remito="REM-2026-004", prestamo_id=prestamo_5.id, estado="Despachado")
    remito_5 = Remito(codigo_remito="REM-2026-005", prestamo_id=prestamo_6.id, estado="Con incidencias")
    remito_6 = Remito(codigo_remito="REM-2026-006", prestamo_id=prestamo_7.id, estado="Recibido")
    session.add_all([remito_1, remito_2, remito_3, remito_4, remito_5, remito_6])
    session.commit()

    # 8. Multas y Sanciones (1 original + 5 nuevas = 6 multas)
    multa_1 = Multa(
        socio_id=socio_inhabilitado.id,
        prestamo_id=prestamo_activo.id,
        monto=2500.00,
        estado="Pendiente",
        fecha_emision=date.today() - timedelta(days=10),
    )
    multa_2 = Multa(
        socio_id=socio_7.id,
        prestamo_id=prestamo_6.id,
        monto=1800.00,
        estado="Pendiente",
        fecha_emision=date.today() - timedelta(days=6),
    )
    multa_3 = Multa(
        socio_id=socio_5.id,
        prestamo_id=prestamo_4.id,
        monto=900.00,
        estado="Pendiente",
        fecha_emision=date.today() - timedelta(days=3),
    )
    multa_4 = Multa(
        socio_id=socio_4.id,
        prestamo_id=prestamo_3.id,
        monto=750.00,
        estado="Pagada",
        fecha_emision=date.today() - timedelta(days=12),
    )
    multa_5 = Multa(
        socio_id=socio_9.id,
        prestamo_id=prestamo_7.id,
        monto=5000.00,
        estado="Condonada",
        fecha_emision=date.today() - timedelta(days=5),
    )
    multa_6 = Multa(
        socio_id=socio_inhabilitado.id,
        prestamo_id=prestamo_inter.id,
        monto=1200.00,
        estado="Pendiente",
        fecha_emision=date.today() - timedelta(days=2),
    )
    session.add_all([multa_1, multa_2, multa_3, multa_4, multa_5, multa_6])
    session.commit()

    # 9. Reservas (1 original + 5 nuevas = 6 reservas)
    reserva_1 = Reserva(
        socio_id=socio_activo1.id,
        libro_id=libro_fundacion.id,
        sede_id=sede_centro.id,
        estado="Pendiente",
    )
    reserva_2 = Reserva(
        socio_id=socio_4.id,
        libro_id=libro_rayuela.id,
        sede_id=sede_centro.id,
        estado="Pendiente",
    )
    reserva_3 = Reserva(
        socio_id=socio_5.id,
        libro_id=libro_soledad.id,
        sede_id=sede_rosario.id,
        fecha_reserva=datetime.now() - timedelta(days=5),
        fecha_notificacion=datetime.now() - timedelta(days=4),
        estado="Pendiente",
    )
    reserva_4 = Reserva(
        socio_id=socio_6.id,
        libro_id=libro_noche.id,
        sede_id=sede_mendoza.id,
        estado="Pendiente",
    )
    reserva_5 = Reserva(
        socio_id=socio_8.id,
        libro_id=libro_ficciones.id,
        sede_id=sede_centro.id,
        estado="Concretada",
    )
    reserva_6 = Reserva(
        socio_id=socio_9.id,
        libro_id=libro_cleancode.id,
        sede_id=sede_sur_cba.id,
        estado="Cancelada",
    )
    session.add_all([reserva_1, reserva_2, reserva_3, reserva_4, reserva_5, reserva_6])
    session.commit()

    print("[Seed] Datos de prueba insertados con éxito.")


if __name__ == "__main__":
    crear_tablas()
    db = SessionLocal()
    try:
        ejecutar_seed(db)
    except Exception as e:
        db.rollback()
        print(f"[Error] Error al ejecutar el seed: {e}")
    finally:
        db.close()
