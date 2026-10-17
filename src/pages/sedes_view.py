"""
Vista de Gestión de Sedes (ABMC Completo con TimePicker Dual y Filtro de Estados).

Permite consultar, buscar, filtrar (Todas / Solo Activas / Solo Inactivas),
registrar nuevas sucursales, modificar datos y gestionar el estado operativo.
"""
import re
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
from sqlalchemy.orm import Session

from api.models import Sede
from api.dao.sede_dao import SedeDAO
from src.components.treeview_table import TreeviewTable
from src.components.time_picker import TimePickerDual


class SedeFormModal(tk.Toplevel):
    """Modal emergente para Alta y Modificación de Sede con Spinbox Dual de Horarios."""

    def __init__(
        self,
        parent: tk.Widget,
        sede_dao: SedeDAO,
        sede: Optional[Sede] = None,
        on_guardar_callback: Optional[callable] = None,
    ):
        super().__init__(parent)
        self.sede_dao = sede_dao
        self.sede = sede
        self.on_guardar_callback = on_guardar_callback

        es_edicion = sede is not None
        self.title("Modificar Sede" if es_edicion else "Nueva Sede")
        self.geometry("520x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._centrar(parent)
        self._crear_formulario(es_edicion)

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 520) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 420) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _crear_formulario(self, es_edicion: bool) -> None:
        padding_frame = ttk.Frame(self, padding="25 20")
        padding_frame.pack(fill="both", expand=True)

        titulo_modal = "✏️ Modificar Sede" if es_edicion else "➕ Registrar Nueva Sede"
        ttk.Label(
            padding_frame,
            text=titulo_modal,
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 15))

        # Campos
        form_frame = ttk.Frame(padding_frame)
        form_frame.pack(fill="x", expand=True)

        # 1. Dirección
        ttk.Label(form_frame, text="Dirección (*):", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w", pady=8
        )
        self.txt_direccion = ttk.Entry(form_frame, width=38, font=("Segoe UI", 10))
        self.txt_direccion.grid(row=0, column=1, sticky="w", pady=8)
        if self.sede:
            self.txt_direccion.insert(0, self.sede.direccion or "")

        # 2. Contacto / Teléfono
        ttk.Label(form_frame, text="Contacto / Tel:", font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky="w", pady=8
        )
        self.txt_contacto = ttk.Entry(form_frame, width=38, font=("Segoe UI", 10))
        self.txt_contacto.grid(row=1, column=1, sticky="w", pady=8)
        if self.sede:
            self.txt_contacto.insert(0, self.sede.contacto or "")

        # 3. Días de atención
        ttk.Label(form_frame, text="Días de atención:", font=("Segoe UI", 9)).grid(
            row=2, column=0, sticky="w", pady=8
        )
        self.combo_dias = ttk.Combobox(
            form_frame,
            values=[
                "Lunes a Viernes",
                "Lunes a Sábados",
                "Lunes a Domingos",
                "Fines de semana",
            ],
            state="readonly",
            width=36,
            font=("Segoe UI", 10),
        )
        self.combo_dias.set("Lunes a Viernes")
        self.combo_dias.grid(row=2, column=1, sticky="w", pady=8)

        # 4. Rango de Horarios con Spinbox Dual (Apertura y Cierre)
        ttk.Label(form_frame, text="Horario (HH:MM):", font=("Segoe UI", 9)).grid(
            row=3, column=0, sticky="w", pady=8
        )
        time_container = ttk.Frame(form_frame)
        time_container.grid(row=3, column=1, sticky="w", pady=8)

        ttk.Label(time_container, text="Apertura:").pack(side="left", padx=(0, 4))
        self.picker_apertura = TimePickerDual(time_container, hora_inicial=8, minuto_inicial=0)
        self.picker_apertura.pack(side="left", padx=(0, 15))

        ttk.Label(time_container, text="Cierre:").pack(side="left", padx=(0, 4))
        self.picker_cierre = TimePickerDual(time_container, hora_inicial=18, minuto_inicial=0)
        self.picker_cierre.pack(side="left")

        # Cargar datos de horarios previos si se está editando
        if self.sede and self.sede.horarios:
            self._cargar_horarios_existentes(self.sede.horarios)

        # 5. Estado operativo
        ttk.Label(form_frame, text="Estado operativo:", font=("Segoe UI", 9)).grid(
            row=4, column=0, sticky="w", pady=8
        )
        self.combo_estado = ttk.Combobox(
            form_frame,
            values=["Activa", "Inactiva"],
            state="readonly",
            width=36,
            font=("Segoe UI", 10),
        )
        estado_actual = "Activa" if (not self.sede or self.sede.estado == "activo") else "Inactiva"
        self.combo_estado.set(estado_actual)
        self.combo_estado.grid(row=4, column=1, sticky="w", pady=8)

        # Botones de acción
        btn_frame = ttk.Frame(padding_frame)
        btn_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=(10, 0))
        ttk.Button(btn_frame, text="Guardar Sede", command=self._guardar).pack(side="right")

        self.txt_direccion.focus()

    def _cargar_horarios_existentes(self, horarios_str: str) -> None:
        """Intenta parsear el formato guardado y colocarlo en los Spinboxes y Combobox."""
        patron = r"^(.*?)\s+de\s+(\d{1,2}:\d{2})\s+a\s+(\d{1,2}:\d{2})"
        match = re.search(patron, horarios_str, re.IGNORECASE)
        if match:
            dias = match.group(1).strip()
            desde = match.group(2)
            hasta = match.group(3)
            if dias in self.combo_dias["values"]:
                self.combo_dias.set(dias)
            self.picker_apertura.set_time(desde)
            self.picker_cierre.set_time(hasta)
        else:
            horas = re.findall(r"\b\d{1,2}(?::\d{2})?\b", horarios_str)
            if len(horas) >= 2:
                self.picker_apertura.set_time(horas[0] if ":" in horas[0] else f"{horas[0]}:00")
                self.picker_cierre.set_time(horas[1] if ":" in horas[1] else f"{horas[1]}:00")

    def _guardar(self) -> None:
        direccion = self.txt_direccion.get().strip()
        contacto = self.txt_contacto.get().strip()
        dias = self.combo_dias.get().strip()
        hora_apertura = self.picker_apertura.get_time()
        hora_cierre = self.picker_cierre.get_time()
        estado = "activo" if self.combo_estado.get() == "Activa" else "baja"

        if not direccion:
            messagebox.showwarning("Dato requerido", "La dirección de la sede es obligatoria.", parent=self)
            self.txt_direccion.focus()
            return

        # Validación lógica de horario
        if hora_apertura >= hora_cierre:
            messagebox.showwarning(
                "Horario inválido",
                f"La hora de cierre ({hora_cierre}) debe ser posterior a la de apertura ({hora_apertura}).",
                parent=self,
            )
            return

        horarios_normalizado = f"{dias} de {hora_apertura} a {hora_cierre} hs"

        sede_existente = self.sede_dao.obtener_por_direccion(direccion)
        if sede_existente:
            if not self.sede or sede_existente.id != self.sede.id:
                messagebox.showerror(
                    "Dirección duplicada",
                    f"Ya existe una sede registrada con la dirección '{direccion}'.",
                    parent=self,
                )
                self.txt_direccion.focus()
                return

        try:
            if self.sede:
                self.sede.direccion = direccion
                self.sede.contacto = contacto
                self.sede.horarios = horarios_normalizado
                self.sede.estado = estado
                self.sede_dao.actualizar()
                messagebox.showinfo("Éxito", "Sede actualizada correctamente.", parent=self)
            else:
                nueva = Sede(
                    direccion=direccion,
                    contacto=contacto,
                    horarios=horarios_normalizado,
                    estado=estado,
                )
                self.sede_dao.crear(nueva)
                messagebox.showinfo("Éxito", "Sede registrada exitosamente.", parent=self)

            if self.on_guardar_callback:
                self.on_guardar_callback()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error al guardar", f"No se pudo guardar la sede: {e}", parent=self)


