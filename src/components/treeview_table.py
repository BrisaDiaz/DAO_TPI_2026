"""
Componente reutilizable de tabla basado en ttk.Treeview.

Provee funcionalidades de ordenamiento por columnas, barras de desplazamiento,
filas alternadas y callbacks de selección para todas las vistas del sistema.
"""
from datetime import date, datetime
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


class TreeviewTable(ttk.Frame):
    """
    Grilla tabular reutilizable con scrollbars y soporte de ordenamiento por columna.
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
        self.titles_map = {col[0]: col[1] for col in columns}
        self.on_select_callback = on_select
        self.on_double_click_callback = on_double_click
        self._sort_reverse: Dict[str, bool] = {col[0]: False for col in columns}
        self._last_sorted_col: Optional[str] = None

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

        # Configurar columnas y encabezados interactivos para ordenamiento
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

    def _parse_value(self, val: Any) -> Any:
        """Convierte valores a tipos comparables (números, fechas o cadenas)."""
        val_str = str(val).strip()
        if not val_str or val_str == "-":
            return ""

        # Intentar parsear número/moneda
        try:
            cleaned_num = val_str.replace("$", "").replace(".", "").replace(",", ".").strip()
            return float(cleaned_num)
        except ValueError:
            pass

        # Intentar parsear fecha (AAAA-MM-DD)
        try:
            return datetime.strptime(val_str, "%Y-%m-%d")
        except ValueError:
            pass

        return val_str.lower()

    def _ordenar_por_columna(self, col_id: str) -> None:
        """Ordena los elementos de la tabla al hacer clic en el encabezado."""
        items = [(self.tree.set(k, col_id), k) for k in self.tree.get_children("")]
        reverse = self._sort_reverse[col_id]

        # Ordenar evaluando el tipo de dato
        items.sort(key=lambda t: self._parse_value(t[0]), reverse=reverse)

        # Mover filas ordenadas y rehacer el coloreado alternado
        for index, (_, k) in enumerate(items):
            self.tree.move(k, "", index)
            self.tree.item(k, tags=("even" if index % 2 == 0 else "odd",))

        # Restablecer el texto original en el encabezado previo
        if self._last_sorted_col and self._last_sorted_col != col_id:
            self.tree.heading(self._last_sorted_col, text=self.titles_map[self._last_sorted_col])

        # Actualizar el encabezado actual con la flecha de dirección
        indicador = " ▼" if reverse else " ▲"
        self.tree.heading(col_id, text=f"{self.titles_map[col_id]}{indicador}")

        # Invertir dirección para la próxima selección y guardar estado
        self._sort_reverse[col_id] = not reverse
        self._last_sorted_col = col_id

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
        """Elimina todas las filas de la tabla y restablece encabezados."""
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