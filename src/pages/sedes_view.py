"""
Vista de Gestión de Sedes.
Permite consultar, registrar y administrar las sucursales de la red bibliotecaria.
"""
import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import Session

from api.dao.sede_dao import SedeDAO
from src.components.treeview_table import TreeviewTable


class SedesView(ttk.Frame):
    """Pestaña de Gestión de Sedes."""

    def __init__(self, parent: tk.Widget, session: Session, **kwargs):
        super().__init__(parent, **kwargs)
        self.session = session
        self.sede_dao = SedeDAO(session)

        self._crear_interfaz()

    def _crear_interfaz(self) -> None:
        """Construye los elementos visuales de la vista de sedes."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Encabezado
        header_frame = ttk.Frame(self, padding="15 10")
        header_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            header_frame,
            text="🏢 Gestión de Sedes",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            header_frame,
            text="Consulta, alta y administración de las sucursales habilitadas en la red de bibliotecas.",
            font=("Segoe UI", 10),
            foreground="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        # Contenedor central (Tabla de sedes)
        main_content = ttk.Frame(self, padding="15 5")
        main_content.grid(row=1, column=0, sticky="nsew")
        main_content.grid_rowconfigure(0, weight=1)
        main_content.grid_columnconfigure(0, weight=1)

        columnas = [
            ("id", "ID", 60),
            ("direccion", "Dirección de la Sede", 350),
            ("estado", "Estado Operativo", 120),
        ]

        self.tabla = TreeviewTable(main_content, columns=columnas)
        self.tabla.grid(row=0, column=0, sticky="nsew")

        # Barra de acciones inferior
        actions_frame = ttk.Frame(self, padding="15 10")
        actions_frame.grid(row=2, column=0, sticky="ew")

        ttk.Button(
            actions_frame,
            text="🔄 Actualizar Listado",
            command=self.cargar_datos,
        ).pack(side="left", padx=(0, 10))

        self.cargar_datos()

    def cargar_datos(self) -> None:
        """Carga las sedes registradas desde la base de datos."""
        sedes = self.sede_dao.obtener_todos()
        filas = [
            {
                "id": str(s.id),
                "direccion": s.direccion,
                "estado": "Activa" if s.estado == "activo" else "Inactiva",
            }
            for s in sedes
        ]
        self.tabla.cargar_datos(filas)
