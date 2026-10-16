"""
Vista de Informes y Estadísticas.
Permite visualizar reportes analíticos y operativos del sistema bibliotecario.
"""
import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import Session

from api.services.reporte_service import ReporteService
from src.components.treeview_table import TreeviewTable


class ReportesView(ttk.Frame):
    """Pestaña de Informes y Estadísticas."""

    def __init__(self, parent: tk.Widget, session: Session, **kwargs):
        super().__init__(parent, **kwargs)
        self.session = session
        self.reporte_service = ReporteService(session)

        self._crear_interfaz()

    def _crear_interfaz(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Encabezado
        header_frame = ttk.Frame(self, padding="15 10")
        header_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            header_frame,
            text="📊 Informes & Estadísticas",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            header_frame,
            text="Visualización de informes de circulación, control de préstamos vencidos, demanda entre sedes e inventario disponible.",
            font=("Segoe UI", 10),
            foreground="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        # Selector de reporte
        selector_frame = ttk.Frame(self, padding="15 5")
        selector_frame.grid(row=1, column=0, sticky="ew")

        ttk.Label(selector_frame, text="Seleccionar Informe: ", font=("Segoe UI", 10, "bold")).pack(side="left")

        self.opciones_reportes = [
            "1. Préstamos Activos y Material en Tránsito",
            "2. Préstamos Vencidos y Multas Acumuladas",
            "3. Libros Más Solicitados Inter-sedes",
            "4. Disponibilidad de Catálogo por Sede",
        ]

        self.combo_reportes = ttk.Combobox(
            selector_frame,
            values=self.opciones_reportes,
            state="readonly",
            width=45,
            font=("Segoe UI", 10),
        )
        self.combo_reportes.current(0)
        self.combo_reportes.pack(side="left", padx=10)
        self.combo_reportes.bind("<<ComboboxSelected>>", lambda e: self.ejecutar_reporte())

        ttk.Button(
            selector_frame,
            text="▶ Consultar Informe",
            command=self.ejecutar_reporte,
        ).pack(side="left", padx=5)

        # Contenedor para la tabla de resultados
        self.table_container = ttk.Frame(self, padding="15 5")
        self.table_container.grid(row=2, column=0, sticky="nsew")
        self.table_container.grid_rowconfigure(0, weight=1)
        self.table_container.grid_columnconfigure(0, weight=1)

        self.tabla_actual: TreeviewTable | None = None
        self.ejecutar_reporte()

    def ejecutar_reporte(self) -> None:
        """Ejecuta el informe seleccionado y actualiza la grilla con sus columnas correspondientes."""
        indice = self.combo_reportes.current()

        if self.tabla_actual:
            self.tabla_actual.destroy()

        if indice == 0:
            columnas = [
                ("id_prestamo", "ID", 50),
                ("titulo_libro", "Título del Libro", 250),
                ("codigo_inventario", "Cód. Ejemplar", 110),
                ("sede_origen", "Sede Origen", 160),
                ("sede_destino", "Sede Destino", 160),
                ("tipo_prestamo", "Tipo", 120),
                ("socio_nombre", "Socio", 180),
                ("fecha_prestamo", "F. Préstamo", 100),
                ("estado_logistico", "Estado Logístico", 150),
            ]
            self.tabla_actual = TreeviewTable(self.table_container, columns=columnas)
            self.tabla_actual.grid(row=0, column=0, sticky="nsew")
            datos = self.reporte_service.reporte_prestamos_activos_y_transito()
            self.tabla_actual.cargar_datos(datos)

        elif indice == 1:
            columnas = [
                ("numero_socio", "Nro. Socio", 100),
                ("socio_nombre", "Socio", 200),
                ("email", "Email", 220),
                ("titulo_libro", "Libro Adeudado", 250),
                ("fecha_devolucion_estimada", "F. Est. Devolución", 120),
                ("dias_retraso", "Días Retraso", 90),
                ("multa_acumulada", "Multa Acumulada ($)", 130),
                ("estado_cuenta", "Estado Cuenta", 140),
            ]
            self.tabla_actual = TreeviewTable(self.table_container, columns=columnas)
            self.tabla_actual.grid(row=0, column=0, sticky="nsew")
            datos = self.reporte_service.reporte_vencidos_y_multas()
            self.tabla_actual.cargar_datos(datos)

        elif indice == 2:
            columnas = [
                ("ranking", "Ranking", 70),
                ("isbn", "ISBN", 150),
                ("titulo", "Título del Libro", 350),
                ("total_solicitudes_intersedes", "Total Solicitudes Inter-sedes", 180),
            ]
            self.tabla_actual = TreeviewTable(self.table_container, columns=columnas)
            self.tabla_actual.grid(row=0, column=0, sticky="nsew")
            datos = self.reporte_service.reporte_demanda_intersedes()
            self.tabla_actual.cargar_datos(datos)

        elif indice == 3:
            columnas = [
                ("sede", "Sede", 200),
                ("isbn", "ISBN", 140),
                ("titulo", "Título del Libro", 300),
                ("ejemplares_totales", "Ejemplares Totales", 120),
                ("ejemplares_disponibles", "Disponibles", 110),
                ("ejemplares_no_disponibles", "No Disponibles", 110),
            ]
            self.tabla_actual = TreeviewTable(self.table_container, columns=columnas)
            self.tabla_actual.grid(row=0, column=0, sticky="nsew")
            datos = self.reporte_service.reporte_disponibilidad_por_sede()
            self.tabla_actual.cargar_datos(datos)