class SedesView(ttk.Frame):
    """Pestaña de Gestión de Sedes (Consulta, Búsqueda, Filtro de Estado, Alta, Modificación y Baja)."""

    def __init__(self, parent: tk.Widget, session: Session, **kwargs):
        super().__init__(parent, **kwargs)
        self.session = session
        self.sede_dao = SedeDAO(session)

        self._crear_interfaz()

    def _crear_interfaz(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Encabezado
        header_frame = ttk.Frame(self, padding="15 10")
        header_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            header_frame,
            text="🏢 Gestión de Sedes",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            header_frame,
            text="Consulta, alta, edición y control de disponibilidad operativa de las sucursales de la red.",
            font=("Segoe UI", 10),
            foreground="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        # 2. Barra de Búsqueda y Filtros
        filter_frame = ttk.Frame(self, padding="15 5")
        filter_frame.grid(row=1, column=0, sticky="ew")

        ttk.Label(filter_frame, text="Buscar dirección:", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.txt_buscar = ttk.Entry(filter_frame, width=28, font=("Segoe UI", 9))
        self.txt_buscar.pack(side="left", padx=(6, 8))
        self.txt_buscar.bind("<Return>", lambda e: self.cargar_datos())

        ttk.Button(
            filter_frame,
            text="🔍 Buscar",
            command=self.cargar_datos,
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            filter_frame,
            text="Limpiar",
            command=self._limpiar_filtro,
        ).pack(side="left", padx=(0, 15))

        # Filtro de Estado (Todas / Solo Activas / Solo Inactivas)
        ttk.Label(filter_frame, text="Estado:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(5, 5))
        self.combo_filtro_estado = ttk.Combobox(
            filter_frame,
            values=["Todas", "Solo Activas", "Solo Inactivas"],
            state="readonly",
            width=15,
            font=("Segoe UI", 9),
        )
        self.combo_filtro_estado.set("Todas")
        self.combo_filtro_estado.pack(side="left")
        self.combo_filtro_estado.bind("<<ComboboxSelected>>", lambda e: self.cargar_datos())

        # 3. Contenedor central (Tabla de sedes)
        main_content = ttk.Frame(self, padding="15 5")
        main_content.grid(row=2, column=0, sticky="nsew")
        main_content.grid_rowconfigure(0, weight=1)
        main_content.grid_columnconfigure(0, weight=1)

        columnas = [
            ("id", "ID", 60),
            ("direccion", "Dirección de la Sede", 320),
            ("contacto", "Contacto / Teléfono", 180),
            ("horarios", "Horarios de Atención", 240),
            ("estado", "Estado Operativo", 130),
        ]

        self.tabla = TreeviewTable(
            main_content,
            columns=columnas,
            on_double_click=lambda row: self._abrir_modal_modificar(),
        )
        self.tabla.grid(row=0, column=0, sticky="nsew")

        # 4. Barra de Acciones inferior (Botones ABMC)
        actions_frame = ttk.Frame(self, padding="15 10")
        actions_frame.grid(row=3, column=0, sticky="ew")

        ttk.Button(
            actions_frame,
            text="➕ Nueva Sede",
            command=self._abrir_modal_alta,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="✏️ Modificar",
            command=self._abrir_modal_modificar,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="🔄 Cambiar Estado (Baja / Alta)",
            command=self._cambiar_estado_sede,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="🗑️ Eliminar",
            command=self._eliminar_sede,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="🔄 Actualizar",
            command=self.cargar_datos,
        ).pack(side="right")

        self.cargar_datos()

    def _limpiar_filtro(self) -> None:
        self.txt_buscar.delete(0, tk.END)
        self.combo_filtro_estado.set("Todas")
        self.cargar_datos()

    def cargar_datos(self) -> None:
        """Carga y filtra las sedes según texto y estado (Todas, Activas o Inactivas)."""
        filtro_texto = self.txt_buscar.get().strip().lower()
        filtro_estado = self.combo_filtro_estado.get()

        if filtro_estado == "Solo Activas":
            sedes = self.sede_dao.obtener_activas()
        elif filtro_estado == "Solo Inactivas":
            # Filtra en memoria las sedes inactivas sobre el listado total, sin alterar /api
            sedes = [s for s in self.sede_dao.obtener_todos() if s.estado != "activo"]
        else:
            sedes = self.sede_dao.obtener_todos()

        if filtro_texto:
            sedes = [s for s in sedes if filtro_texto in (s.direccion or "").lower()]

        filas = [
            {
                "id": str(s.id),
                "direccion": s.direccion or "-",
                "contacto": s.contacto or "-",
                "horarios": s.horarios or "-",
                "estado": "Activa" if s.estado == "activo" else "Inactiva (Baja)",
            }
            for s in sedes
        ]
        self.tabla.cargar_datos(filas)

    def _obtener_sede_seleccionada(self) -> Optional[Sede]:
        """Obtiene la entidad Sede correspondiente a la fila seleccionada."""
        fila = self.tabla.get_selected_row()
        if not fila or not fila.get("id"):
            messagebox.showwarning("Selección requerida", "Por favor, seleccione una sede de la lista.")
            return None
        try:
            sede_id = int(fila["id"])
            sede = self.sede_dao.obtener_por_id(sede_id)
            if not sede:
                messagebox.showerror("Error", "No se encontró el registro de la sede seleccionada.")
                return None
            return sede
        except (ValueError, TypeError):
            return None

    def _abrir_modal_alta(self) -> None:
        """Abre el formulario para registrar una nueva sede."""
        SedeFormModal(
            parent=self.winfo_toplevel(),
            sede_dao=self.sede_dao,
            on_guardar_callback=self.cargar_datos,
        )

    def _abrir_modal_modificar(self) -> None:
        """Abre el formulario para editar la sede seleccionada."""
        sede = self._obtener_sede_seleccionada()
        if not sede:
            return
        SedeFormModal(
            parent=self.winfo_toplevel(),
            sede_dao=self.sede_dao,
            sede=sede,
            on_guardar_callback=self.cargar_datos,
        )

    def _cambiar_estado_sede(self) -> None:
        """Baja o reactivación lógica de la sede seleccionada."""
        sede = self._obtener_sede_seleccionada()
        if not sede:
            return

        nuevo_estado = "baja" if sede.estado == "activo" else "activo"
        accion_desc = "dar de baja (inactivar)" if nuevo_estado == "baja" else "reactivar"

        confirmar = messagebox.askyesno(
            "Confirmar cambio de estado",
            f"¿Está seguro de que desea {accion_desc} la sede '{sede.direccion}'?",
        )
        if not confirmar:
            return

        try:
            sede.estado = nuevo_estado
            self.sede_dao.actualizar()
            messagebox.showinfo("Estado actualizado", f"La sede ahora se encuentra con estado: '{nuevo_estado}'.")
            self.cargar_datos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el estado: {e}")

    def _eliminar_sede(self) -> None:
        """Eliminación física de la sede, verificando dependencias."""
        sede = self._obtener_sede_seleccionada()
        if not sede:
            return

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar permanentemente la sede '{sede.direccion}'?\n\n"
            "Nota: Si la sede posee ejemplares o préstamos asociados, la operación no podrá completarse.",
        )
        if not confirmar:
            return

        try:
            self.sede_dao.eliminar(sede)
            messagebox.showinfo("Sede eliminada", "La sede ha sido eliminada del sistema.")
            self.cargar_datos()
        except Exception as e:
            self.session.rollback()
            messagebox.showerror(
                "Operación denegada",
                f"No es posible eliminar la sede porque posee registros asociados (ejemplares o préstamos).\n"
                f"Sugerencia: Utilice la opción de 'Cambiar Estado' para darla de baja lógica.\n\nDetalle: {e}",
            )
