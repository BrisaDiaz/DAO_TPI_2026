"""
Vista de Gestión de Reservas de Material Bibliográfico.

Permite consultar el listado de reservas, filtrar por estado y socio/libro,
registrar nuevas reservas mediante ReservaService (verificando stock = 0),
cancelar reservas pendientes y visualizar las notificaciones emitidas por el
Patrón Observer.
"""
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
from sqlalchemy.orm import Session

from api.models import Reserva, Libro, Socio, Sede
from api.dao.reserva_dao import ReservaDAO
from api.dao.socio_dao import SocioDAO
from api.dao.libro_dao import LibroDAO
from api.dao.sede_dao import SedeDAO
from api.services.reserva_service import ReservaService
from api.services.notificacion_service import NotificacionService
from src.components.treeview_table import TreeviewTable


class NotificacionesObserverModal(tk.Toplevel):
    """Modal para consultar el historial de notificaciones emitidas por el Patrón Observer."""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent)
        self.title("Historial de Notificaciones — Patrón Observer")
        self.geometry("760x420")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self._centrar(parent)
        self._crear_interfaz()

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        ancho, alto = 760, 420
        x = parent.winfo_rootx() + (parent.winfo_width() - ancho) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{max(0, x)}+{max(0, y)}")

    def _crear_interfaz(self) -> None:
        padding_frame = ttk.Frame(self, padding="20 15")
        padding_frame.pack(fill="both", expand=True)
        padding_frame.grid_rowconfigure(1, weight=1)
        padding_frame.grid_columnconfigure(0, weight=1)

        header = ttk.Frame(padding_frame)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(
            header,
            text="🔔 Notificaciones de Disponibilidad (Patrón Observer)",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Registros disparados automáticamente cuando un ejemplar reservado pasa a estado 'Disponible'.",
            font=("Segoe UI", 9),
            foreground="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        columnas = [
            ("fecha", "Fecha y Hora", 130),
            ("socio", "Socio Suscripto", 150),
            ("email", "Email", 150),
            ("libro", "Obra Disponible", 180),
            ("ejemplar", "Ejemplar", 90),
            ("sede", "Sede", 120),
        ]
        self.tabla = TreeviewTable(padding_frame, columns=columnas)
        self.tabla.grid(row=1, column=0, sticky="nsew")

        btn_frame = ttk.Frame(padding_frame)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))

        ttk.Button(btn_frame, text="Cerrar", command=self.destroy).pack(side="right")
        self._cargar_historial()

    def _cargar_historial(self) -> None:
        historial = NotificacionService.obtener_historial()
        filas = [
            {
                "fecha": n.get("fecha", "-"),
                "socio": n.get("socio", "-"),
                "email": n.get("email", "-"),
                "libro": n.get("libro", "-"),
                "ejemplar": n.get("ejemplar", "-"),
                "sede": n.get("sede", "-"),
            }
            for n in reversed(historial)
        ]
        self.tabla.cargar_datos(filas)


