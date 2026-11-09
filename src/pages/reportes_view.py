"""
Vista de Informes y Estadísticas.
Permite visualizar reportes analíticos y operativos del sistema bibliotecario.

Cada informe se presenta en un menú de pestañas internas: la primera conserva
la grilla de datos y las siguientes están reservadas a los gráficos de torta.
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional
from sqlalchemy.orm import Session

from api.services.reporte_service import ReporteService
from src.components.treeview_table import TreeviewTable


class ReportesView(ttk.Frame):
    """Pestaña de Informes y Estadísticas."""

    def __init__(self, parent: tk.Widget, session: Session, **kwargs):
        super().__init__(parent, **kwargs)
        self.session = session
        self.reporte_service = ReporteService(session)

        # Gráficos de torta previstos por informe (título de la pestaña, descripción)
        self.graficos_por_informe = {
            0: [
                ("🥧 Estados Logísticos", "Distribución de los préstamos activos según el estado logístico del remito."),
                ("🥧 Locales vs. Inter-sedes", "Proporción de préstamos locales frente a interbibliotecarios."),
            ],
            1: [
                ("🥧 Estado de las Multas", "Proporción de multas pendientes, pagadas y condonadas."),
                ("🥧 Estado de Cuenta de Socios", "Socios habilitados frente a inhabilitados por deuda."),
            ],
            2: [
                ("🥧 Participación por Libro", "Participación de cada obra en el total de solicitudes inter-sedes."),
            ],
            3: [
                ("🥧 Disponibilidad Global", "Ejemplares disponibles frente a no disponibles en toda la red."),
                ("🥧 Ejemplares por Sede", "Distribución del inventario total entre las sedes activas."),
            ],
        }

        self._indice_actual: Optional[int] = None
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

        # Selector de reporte (actualización automática al seleccionar)
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

        # Contenedor del menú de pestañas del informe
        self.table_container = ttk.Frame(self, padding="15 5")
        self.table_container.grid(row=2, column=0, sticky="nsew")
        self.table_container.grid_rowconfigure(0, weight=1)
        self.table_container.grid_columnconfigure(0, weight=1)

        self.notebook_informe: Optional[ttk.Notebook] = None
        self.tabla_actual: Optional[TreeviewTable] = None
        self.ejecutar_reporte()

    def ejecutar_reporte(self) -> None:
        """Ejecuta el informe seleccionado y reconstruye su menú de pestañas (datos + gráficos)."""
        indice = self.combo_reportes.current()

        # Conservar la pestaña interna activa si se refresca el mismo informe
        pestana_previa = 0
        if self.notebook_informe is not None:
            if indice == self._indice_actual:
                try:
                    pestana_previa = self.notebook_informe.index(self.notebook_informe.select())
                except tk.TclError:
                    pestana_previa = 0
            self.notebook_informe.destroy()

        self._indice_actual = indice

        self.notebook_informe = ttk.Notebook(self.table_container)
        self.notebook_informe.grid(row=0, column=0, sticky="nsew")

        # Pestaña 1: datos actuales del informe
        tab_datos = ttk.Frame(self.notebook_informe, padding=10)
        tab_datos.grid_rowconfigure(0, weight=1)
        tab_datos.grid_columnconfigure(0, weight=1)
        self.notebook_informe.add(tab_datos, text="📋 Datos del informe")
        self._construir_tabla(tab_datos, indice)

        # Pestañas siguientes: un gráfico de torta por pestaña
        for titulo, descripcion in self.graficos_por_informe.get(indice, []):
            tab_grafico = ttk.Frame(self.notebook_informe, padding=20)
            self.notebook_informe.add(tab_grafico, text=titulo)
            self._construir_placeholder_grafico(tab_grafico, titulo, descripcion)

        total_tabs = len(self.notebook_informe.tabs())
        self.notebook_informe.select(pestana_previa if pestana_previa < total_tabs else 0)

    def _construir_placeholder_grafico(self, parent: ttk.Frame, titulo: str, descripcion: str) -> None:
        """Marcador de posición del gráfico de torta (se implementará a continuación)."""
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        ttk.Label(
            parent,
            text=titulo.replace("🥧 ", ""),
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            parent,
            text=descripcion,
            font=("Segoe UI", 10),
            foreground="#64748B",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        ttk.Label(
            parent,
            text="Gráfico de torta próximamente",
            font=("Segoe UI", 11, "italic"),
            foreground="#94A3B8",
        ).grid(row=2, column=0)

    def _construir_tabla(self, parent: ttk.Frame, indice: int) -> None:
        """Construye la grilla de datos correspondiente al informe seleccionado."""
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
            datos = self.reporte_service.reporte_prestamos_activos_y_transito()

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
            datos = self.reporte_service.reporte_vencidos_y_multas()

        elif indice == 2:
            columnas = [
                ("ranking", "Ranking", 70),
                ("isbn", "ISBN", 150),
                ("titulo", "Título del Libro", 350),
                ("total_solicitudes_intersedes", "Total Solicitudes Inter-sedes", 180),
            ]
            datos = self.reporte_service.reporte_demanda_intersedes()

        else:
            columnas = [
                ("sede", "Sede", 200),
                ("isbn", "ISBN", 140),
                ("titulo", "Título del Libro", 300),
                ("ejemplares_totales", "Ejemplares Totales", 120),
                ("ejemplares_disponibles", "Disponibles", 110),
                ("ejemplares_no_disponibles", "No Disponibles", 110),
            ]
            datos = self.reporte_service.reporte_disponibilidad_por_sede()

        self.tabla_actual = TreeviewTable(parent, columns=columnas, show_scrollbar_x=True)
        self.tabla_actual.grid(row=0, column=0, sticky="nsew")
        self.tabla_actual.cargar_datos(datos)
