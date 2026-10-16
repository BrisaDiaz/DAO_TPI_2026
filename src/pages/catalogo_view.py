"""
Vista de Catálogo de Libros y Ejemplares Físicos.
Permite consultar libros, autores e inventario de unidades por sede.
"""
import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import Session

from api.dao.libro_dao import LibroDAO
from src.components.treeview_table import TreeviewTable


class CatalogoView(ttk.Frame):
    """Pestaña de Catálogo de Libros y Ejemplares."""

    def __init__(self, parent: tk.Widget, session: Session, **kwargs):
        super().__init__(parent, **kwargs)
        self.session = session
        self.libro_dao = LibroDAO(session)

        self._crear_interfaz()

    def _crear_interfaz(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Encabezado
        header_frame = ttk.Frame(self, padding="15 10")
        header_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            header_frame,
            text="📚 Catálogo Bibliográfico",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            header_frame,
            text="Búsqueda y consulta de obras, autores, información editorial y unidades físicas en cada sede.",
            font=("Segoe UI", 10),
            foreground="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        # Contenedor central (Tabla de catálogo)
        main_content = ttk.Frame(self, padding="15 5")
        main_content.grid(row=1, column=0, sticky="nsew")
        main_content.grid_rowconfigure(0, weight=1)
        main_content.grid_columnconfigure(0, weight=1)

        columnas = [
            ("id", "ID", 50),
            ("isbn", "ISBN", 140),
            ("titulo", "Título del Libro", 300),
            ("editorial", "Editorial", 150),
            ("anio", "Año", 70),
            ("ejemplares", "Cant. Ejemplares", 110),
        ]

        self.tabla = TreeviewTable(main_content, columns=columnas)
        self.tabla.grid(row=0, column=0, sticky="nsew")

        # Barra inferior
        actions_frame = ttk.Frame(self, padding="15 10")
        actions_frame.grid(row=2, column=0, sticky="ew")

        ttk.Button(
            actions_frame,
            text="🔄 Actualizar Catálogo",
            command=self.cargar_datos,
        ).pack(side="left", padx=(0, 10))

        self.cargar_datos()

    def cargar_datos(self) -> None:
        libros = self.libro_dao.obtener_todos()
        filas = [
            {
                "id": str(l.id),
                "isbn": l.isbn,
                "titulo": l.titulo,
                "editorial": l.editorial or "-",
                "anio": str(l.anio_edicion) if l.anio_edicion else "-",
                "ejemplares": str(len(l.ejemplares)) if hasattr(l, "ejemplares") else "0",
            }
            for l in libros
        ]
        self.tabla.cargar_datos(filas)
