"""
Vista de Préstamos y Envíos Interbibliotecarios.
Permite registrar préstamos locales, envíos entre sedes, registrar devoluciones
y controlar el ciclo de vida de los remitos en tránsito.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from sqlalchemy.orm import Session

from api.dao.prestamo_dao import PrestamoDAO
from api.dao.remito_dao import RemitoDAO
from api.dao.socio_dao import SocioDAO
from api.dao.sede_dao import SedeDAO
from api.dao.ejemplar_dao import EjemplarDAO
from api.services.prestamo_service import PrestamoService
from api.services.logistica_service import LogisticaService
from src.components.treeview_table import TreeviewTable


# ─────────────────────────────────────────────────────────────────────────────
# Modal: Registrar Préstamo
# ─────────────────────────────────────────────────────────────────────────────
class PrestamoFormModal(tk.Toplevel):
    """Modal para registrar un nuevo préstamo (local o interbibliotecario)."""

    def __init__(self, parent: tk.Widget, session: Session, on_guardar_callback=None):
        super().__init__(parent)
        self.session = session
        self.on_guardar_callback = on_guardar_callback

        self.socio_dao = SocioDAO(session)
        self.sede_dao = SedeDAO(session)
        self.ejemplar_dao = EjemplarDAO(session)
        self.prestamo_service = PrestamoService(session)

        self._socios = []
        self._sedes = []
        self._ejemplares = []

        self.title("Registrar Nuevo Préstamo")
        self.geometry("540x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._centrar(parent)
        self._crear_formulario()

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        ancho, alto = 540, 400
        x = parent.winfo_rootx() + (parent.winfo_width() - ancho) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{max(0, x)}+{max(0, y)}")

    def _crear_formulario(self) -> None:
        padding_frame = ttk.Frame(self, padding="25 20")
        padding_frame.pack(fill="both", expand=True)

        ttk.Label(
            padding_frame,
            text="➕ Registrar Nuevo Préstamo",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 15))

        form_frame = ttk.Frame(padding_frame)
        form_frame.pack(fill="x", expand=True)

        # 1. Socio
        ttk.Label(form_frame, text="Socio (*):", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w", pady=6
        )
        self.cmb_socio = ttk.Combobox(form_frame, state="readonly", width=36, font=("Segoe UI", 10))
        self.cmb_socio.grid(row=0, column=1, sticky="w", pady=6)

        # 2. Sede de origen
        ttk.Label(form_frame, text="Sede de origen (*):", font=("Segoe UI", 9, "bold")).grid(
            row=1, column=0, sticky="w", pady=6
        )
        self.cmb_sede_origen = ttk.Combobox(form_frame, state="readonly", width=36, font=("Segoe UI", 10))
        self.cmb_sede_origen.grid(row=1, column=1, sticky="w", pady=6)
        self.cmb_sede_origen.bind("<<ComboboxSelected>>", self._on_sede_origen_change)

        # 3. Ejemplar
        ttk.Label(form_frame, text="Ejemplar disponible (*):", font=("Segoe UI", 9, "bold")).grid(
            row=2, column=0, sticky="w", pady=6
        )
        self.cmb_ejemplar = ttk.Combobox(form_frame, state="readonly", width=36, font=("Segoe UI", 10))
        self.cmb_ejemplar.grid(row=2, column=1, sticky="w", pady=6)

        # 4. Tipo de préstamo
        ttk.Label(form_frame, text="Tipo de préstamo:", font=("Segoe UI", 9)).grid(
            row=3, column=0, sticky="w", pady=6
        )
        tipo_frame = ttk.Frame(form_frame)
        tipo_frame.grid(row=3, column=1, sticky="w", pady=6)
        self.var_tipo = tk.StringVar(value="local")
        ttk.Radiobutton(
            tipo_frame, text="Local", variable=self.var_tipo,
            value="local", command=self._on_tipo_change,
        ).pack(side="left")
        ttk.Radiobutton(
            tipo_frame, text="Interbibliotecario", variable=self.var_tipo,
            value="inter", command=self._on_tipo_change,
        ).pack(side="left", padx=(12, 0))

        # 5. Sede de destino (solo interbibliotecario)
        ttk.Label(form_frame, text="Sede de destino:", font=("Segoe UI", 9)).grid(
            row=4, column=0, sticky="w", pady=6
        )
        self.cmb_sede_destino = ttk.Combobox(form_frame, state="disabled", width=36, font=("Segoe UI", 10))
        self.cmb_sede_destino.grid(row=4, column=1, sticky="w", pady=6)

        # 6. Días de préstamo
        ttk.Label(form_frame, text="Días de préstamo:", font=("Segoe UI", 9)).grid(
            row=5, column=0, sticky="w", pady=6
        )
        self.spn_dias = ttk.Spinbox(form_frame, from_=1, to=60, width=10, font=("Segoe UI", 10))
        self.spn_dias.set(15)
        self.spn_dias.grid(row=5, column=1, sticky="w", pady=6)

        # Botones (derecha → Guardar | Cancelar)
        btn_frame = ttk.Frame(padding_frame)
        btn_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=(10, 0))
        ttk.Button(btn_frame, text="Registrar Préstamo", command=self._guardar).pack(side="right")

        self._cargar_combos()

    # ── Lógica de combos ─────────────────────────────────────────────────────
    def _cargar_combos(self) -> None:
        self._socios = self.socio_dao.obtener_activos()
        self.cmb_socio["values"] = [
            f"[{s.numero_socio}] {s.nombre} {s.apellido}" for s in self._socios
        ]
        if self._socios:
            self.cmb_socio.current(0)

        self._sedes = self.sede_dao.obtener_activas()
        valores_sedes = [f"[{s.id}] {s.direccion}" for s in self._sedes]
        self.cmb_sede_origen["values"] = valores_sedes
        self.cmb_sede_destino["values"] = valores_sedes
        if self._sedes:
            self.cmb_sede_origen.current(0)
            self._cargar_ejemplares_de_sede(self._sedes[0].id)

    def _on_sede_origen_change(self, _event=None) -> None:
        idx = self.cmb_sede_origen.current()
        if idx >= 0:
            self._cargar_ejemplares_de_sede(self._sedes[idx].id)

    def _cargar_ejemplares_de_sede(self, sede_id: int) -> None:
        self._ejemplares = self.ejemplar_dao.obtener_disponibles_por_sede(sede_id)
        self.cmb_ejemplar["values"] = [
            f"[{e.id}] {e.codigo_inventario} — {e.libro.titulo if e.libro else '?'}"
            for e in self._ejemplares
        ]
        if self._ejemplares:
            self.cmb_ejemplar.current(0)
        else:
            self.cmb_ejemplar.set("(Sin ejemplares disponibles en esta sede)")

    def _on_tipo_change(self) -> None:
        if self.var_tipo.get() == "inter":
            self.cmb_sede_destino.configure(state="readonly")
        else:
            self.cmb_sede_destino.configure(state="disabled")
            self.cmb_sede_destino.set("")

    # ── Guardar ──────────────────────────────────────────────────────────────
    def _guardar(self) -> None:
        idx_socio = self.cmb_socio.current()
        idx_sede_origen = self.cmb_sede_origen.current()
        idx_ejemplar = self.cmb_ejemplar.current()

        if idx_socio < 0:
            messagebox.showwarning("Dato requerido", "Seleccione un socio.", parent=self)
            return
        if idx_sede_origen < 0:
            messagebox.showwarning("Dato requerido", "Seleccione la sede de origen.", parent=self)
            return
        if idx_ejemplar < 0 or not self._ejemplares:
            messagebox.showwarning(
                "Sin ejemplares disponibles",
                "La sede seleccionada no tiene ejemplares disponibles para prestar.",
                parent=self,
            )
            return

        socio_id = self._socios[idx_socio].id
        sede_origen_id = self._sedes[idx_sede_origen].id
        ejemplar_id = self._ejemplares[idx_ejemplar].id

        sede_destino_id = None
        if self.var_tipo.get() == "inter":
            idx_dest = self.cmb_sede_destino.current()
            if idx_dest < 0:
                messagebox.showwarning("Dato requerido", "Seleccione la sede de destino.", parent=self)
                return
            sede_destino_id = self._sedes[idx_dest].id
            if sede_destino_id == sede_origen_id:
                messagebox.showwarning(
                    "Datos inválidos",
                    "La sede de destino debe ser diferente a la sede de origen.",
                    parent=self,
                )
                return

        try:
            dias = int(self.spn_dias.get())
        except ValueError:
            dias = 15

        try:
            self.prestamo_service.registrar_prestamo(
                socio_id=socio_id,
                ejemplar_id=ejemplar_id,
                sede_origen_id=sede_origen_id,
                sede_destino_id=sede_destino_id,
                dias_prestamo=dias,
            )
            messagebox.showinfo("Préstamo registrado", "El préstamo fue registrado exitosamente.", parent=self)
            if self.on_guardar_callback:
                self.on_guardar_callback()
            self.destroy()
        except ValueError as e:
            messagebox.showerror("No se pudo registrar", str(e), parent=self)
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error inesperado", str(e), parent=self)


# ─────────────────────────────────────────────────────────────────────────────
# Modal: Registrar Devolución
# ─────────────────────────────────────────────────────────────────────────────
class DevolucionModal(tk.Toplevel):
    """Modal para registrar la devolución de un préstamo activo."""

    ESTADOS_FISICOS = ["Disponible", "Dañado", "Extraviado"]

    def __init__(self, parent: tk.Widget, session: Session, prestamo, on_guardar_callback=None):
        super().__init__(parent)
        self.session = session
        self.prestamo = prestamo
        self.on_guardar_callback = on_guardar_callback
        self.prestamo_service = PrestamoService(session)

        self.title(f"Registrar Devolución — Préstamo #{prestamo.id}")
        self.geometry("480x340")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._centrar(parent)
        self._crear_formulario()

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        ancho, alto = 480, 340
        x = parent.winfo_rootx() + (parent.winfo_width() - ancho) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{max(0, x)}+{max(0, y)}")

    def _crear_formulario(self) -> None:
        padding_frame = ttk.Frame(self, padding="25 20")
        padding_frame.pack(fill="both", expand=True)

        ttk.Label(
            padding_frame,
            text="↩ Registrar Devolución",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 15))

        form_frame = ttk.Frame(padding_frame)
        form_frame.pack(fill="x", expand=True)

        p = self.prestamo
        socio_nombre = f"{p.socio.nombre} {p.socio.apellido}" if p.socio else f"ID {p.socio_id}"
        ejemplar_cod = p.ejemplar.codigo_inventario if p.ejemplar else f"ID {p.ejemplar_id}"
        libro_titulo = (p.ejemplar.libro.titulo if p.ejemplar and p.ejemplar.libro else "—")

        # Información del préstamo (solo lectura)
        info = [
            ("Socio:", socio_nombre),
            ("Ejemplar:", f"{ejemplar_cod} — {libro_titulo}"),
            ("Fecha de vencimiento:", str(p.fecha_devolucion_estimada)),
        ]
        for i, (label, valor) in enumerate(info):
            ttk.Label(form_frame, text=label, font=("Segoe UI", 9, "bold")).grid(
                row=i, column=0, sticky="w", pady=5
            )
            ttk.Label(form_frame, text=valor, font=("Segoe UI", 9)).grid(
                row=i, column=1, sticky="w", pady=5, padx=(8, 0)
            )

        # Aviso de retraso
        hoy = date.today()
        row_siguiente = len(info)
        if hoy > p.fecha_devolucion_estimada:
            dias_retraso = (hoy - p.fecha_devolucion_estimada).days
            ttk.Label(
                form_frame,
                text=f"⚠  Devolución con {dias_retraso} día(s) de retraso — se generará una multa.",
                foreground="#B91C1C",
                font=("Segoe UI", 9),
                wraplength=400,
            ).grid(row=row_siguiente, column=0, columnspan=2, sticky="w", pady=(6, 0))
            row_siguiente += 1

        # Estado físico del ejemplar al devolver
        ttk.Label(
            form_frame, text="Estado del ejemplar:", font=("Segoe UI", 9, "bold")
        ).grid(row=row_siguiente, column=0, sticky="w", pady=(14, 6))
        self.cmb_estado = ttk.Combobox(
            form_frame, values=self.ESTADOS_FISICOS, state="readonly",
            width=20, font=("Segoe UI", 10),
        )
        self.cmb_estado.current(0)
        self.cmb_estado.grid(row=row_siguiente, column=1, sticky="w", pady=(14, 6), padx=(8, 0))

        # Botones
        btn_frame = ttk.Frame(padding_frame)
        btn_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=(10, 0))
        ttk.Button(btn_frame, text="Confirmar Devolución", command=self._confirmar).pack(side="right")

    def _confirmar(self) -> None:
        estado_fisico = self.cmb_estado.get()
        if not messagebox.askyesno(
            "Confirmar devolución",
            f"¿Confirmar la devolución del préstamo #{self.prestamo.id}?\n"
            f"Estado del ejemplar al devolver: {estado_fisico}.",
            parent=self,
        ):
            return
        try:
            self.prestamo_service.registrar_devolucion(
                prestamo_id=self.prestamo.id,
                estado_fisico_ejemplar=estado_fisico,
            )
            messagebox.showinfo("Devolución registrada", "La devolución fue registrada correctamente.", parent=self)
            if self.on_guardar_callback:
                self.on_guardar_callback()
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error inesperado", str(e), parent=self)


# ─────────────────────────────────────────────────────────────────────────────
# Vista principal: Préstamos + Remitos (Notebook interno)
# ─────────────────────────────────────────────────────────────────────────────
class PrestamosView(ttk.Frame):
    """Pestaña de Préstamos y Logística de Remitos."""

    def __init__(self, parent: tk.Widget, session: Session, **kwargs):
        super().__init__(parent, **kwargs)
        self.session = session
        self.prestamo_dao = PrestamoDAO(session)
        self.remito_dao = RemitoDAO(session)
        self.logistica_service = LogisticaService(session)

        self._crear_interfaz()

    # ── Construcción de la interfaz ──────────────────────────────────────────
    def _crear_interfaz(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Encabezado
        header_frame = ttk.Frame(self, padding="15 10")
        header_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            header_frame,
            text="🔄 Gestión de Préstamos y Envíos",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            header_frame,
            text="Registro de préstamos locales e interbibliotecarios, devoluciones y seguimiento de remitos.",
            font=("Segoe UI", 10),
            foreground="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        # 2. Barra de filtros
        filter_frame = ttk.Frame(self, padding="15 5")
        filter_frame.grid(row=1, column=0, sticky="ew")

        ttk.Label(filter_frame, text="Mostrar:", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.cmb_filtro = ttk.Combobox(
            filter_frame,
            values=["Todos", "Solo activos", "Solo devueltos", "Solo interbibliotecarios"],
            state="readonly",
            width=24,
            font=("Segoe UI", 9),
        )
        self.cmb_filtro.current(0)
        self.cmb_filtro.pack(side="left", padx=(6, 0))
        self.cmb_filtro.bind("<<ComboboxSelected>>", lambda _e: self.cargar_datos())

        # 3. Notebook interno: Préstamos / Remitos
        nb = ttk.Notebook(self)
        nb.grid(row=2, column=0, sticky="nsew", padx=15, pady=(5, 15))

        self._tab_prestamos = ttk.Frame(nb, padding=10)
        self._tab_remitos = ttk.Frame(nb, padding=10)
        nb.add(self._tab_prestamos, text="📋 Préstamos")
        nb.add(self._tab_remitos, text="📦 Remitos en tránsito")

        self._construir_tab_prestamos(self._tab_prestamos)
        self._construir_tab_remitos(self._tab_remitos)

        self.cargar_datos()

    def _construir_tab_prestamos(self, parent: ttk.Frame) -> None:
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        cols_prest = [
            ("id", "ID", 50),
            ("socio", "Socio", 190),
            ("ejemplar", "Cód. Ejemplar", 120),
            ("libro", "Libro", 180),
            ("tipo", "Tipo", 120),
            ("origen", "Sede origen", 130),
            ("destino", "Sede destino", 130),
            ("fecha_prestamo", "F. Préstamo", 100),
            ("vencimiento", "Vencimiento", 100),
            ("estado", "Estado", 90),
        ]
        self.tabla_prestamos = TreeviewTable(parent, columns=cols_prest)
        self.tabla_prestamos.grid(row=0, column=0, sticky="nsew")

        # Botones específicos de Préstamos (ubicados en su propia pestaña)
        actions_prestamos = ttk.Frame(parent, padding="0 10 0 0")
        actions_prestamos.grid(row=1, column=0, sticky="ew")

        ttk.Button(
            actions_prestamos,
            text="➕ Nuevo Préstamo",
            command=self._abrir_form_prestamo,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_prestamos,
            text="↩ Registrar Devolución",
            command=self._registrar_devolucion,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_prestamos,
            text="🔄 Actualizar",
            command=self.cargar_datos,
        ).pack(side="right")

    def _construir_tab_remitos(self, parent: ttk.Frame) -> None:
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        cols_rem = [
            ("id", "ID", 50),
            ("codigo", "Código remito", 160),
            ("prestamo_id", "ID Préstamo", 90),
            ("libro", "Libro", 200),
            ("origen", "Sede origen", 150),
            ("destino", "Sede destino", 150),
            ("estado", "Estado", 130),
        ]
        self.tabla_remitos = TreeviewTable(parent, columns=cols_rem)
        self.tabla_remitos.grid(row=0, column=0, sticky="nsew")

        ttk.Label(
            parent,
            text="Estados: Empaquetado → Despachado → Recibido  |  La incidencia solo se puede reportar desde 'Despachado'.",
            font=("Segoe UI", 8),
            foreground="#64748B",
        ).grid(row=1, column=0, sticky="w", padx=0, pady=(4, 2))

        # Botones específicos de Remitos (ubicados en su propia pestaña)
        actions_remitos = ttk.Frame(parent, padding="0 6 0 0")
        actions_remitos.grid(row=2, column=0, sticky="ew")

        ttk.Button(
            actions_remitos,
            text="▶ Avanzar estado de remito",
            command=self._avanzar_remito,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_remitos,
            text="⚠ Reportar incidencia",
            command=self._reportar_incidencia,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_remitos,
            text="🔄 Actualizar",
            command=self.cargar_datos,
        ).pack(side="right")

    # ── Carga de datos ───────────────────────────────────────────────────────
    def cargar_datos(self) -> None:
        filtro = self.cmb_filtro.get()
        todos = self.prestamo_dao.obtener_todos()

        if filtro == "Solo activos":
            prestamos = [p for p in todos if p.estado == "Activo"]
        elif filtro == "Solo devueltos":
            prestamos = [p for p in todos if p.estado == "Devuelto"]
        elif filtro == "Solo interbibliotecarios":
            prestamos = [
                p for p in todos
                if p.sede_destino_id and p.sede_destino_id != p.sede_origen_id
            ]
        else:
            prestamos = todos

        filas = []
        for p in prestamos:
            socio_str = f"{p.socio.nombre} {p.socio.apellido}" if p.socio else f"ID {p.socio_id}"
            ej = p.ejemplar
            ejemplar_str = ej.codigo_inventario if ej else f"ID {p.ejemplar_id}"
            libro_str = (ej.libro.titulo if ej and ej.libro else "—")
            es_inter = p.sede_destino_id and p.sede_destino_id != p.sede_origen_id
            filas.append({
                "id": str(p.id),
                "socio": socio_str,
                "ejemplar": ejemplar_str,
                "libro": libro_str,
                "tipo": "Interbibliotecario" if es_inter else "Local",
                "origen": p.sede_origen.direccion if p.sede_origen else "—",
                "destino": p.sede_destino.direccion if p.sede_destino else "Local",
                "fecha_prestamo": str(p.fecha_prestamo),
                "vencimiento": str(p.fecha_devolucion_estimada),
                "estado": p.estado,
            })

        self.tabla_prestamos.cargar_datos(filas)
        self.cargar_remitos()

    def cargar_remitos(self) -> None:
        remitos = self.remito_dao.obtener_todos()
        filas = []
        for r in remitos:
            p = r.prestamo
            libro_str = origen_str = destino_str = "—"
            if p:
                if p.ejemplar and p.ejemplar.libro:
                    libro_str = p.ejemplar.libro.titulo
                if p.sede_origen:
                    origen_str = p.sede_origen.direccion
                if p.sede_destino:
                    destino_str = p.sede_destino.direccion
            filas.append({
                "id": str(r.id),
                "codigo": r.codigo_remito,
                "prestamo_id": str(r.prestamo_id),
                "libro": libro_str,
                "origen": origen_str,
                "destino": destino_str,
                "estado": r.estado,
            })
        self.tabla_remitos.cargar_datos(filas)

    # ── Acciones: Préstamos ──────────────────────────────────────────────────
    def _abrir_form_prestamo(self) -> None:
        PrestamoFormModal(
            parent=self.winfo_toplevel(),
            session=self.session,
            on_guardar_callback=self.cargar_datos,
        )

    def _registrar_devolucion(self) -> None:
        fila = self.tabla_prestamos.get_selected_row()
        if not fila:
            messagebox.showinfo(
                "Selección requerida",
                "Seleccione un préstamo activo de la lista para registrar la devolución.",
            )
            return

        prestamo_id = int(fila["id"])
        prestamo = self.prestamo_dao.obtener_por_id(prestamo_id)
        if not prestamo:
            messagebox.showerror("Error", "No se encontró el préstamo seleccionado.")
            return
        if prestamo.estado != "Activo":
            messagebox.showwarning(
                "Préstamo no activo",
                f"El préstamo #{prestamo_id} ya fue devuelto o no se encuentra activo.",
            )
            return

        DevolucionModal(
            parent=self.winfo_toplevel(),
            session=self.session,
            prestamo=prestamo,
            on_guardar_callback=self.cargar_datos,
        )

    # ── Acciones: Remitos ────────────────────────────────────────────────────
    def _avanzar_remito(self) -> None:
        fila = self.tabla_remitos.get_selected_row()
        if not fila:
            messagebox.showinfo(
                "Selección requerida",
                "Seleccione un remito de la lista para avanzar su estado.",
            )
            return

        remito_id = int(fila["id"])
        estado_actual = fila["estado"]

        if estado_actual == "Recibido":
            messagebox.showinfo(
                "Sin transición posible",
                "Este remito ya se encuentra en su estado final (Recibido).",
            )
            return

        siguiente = {
            "Empaquetado": "Despachado",
            "Despachado": "Recibido",
            "Con incidencias": "Recibido",
        }.get(estado_actual, "—")

        if not messagebox.askyesno(
            "Confirmar avance de estado",
            f"¿Avanzar el remito «{fila['codigo']}»\nde '{estado_actual}' a '{siguiente}'?",
        ):
            return

        try:
            self.logistica_service.avanzar_estado(remito_id)
            messagebox.showinfo("Estado actualizado", f"El remito pasó al estado '{siguiente}'.")
            self.cargar_datos()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error inesperado", str(e))

    def _reportar_incidencia(self) -> None:
        fila = self.tabla_remitos.get_selected_row()
        if not fila:
            messagebox.showinfo(
                "Selección requerida",
                "Seleccione un remito de la lista para reportar una incidencia.",
            )
            return

        remito_id = int(fila["id"])
        estado_actual = fila["estado"]

        if estado_actual != "Despachado":
            messagebox.showwarning(
                "Acción no disponible",
                "Solo se puede reportar una incidencia en remitos con estado 'Despachado'.",
            )
            return

        if not messagebox.askyesno(
            "Confirmar incidencia",
            f"¿Reportar una incidencia en el remito «{fila['codigo']}»?\n"
            "El estado pasará a 'Con incidencias'.",
        ):
            return

        try:
            self.logistica_service.reportar_incidencia(remito_id)
            messagebox.showinfo("Incidencia registrada", "Se registró la incidencia en el remito.")
            self.cargar_datos()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error inesperado", str(e))