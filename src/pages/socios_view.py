"""
Vista de Gestión de Socios.
Permite consultar socios, actualizar estados de cuenta y regularizar sanciones.
"""
import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import Session

from api.dao.socio_dao import SocioDAO
from src.components.treeview_table import TreeviewTable


class SociosView(ttk.Frame):
    """Pestaña de Gestión de Socios."""

    def __init__(self, parent: tk.Widget, session: Session, **kwargs):
        super().__init__(parent, **kwargs)
        self.session = session
        self.socio_dao = SocioDAO(session)

        self._crear_interfaz()

    def _crear_interfaz(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Encabezado
        header_frame = ttk.Frame(self, padding="15 10")
        header_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            header_frame,
            text="👥 Gestión de Socios",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            header_frame,
            text="Consulta y administración del padrón de socios, verificación de estados de cuenta y cobro de multas.",
            font=("Segoe UI", 10),
            foreground="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        # Contenedor central (Tabla de socios)
        main_content = ttk.Frame(self, padding="15 5")
        main_content.grid(row=1, column=0, sticky="nsew")
        main_content.grid_rowconfigure(0, weight=1)
        main_content.grid_columnconfigure(0, weight=1)

        columnas = [
            ("id", "ID", 50),
            ("numero_socio", "Nro. Socio", 100),
            ("nombre_completo", "Nombre y Apellido", 250),
            ("dni", "DNI", 110),
            ("email", "Email", 220),
            ("estado", "Estado de Cuenta", 120),
        ]

        self.tabla = TreeviewTable(main_content, columns=columnas)
        self.tabla.grid(row=0, column=0, sticky="nsew")

        # Barra inferior
        actions_frame = ttk.Frame(self, padding="15 10")
        actions_frame.grid(row=2, column=0, sticky="ew")

        ttk.Button(
            actions_frame,
            text="🔄 Actualizar Listado",
            command=self.cargar_datos,
        ).pack(side="left", padx=(0, 10))

        self.cargar_datos()

    def cargar_datos(self) -> None:
        socios = self.socio_dao.obtener_todos()
        filas = [
            {
                "id": str(s.id),
                "numero_socio": s.numero_socio,
                "nombre_completo": f"{s.nombre} {s.apellido}",
                "dni": s.dni,
                "email": s.email,
                "estado": "Habilitado" if s.activo else "Inhabilitado",
            }
            for s in socios
        ]
        self.tabla.cargar_datos(filas)