class ReservaFormModal(tk.Toplevel):
    """Modal para Alta de una Nueva Reserva de Material Bibliográfico."""

    def __init__(
        self,
        parent: tk.Widget,
        session: Session,
        on_guardar_callback: Optional[callable] = None,
    ):
        super().__init__(parent)
        self.session = session
        self.on_guardar_callback = on_guardar_callback

        self.socio_dao = SocioDAO(session)
        self.libro_dao = LibroDAO(session)
        self.sede_dao = SedeDAO(session)
        self.reserva_service = ReservaService(session)

        self._socios = []
        self._libros = []
        self._sedes = []

        self.title("Registrar Nueva Reserva")
        self.geometry("520x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._centrar(parent)
        self._crear_formulario()

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        ancho, alto = 520, 400
        x = parent.winfo_rootx() + (parent.winfo_width() - ancho) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{max(0, x)}+{max(0, y)}")

    def _crear_formulario(self) -> None:
        padding_frame = ttk.Frame(self, padding="25 20")
        padding_frame.pack(fill="both", expand=True)

        ttk.Label(
            padding_frame,
            text="➕ Registrar Nueva Reserva",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 15))

        form_frame = ttk.Frame(padding_frame)
        form_frame.pack(fill="x", expand=True)

        # 1. Socio Solicitante
        ttk.Label(form_frame, text="Socio Habilitado (*):", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w", pady=8
        )
        self._socios = self.socio_dao.obtener_activos()
        nombres_socios = [f"[{s.numero_socio}] {s.nombre} {s.apellido}" for s in self._socios]
        self.cmb_socio = ttk.Combobox(
            form_frame, values=nombres_socios, state="readonly", width=36, font=("Segoe UI", 10)
        )
        self.cmb_socio.grid(row=0, column=1, sticky="w", pady=8)
        if nombres_socios:
            self.cmb_socio.current(0)

        # 2. Obra / Libro
        ttk.Label(form_frame, text="Obra Bibliográfica (*):", font=("Segoe UI", 9, "bold")).grid(
            row=1, column=0, sticky="w", pady=8
        )
        self._libros = self.libro_dao.obtener_todos()
        nombres_libros = [f"[ISBN: {l.isbn}] {l.titulo}" for l in self._libros]
        self.cmb_libro = ttk.Combobox(
            form_frame, values=nombres_libros, state="readonly", width=36, font=("Segoe UI", 10)
        )
        self.cmb_libro.grid(row=1, column=1, sticky="w", pady=8)
        if nombres_libros:
            self.cmb_libro.current(0)

        # 3. Sede de Retiro
        ttk.Label(form_frame, text="Sede Activa (*):", font=("Segoe UI", 9, "bold")).grid(
            row=2, column=0, sticky="w", pady=8
        )
        self._sedes = self.sede_dao.obtener_activas()
        nombres_sedes = [f"[{s.id}] {s.direccion}" for s in self._sedes]
        self.cmb_sede = ttk.Combobox(
            form_frame, values=nombres_sedes, state="readonly", width=36, font=("Segoe UI", 10)
        )
        self.cmb_sede.grid(row=2, column=1, sticky="w", pady=8)
        if nombres_sedes:
            self.cmb_sede.current(0)

        # Nota informativa sobre la regla de stock 0 (SUP-06)
        ttk.Label(
            form_frame,
            text="Nota (SUP-06): Solo es posible reservar si el stock disponible en la sede es 0.",
            font=("Segoe UI", 8),
            foreground="#64748B",
            wraplength=350,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))

        # Botones de Acción
        btn_frame = ttk.Frame(padding_frame)
        btn_frame.pack(fill="x", pady=(25, 0))

        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=(10, 0))
        ttk.Button(btn_frame, text="Registrar Reserva", command=self._guardar).pack(side="right")

    def _guardar(self) -> None:
        idx_socio = self.cmb_socio.current()
        idx_libro = self.cmb_libro.current()
        idx_sede = self.cmb_sede.current()

        if idx_socio < 0 or not self._socios:
            messagebox.showwarning("Dato requerido", "Debe seleccionar un socio válido.", parent=self)
            return
        if idx_libro < 0 or not self._libros:
            messagebox.showwarning("Dato requerido", "Debe seleccionar una obra bibliográfica.", parent=self)
            return
        if idx_sede < 0 or not self._sedes:
            messagebox.showwarning("Dato requerido", "Debe seleccionar una sede activa.", parent=self)
            return

        socio_id = self._socios[idx_socio].id
        libro_id = self._libros[idx_libro].id
        sede_id = self._sedes[idx_sede].id

        try:
            self.reserva_service.crear_reserva(
                socio_id=socio_id,
                libro_id=libro_id,
                sede_id=sede_id,
            )
            messagebox.showinfo("Reserva Exitosa", "La reserva ha sido registrada correctamente.", parent=self)
            if self.on_guardar_callback:
                self.on_guardar_callback()
            self.destroy()
        except ValueError as e:
            messagebox.showerror("No se pudo registrar la reserva", str(e), parent=self)
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error inesperado", str(e), parent=self)


