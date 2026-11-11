"""
Vista de Informes y Estadísticas.
Permite visualizar reportes analíticos y operativos del sistema bibliotecario.

Cada informe se presenta en un menú de pestañas internas: la primera conserva
la grilla de datos y las siguientes muestran gráficos de torta interactivos
dibujados de forma nativa con tk.Canvas.
"""
from collections import Counter
import math
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from api.dao.multa_dao import MultaDAO
from api.dao.socio_dao import SocioDAO
from api.services.reporte_service import ReporteService
from src.components.treeview_table import TreeviewTable


PALETA_COLORES = [
    "#2563EB",  # Azul intenso
    "#10B981",  # Verde esmeralda
    "#F59E0B",  # Ámbar / Naranja
    "#EF4444",  # Rojo coral
    "#8B5CF6",  # Violeta
    "#06B6D4",  # Cian
    "#EC4899",  # Rosa
    "#64748B",  # Gris pizarra
]


class PieChartTab(ttk.Frame):
    """
    Pestaña que renderiza un gráfico de torta (Pie Chart) nativo en tk.Canvas
    junto con su leyenda detallada de cantidades y porcentajes.
    """

    def __init__(
        self,
        parent: tk.Widget,
        titulo: str,
        descripcion: str,
        items: List[Tuple[str, float]],
        unidad: str = "registros",
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.titulo = titulo
        self.descripcion = descripcion
        self.items = [(etiqueta, float(valor)) for etiqueta, valor in items if float(valor) > 0]
        self.unidad = unidad

        self._crear_widgets()

    def _crear_widgets(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Título y descripción
        ttk.Label(
            self,
            text=self.titulo.replace("🥧 ", ""),
            font=("Segoe UI", 13, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            self,
            text=self.descripcion,
            font=("Segoe UI", 10),
            foreground="#64748B",
        ).grid(row=1, column=0, sticky="w", pady=(2, 10))

        # Lienzo tk.Canvas para el gráfico de torta y su leyenda
        self.canvas = tk.Canvas(
            self,
            bg="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CBD5E1",
        )
        self.canvas.grid(row=2, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self._redibujar)

    def _redibujar(self, _event: Optional[tk.Event] = None) -> None:
        """Dibuja el gráfico de torta y el cuadro de referencias ajustado al tamaño actual."""
        self.canvas.delete("all")

        ancho = self.canvas.winfo_width()
        alto = self.canvas.winfo_height()
        if ancho <= 20 or alto <= 20:
            return

        total = sum(valor for _, valor in self.items)
        if total <= 0 or not self.items:
            cx, cy = ancho // 2, alto // 2
            r = min(ancho, alto) // 4
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill="#F1F5F9", outline="#CBD5E1", width=2,
            )
            self.canvas.create_text(
                cx, cy,
                text="Sin datos disponibles para graficar",
                font=("Segoe UI", 11, "italic"),
                fill="#64748B",
            )
            return

        # Dimensiones y posición de la torta (mitad izquierda del lienzo)
        area_torta_ancho = int(ancho * 0.52)
        cx = max(140, area_torta_ancho // 2)
        cy = alto // 2
        radio = max(60, min(int(area_torta_ancho * 0.38), int(alto * 0.38)))

        x0, y0 = cx - radio, cy - radio
        x1, y1 = cx + radio, cy + radio

        # Sombra suave de fondo para el círculo
        self.canvas.create_oval(
            x0 + 3, y0 + 4, x1 + 3, y1 + 4,
            fill="#E2E8F0", outline="",
        )

        # Caso de una única categoría con el 100% (evita bug de extent=360 en Tk)
        if len(self.items) == 1:
            color = PALETA_COLORES[0]
            self.canvas.create_oval(
                x0, y0, x1, y1,
                fill=color, outline="#FFFFFF", width=2,
            )
            self.canvas.create_text(
                cx, cy,
                text="100.0%",
                font=("Segoe UI", 11, "bold"),
                fill="#FFFFFF",
            )
        else:
            angulo_inicio = 90.0  # Comenzar desde arriba (12 en punto)
            for idx, (etiqueta, valor) in enumerate(self.items):
                porcion = (valor / total) * 360.0
                color = PALETA_COLORES[idx % len(PALETA_COLORES)]

                self.canvas.create_arc(
                    x0, y0, x1, y1,
                    start=angulo_inicio,
                    extent=-porcion,  # Sentido horario
                    fill=color,
                    outline="#FFFFFF",
                    width=2,
                    style="pieslice",
                )

                # Etiqueta de porcentaje dentro de la porción si tiene suficiente tamaño
                porcentaje = (valor / total) * 100.0
                if porcentaje >= 6.0:
                    angulo_medio = angulo_inicio - (porcion / 2.0)
                    rad = math.radians(angulo_medio)
                    r_texto = radio * 0.62
                    tx = cx + math.cos(rad) * r_texto
                    ty = cy - math.sin(rad) * r_texto
                    self.canvas.create_text(
                        tx, ty,
                        text=f"{porcentaje:.1f}%",
                        font=("Segoe UI", 9, "bold"),
                        fill="#FFFFFF",
                    )

                angulo_inicio -= porcion

        # Panel de leyenda y resumen estadístico (mitad derecha del lienzo)
        leyenda_x = max(cx + radio + 35, int(ancho * 0.50))
        leyenda_ancho = max(220, ancho - leyenda_x - 30)
        fila_alto = 30
        alto_caja = 65 + len(self.items) * fila_alto
        leyenda_y = max(20, (alto - alto_caja) // 2)

        # Contenedor de la leyenda
        self.canvas.create_rectangle(
            leyenda_x,
            leyenda_y,
            leyenda_x + leyenda_ancho,
            leyenda_y + alto_caja,
            fill="#F8FAFC",
            outline="#E2E8F0",
            width=1,
        )

        self.canvas.create_text(
            leyenda_x + 16,
            leyenda_y + 18,
            text="Referencias y Distribución",
            font=("Segoe UI", 10, "bold"),
            fill="#1E293B",
            anchor="w",
        )

        self.canvas.create_line(
            leyenda_x + 12,
            leyenda_y + 34,
            leyenda_x + leyenda_ancho - 12,
            leyenda_y + 34,
            fill="#E2E8F0",
        )

        for idx, (etiqueta, valor) in enumerate(self.items):
            color = PALETA_COLORES[idx % len(PALETA_COLORES)]
            porcentaje = (valor / total) * 100.0
            y_item = leyenda_y + 50 + idx * fila_alto

            # Muestra de color
            self.canvas.create_rectangle(
                leyenda_x + 16,
                y_item - 7,
                leyenda_x + 30,
                y_item + 7,
                fill=color,
                outline="#FFFFFF",
            )

            # Nombre de la categoría (truncado si es muy largo)
            texto_cat = etiqueta if len(etiqueta) <= 32 else etiqueta[:29] + "..."
            self.canvas.create_text(
                leyenda_x + 40,
                y_item,
                text=texto_cat,
                font=("Segoe UI", 9),
                fill="#334155",
                anchor="w",
            )

            # Cantidad y porcentaje alineados a la derecha
            valor_fmt = int(valor) if valor.is_integer() else f"{valor:,.2f}"
            self.canvas.create_text(
                leyenda_x + leyenda_ancho - 16,
                y_item,
                text=f"{valor_fmt} ({porcentaje:.1f}%)",
                font=("Segoe UI", 9, "bold"),
                fill="#0F172A",
                anchor="e",
            )

        # Pie con el total general
        y_total = leyenda_y + alto_caja - 14
        self.canvas.create_line(
            leyenda_x + 12,
            y_total - 14,
            leyenda_x + leyenda_ancho - 12,
            y_total - 14,
            fill="#CBD5E1",
        )
        total_fmt = int(total) if total.is_integer() else f"{total:,.2f}"
        self.canvas.create_text(
            leyenda_x + 16,
            y_total,
            text=f"Total: {total_fmt} {self.unidad}",
            font=("Segoe UI", 9, "bold"),
            fill="#1E3A8A",
            anchor="w",
        )


class ReportesView(ttk.Frame):
    """Pestaña de Informes y Estadísticas."""

    def __init__(self, parent: tk.Widget, session: Session, **kwargs):
        super().__init__(parent, **kwargs)
        self.session = session
        self.reporte_service = ReporteService(session)
        self.multa_dao = MultaDAO(session)
        self.socio_dao = SocioDAO(session)

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
        datos = self._construir_tabla(tab_datos, indice)

        # Pestañas siguientes: gráficos de torta en tk.Canvas
        for titulo, descripcion, items, unidad in self._obtener_graficos_informe(indice, datos):
            tab_grafico = PieChartTab(
                self.notebook_informe,
                titulo=titulo,
                descripcion=descripcion,
                items=items,
                unidad=unidad,
                padding="20 15",
            )
            self.notebook_informe.add(tab_grafico, text=titulo)

        total_tabs = len(self.notebook_informe.tabs())
        self.notebook_informe.select(pestana_previa if pestana_previa < total_tabs else 0)

    def _obtener_graficos_informe(
        self, indice: int, datos: List[Dict[str, Any]]
    ) -> List[Tuple[str, str, List[Tuple[str, float]], str]]:
        """Calcula las series de datos para los gráficos de torta de cada informe."""
        if indice == 0:
            conteo_estados = Counter(d.get("estado_logistico", "Sin estado") for d in datos)
            conteo_tipos = Counter(d.get("tipo_prestamo", "Local") for d in datos)
            return [
                (
                    "🥧 Estados Logísticos",
                    "Distribución de los préstamos activos según el estado logístico del remito.",
                    list(conteo_estados.items()),
                    "préstamos activos",
                ),
                (
                    "🥧 Locales vs. Inter-sedes",
                    "Proporción de préstamos locales frente a préstamos interbibliotecarios.",
                    list(conteo_tipos.items()),
                    "préstamos activos",
                ),
            ]

        if indice == 1:
            todas_multas = self.multa_dao.obtener_todos()
            conteo_multas = Counter(m.estado for m in todas_multas)
            orden_estados = ["Pendiente", "Pagada", "Condonada"]
            items_multas = [
                (est, conteo_multas[est]) for est in orden_estados if conteo_multas.get(est, 0) > 0
            ]

            todos_socios = self.socio_dao.obtener_todos()
            habilitados = sum(1 for s in todos_socios if s.activo == 1)
            inhabilitados = sum(1 for s in todos_socios if s.activo != 1)
            items_socios = [
                ("Habilitados", habilitados),
                ("Inhabilitados por Deuda", inhabilitados),
            ]
            return [
                (
                    "🥧 Estado de las Multas",
                    "Proporción de sanciones registradas según su estado (Pendiente, Pagada o Condonada).",
                    items_multas,
                    "multas",
                ),
                (
                    "🥧 Estado de Cuenta de Socios",
                    "Relación de socios habilitados frente a socios inhabilitados en el padrón.",
                    items_socios,
                    "socios",
                ),
            ]

        if indice == 2:
            items_libros = [
                (str(d.get("titulo", "-")), float(d.get("total_solicitudes_intersedes", 0)))
                for d in datos
            ]
            return [
                (
                    "🥧 Participación por Libro",
                    "Participación de cada obra en el total de solicitudes interbibliotecarias entre sedes.",
                    items_libros,
                    "solicitudes inter-sedes",
                ),
            ]

        # Informe 3: Disponibilidad de Catálogo por Sede
        total_disp = sum(int(d.get("ejemplares_disponibles", 0)) for d in datos)
        total_no_disp = sum(int(d.get("ejemplares_no_disponibles", 0)) for d in datos)
        items_disp = [
            ("Disponibles en estantería", total_disp),
            ("No disponibles (Prestados / Dañados)", total_no_disp),
        ]

        por_sede: Dict[str, int] = {}
        for d in datos:
            sede_nom = str(d.get("sede", "-"))
            por_sede[sede_nom] = por_sede.get(sede_nom, 0) + int(d.get("ejemplares_totales", 0))

        return [
            (
                "🥧 Disponibilidad Global",
                "Proporción de ejemplares disponibles frente a no disponibles en todas las sedes activas.",
                items_disp,
                "ejemplares",
            ),
            (
                "🥧 Ejemplares por Sede",
                "Distribución del inventario físico total entre las sedes activas de la red.",
                list(por_sede.items()),
                "ejemplares",
            ),
        ]

    def _construir_tabla(self, parent: ttk.Frame, indice: int) -> List[Dict[str, Any]]:
        """Construye la grilla de datos correspondiente al informe seleccionado y retorna sus filas."""
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
        return datos
