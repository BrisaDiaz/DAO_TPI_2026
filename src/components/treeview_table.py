"""
Componente reutilizable de tabla basado en ttk.Treeview.

Provee funcionalidades de ordenamiento por columnas, barras de desplazamiento,
filas alternadas y callbacks de selección para todas las vistas del sistema.
"""
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


class TreeviewTable(ttk.Frame):
    """
    Grilla tabular reutilizable con scrollbars y estilos configurados.
    """

    def __init__(
        self,
        parent: tk.Widget,
        columns: List[Tuple[str, str, int]],  # [(col_id, col_title, width), ...]
        on_select: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_double_click: Optional[Callable[[Dict[str, Any]], None]] = None,
        show_scrollbar_x: bool = False,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self.columns_info = columns
        self.column_ids = [col[0] for col in columns]
        self.on_select_callback = on_select
        self.on_double_click_callback = on_double_click
        self._sort_reverse: Dict[str, bool] = {col[0]: False for col in columns}

        self._crear_widgets(show_scrollbar_x)

    def _crear_widgets(self, show_scrollbar_x: bool) -> None:
        """Inicializa el Treeview y sus scrollbars."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Treeview
        self.tree = ttk.Treeview(
            self,
            columns=self.column_ids,
            show="headings",
            selectmode="browse",
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Configurar columnas
        for col_id, col_title, width in self.columns_info:
            self.tree.heading(
                col_id,
                text=col_title,
                command=lambda c=col_id: self._ordenar_por_columna(c),
            )
            self.tree.column(col_id, width=width, minwidth=50, anchor="w")

        # Scrollbar vertical
        scrollbar_y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.grid(row=0, column=1, sticky="ns")

        # Scrollbar horizontal (opcional)
        if show_scrollbar_x:
            scrollbar_x = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
            self.tree.configure(xscrollcommand=scrollbar_x.set)
            scrollbar_x.grid(row=1, column=0, sticky="ew")

        # Configurar colores de filas alternadas
        self.tree.tag_configure("even", background="#FFFFFF")
        self.tree.tag_configure("odd", background="#F8FAFC")

        # Eventos
        self.tree.bind("<<TreeviewSelect>>", self._on_treeview_select)
        if self.on_double_click_callback:
            self.tree.bind("<Double-1>", self._on_treeview_double_click)

    def _ordenar_por_columna(self, col_id: str) -> None:
        """Ordena los elementos de la tabla al hacer clic en el encabezado."""
        items = [(self.tree.set(k, col_id), k) for k in self.tree.get_children("")]

        # Intentar ordenar como número si es posible, sino como texto
        try:
            items.sort(key=lambda t: float(t[0].replace("$", "").replace(".", "").replace(",", ".").strip()), reverse=self._sort_reverse[col_id])
        except (ValueError, TypeError):
            items.sort(key=lambda t: str(t[0]).lower(), reverse=self._sort_reverse[col_id])

        for index, (_, k) in enumerate(items):
            self.tree.move(k, "", index)
            self.tree.item(k, tags=("even" if index % 2 == 0 else "odd",))

        # Invertir dirección para el próximo clic
        self._sort_reverse[col_id] = not self._sort_reverse[col_id]

    def _on_treeview_select(self, event: tk.Event) -> None:
        """Maneja el evento de selección de fila."""
        if not self.on_select_callback:
            return
        selected = self.get_selected_row()
        if selected is not None:
            self.on_select_callback(selected)

    def _on_treeview_double_click(self, event: tk.Event) -> None:
        """Maneja el evento de doble clic en una fila."""
        if not self.on_double_click_callback:
            return
        selected = self.get_selected_row()
        if selected is not None:
            self.on_double_click_callback(selected)

    def limpiar(self) -> None:
        """Elimina todas las filas de la tabla."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def cargar_datos(self, filas: List[Union[Dict[str, Any], Tuple, List]]) -> None:
        """
        Limpia y carga una nueva lista de filas en el Treeview con estilo alternado.
        Soporta listas de diccionarios o tuplas/listas posicionales.
        """
        self.limpiar()
        for idx, fila in enumerate(filas):
            tag = "even" if idx % 2 == 0 else "odd"
            if isinstance(fila, dict):
                valores = [fila.get(col_id, "") for col_id in self.column_ids]
            else:
                valores = list(fila)
            self.tree.insert("", "end", values=valores, tags=(tag,))

    def get_selected_row(self) -> Optional[Dict[str, Any]]:
        """Retorna los valores de la fila actualmente seleccionada como diccionario."""
        selected_items = self.tree.selection()
        if not selected_items:
            return None
        item_id = selected_items[0]
        values = self.tree.item(item_id, "values")
        return {col_id: values[i] if i < len(values) else None for i, col_id in enumerate(self.column_ids)}