class ReservasView(ttk.Frame):
    """Pestaña principal de Gestión de Reservas."""

    def __init__(self, parent: tk.Widget, session: Session, **kwargs):
        super().__init__(parent, **kwargs)
        self.session = session
        self.reserva_dao = ReservaDAO(session)
        self.reserva_service = ReservaService(session)

        self._crear_interfaz()

    def _crear_interfaz(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Encabezado
        header_frame = ttk.Frame(self, padding="15 10")
        header_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            header_frame,
            text="📌 Gestión de Reservas Bibliográficas",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            header_frame,
            text="Control de solicitudes de material sin stock, seguimiento de estados y notificaciones Observer.",
            font=("Segoe UI", 10),
            foreground="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        # 2. Barra de Filtros y Búsqueda
        filter_frame = ttk.Frame(self, padding="15 5")
        filter_frame.grid(row=1, column=0, sticky="ew")

        ttk.Label(filter_frame, text="Buscar socio o libro:", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.txt_buscar = ttk.Entry(filter_frame, width=28, font=("Segoe UI", 9))
        self.txt_buscar.pack(side="left", padx=(6, 8))
        self.txt_buscar.bind("<Return>", lambda e: self.cargar_datos())

        ttk.Button(filter_frame, text="🔍 Buscar", command=self.cargar_datos).pack(side="left", padx=(0, 6))
        ttk.Button(filter_frame, text="Limpiar", command=self._limpiar_filtro).pack(side="left", padx=(0, 15))

        # Filtro de Estado
        ttk.Label(filter_frame, text="Estado:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(5, 5))
        self.combo_filtro_estado = ttk.Combobox(
            filter_frame,
            values=["Todas", "Solo Pendientes", "Solo Canceladas", "Solo Caducadas"],
            state="readonly",
            width=18,
            font=("Segoe UI", 9),
        )
        self.combo_filtro_estado.set("Todas")
        self.combo_filtro_estado.pack(side="left")
        self.combo_filtro_estado.bind("<<ComboboxSelected>>", lambda e: self.cargar_datos())

        # 3. Contenedor Central (Tabla de Reservas)
        main_content = ttk.Frame(self, padding="15 5")
        main_content.grid(row=2, column=0, sticky="nsew")
        main_content.grid_rowconfigure(0, weight=1)
        main_content.grid_columnconfigure(0, weight=1)

        columnas = [
            ("id", "ID", 50),
            ("socio", "Socio Solicitante", 210),
            ("libro", "Título de la Obra", 260),
            ("sede", "Sede de Retiro", 180),
            ("fecha", "Fecha de Reserva", 140),
            ("estado", "Estado", 110),
        ]

        self.tabla = TreeviewTable(main_content, columns=columnas)
        self.tabla.grid(row=0, column=0, sticky="nsew")

        # 4. Barra de Acciones Inferior
        actions_frame = ttk.Frame(self, padding="15 10")
        actions_frame.grid(row=3, column=0, sticky="ew")

        ttk.Button(
            actions_frame,
            text="➕ Nueva Reserva",
            command=self._abrir_modal_alta,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="❌ Cancelar Reserva",
            command=self._cancelar_reserva,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="🔄 Procesar Caducidades (48h)",
            command=self._procesar_caducidades,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="🔔 Ver Notificaciones (Observer)",
            command=self._abrir_modal_notificaciones,
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
        """Carga y filtra las reservas registradas en el sistema."""
        filtro_texto = self.txt_buscar.get().strip().lower()
        filtro_estado = self.combo_filtro_estado.get()

        reservas = self.reserva_dao.obtener_todos()

        if filtro_estado == "Solo Pendientes":
            reservas = [r for r in reservas if r.estado == "Pendiente"]
        elif filtro_estado == "Solo Canceladas":
            reservas = [r for r in reservas if r.estado == "Cancelada"]
        elif filtro_estado == "Solo Caducadas":
            reservas = [r for r in reservas if r.estado == "Caducada"]

        if filtro_texto:
            reservas = [
                r for r in reservas
                if filtro_texto in f"{r.socio.nombre} {r.socio.apellido}".lower()
                or filtro_texto in (r.libro.titulo or "").lower()
                or filtro_texto in (r.socio.numero_socio or "").lower()
            ]

        filas = [
            {
                "id": str(r.id),
                "socio": f"{r.socio.nombre} {r.socio.apellido} ({r.socio.numero_socio})" if r.socio else f"ID {r.socio_id}",
                "libro": r.libro.titulo if r.libro else f"ID {r.libro_id}",
                "sede": r.sede.direccion if r.sede else f"ID {r.sede_id}",
                "fecha": str(r.fecha_reserva)[:19] if r.fecha_reserva else "-",
                "estado": r.estado,
            }
            for r in reservas
        ]
        self.tabla.cargar_datos(filas)

    def _abrir_modal_alta(self) -> None:
        ReservaFormModal(
            parent=self.winfo_toplevel(),
            session=self.session,
            on_guardar_callback=self.cargar_datos,
        )

    def _abrir_modal_notificaciones(self) -> None:
        NotificacionesObserverModal(parent=self.winfo_toplevel())

    def _cancelar_reserva(self) -> None:
        fila = self.tabla.get_selected_row()
        if not fila or not fila.get("id"):
            messagebox.showwarning("Selección requerida", "Seleccione una reserva de la tabla para cancelar.")
            return

        reserva_id = int(fila["id"])
        estado_actual = fila["estado"]

        if estado_actual != "Pendiente":
            messagebox.showwarning(
                "Acción no permitida",
                f"La reserva seleccionada se encuentra en estado '{estado_actual}' y no puede ser cancelada.",
            )
            return

        if not messagebox.askyesno(
            "Confirmar Cancelación",
            f"¿Está seguro de cancelar la reserva ID #{reserva_id}?",
        ):
            return

        try:
            self.reserva_service.cancelar_reserva(reserva_id)
            messagebox.showinfo("Reserva Cancelada", "La reserva fue cancelada exitosamente.")
            self.cargar_datos()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error inesperado", str(e))

    def _procesar_caducidades(self) -> None:
        """Ejecuta el control de caducidad automática a las 48h (SUP-05)."""
        try:
            cant = self.reserva_service.procesar_caducidades()
            if cant > 0:
                messagebox.showinfo(
                    "Caducidades Procesadas",
                    f"Se han marcado {cant} reserva(s) como 'Caducada' por superar el plazo de 48 horas.",
                )
            else:
                messagebox.showinfo(
                    "Sin cambios",
                    "No se encontraron reservas pendientes que superen las 48 horas de caducidad.",
                )
            self.cargar_datos()
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error", f"No se pudo procesar las caducidades: {e}")
