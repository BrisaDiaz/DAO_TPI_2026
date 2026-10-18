"""
Servicio de Reportes No Triviales.

Implementa las 4 consultas analíticas complejas exigidas por la cátedra,
con JOINs, funciones de agregación, CASE y subconsultas.
"""
from datetime import date
from typing import List, Dict, Any

from sqlalchemy import func, case, and_
from sqlalchemy.orm import Session

from api.models import (Prestamo, Ejemplar, Libro, Socio, Sede, Remito, Multa)


class ReporteService:
    """Servicio para la generación de los reportes no triviales del sistema."""

    def __init__(self, session: Session):
        self.session = session

    # ─────────────────────────────────────────────────────────────────────────
    # Reporte 1: Préstamos Activos y Material en Tránsito
    # ─────────────────────────────────────────────────────────────────────────
    def reporte_prestamos_activos_y_transito(self) -> List[Dict[str, Any]]:
        """
        Retorna los préstamos activos con su información de tránsito logístico.
        Incluye: ID préstamo, título, código ejemplar, sedes, tipo, socio,
        fecha y estado logístico del remito.
        """
        SedeOrigen = Sede.__table__.alias("sede_origen")
        SedeDestino = Sede.__table__.alias("sede_destino")

        resultados = (
            self.session.query(
                Prestamo.id.label("id_prestamo"),
                Libro.titulo.label("titulo_libro"),
                Ejemplar.codigo_inventario,
                SedeOrigen.c.direccion.label("sede_origen"),
                SedeDestino.c.direccion.label("sede_destino"),
                case(
                    (Prestamo.sede_destino_id.is_(None), "Local"),
                    (Prestamo.sede_origen_id == Prestamo.sede_destino_id, "Local"),
                    else_="Interbibliotecario",
                ).label("tipo_prestamo"),
                (Socio.nombre + " " + Socio.apellido).label("socio_nombre"),
                Prestamo.fecha_prestamo,
                func.coalesce(Remito.estado, "Activo (Sin Tránsito)").label(
                    "estado_logistico"
                ),
            )
            .join(Ejemplar, Prestamo.ejemplar_id == Ejemplar.id)
            .join(Libro, Ejemplar.libro_id == Libro.id)
            .join(Socio, Prestamo.socio_id == Socio.id)
            .join(SedeOrigen, Prestamo.sede_origen_id == SedeOrigen.c.id)
            .outerjoin(SedeDestino, Prestamo.sede_destino_id == SedeDestino.c.id)
            .outerjoin(Remito, Prestamo.id == Remito.prestamo_id)
            .filter(Prestamo.estado == "Activo")
            .all()
        )

        return [
            {
                "id_prestamo": r.id_prestamo,
                "titulo_libro": r.titulo_libro,
                "codigo_inventario": r.codigo_inventario,
                "sede_origen": r.sede_origen,
                "sede_destino": r.sede_destino or "-",
                "tipo_prestamo": r.tipo_prestamo,
                "socio_nombre": r.socio_nombre,
                "fecha_prestamo": str(r.fecha_prestamo),
                "estado_logistico": r.estado_logistico,
            }
            for r in resultados
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # Reporte 2: Préstamos Vencidos y Multas Acumuladas
    # ─────────────────────────────────────────────────────────────────────────
    def reporte_vencidos_y_multas(self) -> List[Dict[str, Any]]:
        """
        Retorna el listado de multas y sanciones registradas en el sistema
        (por retrasos, daños o extravíos), asociadas al socio y préstamo correspondiente.
        """
        hoy = date.today()

        resultados = (
            self.session.query(
                Socio.numero_socio,
                (Socio.nombre + " " + Socio.apellido).label("socio_nombre"),
                Socio.email,
                Libro.titulo.label("titulo_libro"),
                Prestamo.fecha_devolucion_estimada,
                Multa.monto,
                Multa.estado.label("estado_multa"),
                case(
                    (Socio.activo == 0, "Inhabilitado (Deuda)"),
                    else_="Activo",
                ).label("estado_cuenta"),
            )
            .join(Multa, Socio.id == Multa.socio_id)
            .join(Prestamo, Multa.prestamo_id == Prestamo.id)
            .join(Ejemplar, Prestamo.ejemplar_id == Ejemplar.id)
            .join(Libro, Ejemplar.libro_id == Libro.id)
            .filter(Multa.estado == "Pendiente") # Opcional: filtrar las pendientes o mostrarlas todas
            .all()
        )

        return [
            {
                "numero_socio": r.numero_socio,
                "socio_nombre": r.socio_nombre,
                "email": r.email,
                "titulo_libro": r.titulo_libro,
                "fecha_devolucion_estimada": str(r.fecha_devolucion_estimada) if r.fecha_devolucion_estimada else "-",
                "dias_retraso": (hoy - r.fecha_devolucion_estimada).days if r.fecha_devolucion_estimada and hoy > r.fecha_devolucion_estimada else 0,
                "multa_acumulada": float(r.monto),
                "estado_cuenta": r.estado_cuenta,
            }
            for r in resultados
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # Reporte 3: Libros Más Solicitados para Préstamos Inter-sedes
    # ─────────────────────────────────────────────────────────────────────────
    def reporte_demanda_intersedes(self) -> List[Dict[str, Any]]:
        """
        Retorna el ranking de libros más solicitados en préstamos interbibliotecarios,
        agrupados por ISBN y título con conteo de solicitudes.
        """
        resultados = (
            self.session.query(
                Libro.isbn,
                Libro.titulo,
                func.count(Prestamo.id).label("total_solicitudes"),
            )
            .join(Ejemplar, Prestamo.ejemplar_id == Ejemplar.id)
            .join(Libro, Ejemplar.libro_id == Libro.id)
            .filter(
                Prestamo.sede_destino_id.isnot(None),
                Prestamo.sede_origen_id != Prestamo.sede_destino_id,
            )
            .group_by(Libro.isbn, Libro.titulo)
            .order_by(func.count(Prestamo.id).desc())
            .all()
        )

        return [
            {
                "ranking": idx + 1,
                "isbn": r.isbn,
                "titulo": r.titulo,
                "total_solicitudes_intersedes": r.total_solicitudes,
            }
            for idx, r in enumerate(resultados)
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # Reporte 4: Disponibilidad de Catálogo por Sede
    # ─────────────────────────────────────────────────────────────────────────
    def reporte_disponibilidad_por_sede(self) -> List[Dict[str, Any]]:
        """
        Retorna el inventario de ejemplares por sede, discriminando cuántos
        están disponibles y cuántos no, agrupados por libro y sede activa.
        """
        resultados = (
            self.session.query(
                Sede.direccion.label("sede"),
                Libro.isbn,
                Libro.titulo,
                func.count(Ejemplar.id).label("ejemplares_totales"),
                func.sum(
                    case(
                        (Ejemplar.estado_fisico == "Disponible", 1),
                        else_=0,
                    )
                ).label("ejemplares_disponibles"),
                func.sum(
                    case(
                        (Ejemplar.estado_fisico != "Disponible", 1),
                        else_=0,
                    )
                ).label("ejemplares_no_disponibles"),
            )
            .join(Ejemplar, Sede.id == Ejemplar.sede_id)
            .join(Libro, Ejemplar.libro_id == Libro.id)
            .filter(Sede.estado == "activo")
            .group_by(Sede.id, Sede.direccion, Libro.isbn, Libro.titulo)
            .all()
        )

        return [
            {
                "sede": r.sede,
                "isbn": r.isbn,
                "titulo": r.titulo,
                "ejemplares_totales": r.ejemplares_totales,
                "ejemplares_disponibles": r.ejemplares_disponibles,
                "ejemplares_no_disponibles": r.ejemplares_no_disponibles,
            }
            for r in resultados
        ]
