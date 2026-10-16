"""
Vista de Préstamos y Envíos Interbibliotecarios.
Permite registrar préstamos locales, envíos entre sedes y controlar el estado de los remitos.
"""
import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import Session

from api.dao.prestamo_dao import PrestamoDAO
from src.components.treeview_table import TreeviewTable


class PrestamosView(ttk.Frame):
    """Pestaña de Préstamos y Logística de Remitos."""

    def __init__(self, parent: tk.Widget, session: Session, **kwargs):
        super().__init__(parent, **kwargs)
        self.session = session
        self.prestamo_dao = PrestamoDAO(session)

        self._crear_interfaz()

    def _crear_interfaz(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Encabezado
        header_frame = ttk.Frame(self, padding="15 10")
        header_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            header_frame,
            text="🔄 Gestión de Préstamos y Envíos",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            header_frame,
            text="Registro de préstamos locales e interbibliotecarios, devoluciones y seguimiento de remitos en tránsito.",
            font=("Segoe UI", 10),
            foreground="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        # Contenedor central (Tabla de préstamos)
        main_content = ttk.Frame(self, padding="15 5")
        main_content.grid(row=1, column=0, sticky="nsew")
        main_content.grid_rowconfigure(0, weight=1)
        main_content.grid_columnconfigure(0, weight=1)

        columnas = [
            ("id", "ID", 50),
            ("socio", "Socio", 180),
            ("ejemplar", "Cód. Ejemplar", 120),
            ("origen", "Sede Origen", 130),
            ("destino", "Sede Destino", 130),
            ("tipo", "Tipo", 120),
            ("fecha_prestamo", "Fecha Préstamo", 110),
            ("estado", "Estado", 90),
        ]

        self.tabla = TreeviewTable(main_content, columns=columnas)
        self.tabla.grid(row=0, column=0, sticky="nsew")

        # Barra inferior
        actions_frame = ttk.Frame(self, padding="15 10")
        actions_frame.grid(row=2, column=0, sticky="ew")

        ttk.Button(
            actions_frame,
            text="🔄 Actualizar Préstamos",
            command=self.cargar_datos,
        ).pack(side="left", padx=(0, 10))

        self.cargar_datos()

    def cargar_datos(self) -> None:
        prestamos = self.prestamo_dao.obtener_todos()
        filas = [
            {
                "id": str(p.id),
                "socio": f"{p.socio.nombre} {p.socio.apellido}" if p.socio else f"ID {p.socio_id}",
                "ejemplar": p.ejemplar.codigo_inventario if p.ejemplar else f"ID {p.ejemplar_id}",
                "origen": p.sede_origen.direccion if p.sede_origen else "-",
                "destino": p.sede_destino.direccion if p.sede_destino else "Local",
                "tipo": "Interbibliotecario" if p.sede_destino_id and p.sede_destino_id != p.sede_origen_id else "Local",
                "fecha_prestamo": str(p.fecha_prestamo),
                "estado": p.estado,
            }
            for p in prestamos
        ]
        self.tabla.cargar_datos(filas)
