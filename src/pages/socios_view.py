"""
Vista de Gestión de Socios y Regularización de Multas (ABMC Completo).

Permite consultar el padrón de socios, registrar nuevos miembros, modificar
información de contacto, gestionar inhabilitaciones y administrar la cobranza
o condonación de multas pendientes mediante MultaService (Patrón Strategy).
"""
from datetime import date
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
from sqlalchemy.orm import Session

from api.models import Socio, Multa
from api.dao.socio_dao import SocioDAO
from api.dao.multa_dao import MultaDAO
from api.services.multa_service import MultaService
from src.components.treeview_table import TreeviewTable


class SocioFormModal(tk.Toplevel):
    """Modal para Alta y Modificación de Socios."""

    def __init__(
        self,
        parent: tk.Widget,
        socio_dao: SocioDAO,
        socio: Optional[Socio] = None,
        on_guardar_callback: Optional[callable] = None,
    ):
        super().__init__(parent)
        self.socio_dao = socio_dao
        self.socio = socio
        self.on_guardar_callback = on_guardar_callback

        es_edicion = socio is not None
        self.title("Modificar Socio" if es_edicion else "Registrar Nuevo Socio")
        self.geometry("520x460")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._centrar(parent)
        self._crear_formulario(es_edicion)

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 520) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 460) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _crear_formulario(self, es_edicion: bool) -> None:
        padding_frame = ttk.Frame(self, padding="25 20")
        padding_frame.pack(fill="both", expand=True)

        titulo_modal = "✏️ Modificar Socio" if es_edicion else "➕ Registrar Nuevo Socio"
        ttk.Label(
            padding_frame,
            text=titulo_modal,
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 15))

        form_frame = ttk.Frame(padding_frame)
        form_frame.pack(fill="x", expand=True)

        # 1. Nro. Socio
        ttk.Label(form_frame, text="Nro. de Socio (*):", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w", pady=6
        )
        self.txt_nro_socio = ttk.Entry(form_frame, width=36, font=("Segoe UI", 10))
        self.txt_nro_socio.grid(row=0, column=1, sticky="w", pady=6)
        if self.socio:
            self.txt_nro_socio.insert(0, self.socio.numero_socio or "")
        else:
            # Sugerir un número correlativo aproximado
            total = len(self.socio_dao.obtener_todos()) + 1
            self.txt_nro_socio.insert(0, f"SOC-{total:03d}")

        # 2. Documento / DNI
        ttk.Label(form_frame, text="Documento / DNI (*):", font=("Segoe UI", 9, "bold")).grid(
            row=1, column=0, sticky="w", pady=6
        )
        self.txt_documento = ttk.Entry(form_frame, width=36, font=("Segoe UI", 10))
        self.txt_documento.grid(row=1, column=1, sticky="w", pady=6)
        if self.socio:
            doc_actual = getattr(self.socio, "documento", getattr(self.socio, "dni", ""))
            self.txt_documento.insert(0, str(doc_actual or ""))

        # 3. Nombre
        ttk.Label(form_frame, text="Nombre (*):", font=("Segoe UI", 9, "bold")).grid(
            row=2, column=0, sticky="w", pady=6
        )
        self.txt_nombre = ttk.Entry(form_frame, width=36, font=("Segoe UI", 10))
        self.txt_nombre.grid(row=2, column=1, sticky="w", pady=6)
        if self.socio:
            self.txt_nombre.insert(0, self.socio.nombre or "")

        # 4. Apellido
        ttk.Label(form_frame, text="Apellido (*):", font=("Segoe UI", 9, "bold")).grid(
            row=3, column=0, sticky="w", pady=6
        )
        self.txt_apellido = ttk.Entry(form_frame, width=36, font=("Segoe UI", 10))
        self.txt_apellido.grid(row=3, column=1, sticky="w", pady=6)
        if self.socio:
            self.txt_apellido.insert(0, self.socio.apellido or "")

        # 5. Email
        ttk.Label(form_frame, text="Email:", font=("Segoe UI", 9)).grid(
            row=4, column=0, sticky="w", pady=6
        )
        self.txt_email = ttk.Entry(form_frame, width=36, font=("Segoe UI", 10))
        self.txt_email.grid(row=4, column=1, sticky="w", pady=6)
        if self.socio:
            self.txt_email.insert(0, self.socio.email or "")

        # 6. Teléfono
        ttk.Label(form_frame, text="Teléfono:", font=("Segoe UI", 9)).grid(
            row=5, column=0, sticky="w", pady=6
        )
        self.txt_telefono = ttk.Entry(form_frame, width=36, font=("Segoe UI", 10))
        self.txt_telefono.grid(row=5, column=1, sticky="w", pady=6)
        if self.socio:
            self.txt_telefono.insert(0, self.socio.telefono or "")

        # 7. Estado
        ttk.Label(form_frame, text="Estado de Cuenta:", font=("Segoe UI", 9)).grid(
            row=6, column=0, sticky="w", pady=6
        )
        self.combo_estado = ttk.Combobox(
            form_frame,
            values=["Habilitado", "Inhabilitado"],
            state="readonly",
            width=34,
            font=("Segoe UI", 10),
        )
        estado_inicial = "Habilitado" if (not self.socio or self.socio.activo) else "Inhabilitado"
        self.combo_estado.set(estado_inicial)
        self.combo_estado.grid(row=6, column=1, sticky="w", pady=6)

        # Botones
        btn_frame = ttk.Frame(padding_frame)
        btn_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=(10, 0))
        ttk.Button(btn_frame, text="Guardar Socio", command=self._guardar).pack(side="right")

        self.txt_nombre.focus()

    def _guardar(self) -> None:
        nro_socio = self.txt_nro_socio.get().strip()
        documento = self.txt_documento.get().strip()
        nombre = self.txt_nombre.get().strip()
        apellido = self.txt_apellido.get().strip()
        email = self.txt_email.get().strip()
        telefono = self.txt_telefono.get().strip()
        activo = 1 if self.combo_estado.get() == "Habilitado" else 0

        # Validaciones obligatorias
        if not nro_socio or not documento or not nombre or not apellido:
            messagebox.showwarning(
                "Datos obligatorios",
                "Por favor complete los campos obligatorios: Nro. de Socio, Documento, Nombre y Apellido.",
                parent=self,
            )
            return

        # Validar no duplicidad de Nro. de socio
        socio_por_nro = self.socio_dao.obtener_por_numero_socio(nro_socio)
        if socio_por_nro and (not self.socio or socio_por_nro.id != self.socio.id):
            messagebox.showerror(
                "Nro. de Socio duplicado",
                f"Ya existe un socio registrado con el número '{nro_socio}'.",
                parent=self,
            )
            self.txt_nro_socio.focus()
            return

        # Validar no duplicidad de Documento
        socio_por_doc = self.socio_dao.obtener_por_documento(documento)
        if socio_por_doc and (not self.socio or socio_por_doc.id != self.socio.id):
            messagebox.showerror(
                "Documento duplicado",
                f"Ya existe un socio registrado con el documento '{documento}'.",
                parent=self,
            )
            self.txt_documento.focus()
            return

        try:
            if self.socio:
                self.socio.numero_socio = nro_socio
                if hasattr(self.socio, "documento"):
                    self.socio.documento = documento
                elif hasattr(self.socio, "dni"):
                    self.socio.dni = documento
                self.socio.nombre = nombre
                self.socio.apellido = apellido
                self.socio.email = email
                self.socio.telefono = telefono
                self.socio.activo = activo
                self.socio_dao.actualizar()
                messagebox.showinfo("Éxito", "Datos del socio actualizados correctamente.", parent=self)
            else:
                nuevo = Socio(
                    numero_socio=nro_socio,
                    documento=documento,
                    nombre=nombre,
                    apellido=apellido,
                    email=email,
                    telefono=telefono,
                    activo=activo,
                )
                self.socio_dao.crear(nuevo)
                messagebox.showinfo("Éxito", "Socio registrado exitosamente en el sistema.", parent=self)

            if self.on_guardar_callback:
                self.on_guardar_callback()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error al guardar", f"No se pudo guardar el socio: {e}", parent=self)


class MultasModal(tk.Toplevel):
    """Ventana emergente para la consulta, cobro y condonación de sanciones de un socio."""

    def __init__(
        self,
        parent: tk.Widget,
        session: Session,
        socio: Socio,
        on_actualizar_callback: Optional[callable] = None,
    ):
        super().__init__(parent)
        self.session = session
        self.socio = socio
        self.on_actualizar_callback = on_actualizar_callback

        self.multa_dao = MultaDAO(session)
        self.multa_service = MultaService(session)

        self.title(f"Gestión de Multas — {socio.nombre} {socio.apellido} ({socio.numero_socio})")
        self.geometry("720x480")
        self.minsize(620, 400)
        self.transient(parent)
        self.grab_set()

        self._centrar(parent)
        self._crear_interfaz()

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        ancho, alto = 720, 480
        x = parent.winfo_rootx() + (parent.winfo_width() - ancho) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{max(0, x)}+{max(0, y)}")

    def _crear_interfaz(self) -> None:
        main_frame = ttk.Frame(self, padding="20 15")
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # 1. Encabezado y Resumen (Fila 0)
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(
            info_frame,
            text=f"Historial de Sanciones: {self.socio.nombre} {self.socio.apellido} ({self.socio.numero_socio})",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        self.lbl_resumen = ttk.Label(
            info_frame,
            text="",
            font=("Segoe UI", 10),
        )
        self.lbl_resumen.pack(anchor="w", pady=(3, 0))

        # 2. Tabla de multas (Fila 1 - expandible)
        table_container = ttk.Frame(main_frame)
        table_container.grid(row=1, column=0, sticky="nsew", pady=5)
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        columnas = [
            ("id", "ID Multa", 80),
            ("prestamo_id", "ID Préstamo", 100),
            ("monto", "Monto", 110),
            ("estado", "Estado", 120),
            ("fecha", "Fecha Emisión", 140),
        ]

        self.tabla = TreeviewTable(table_container, columns=columnas)
        self.tabla.grid(row=0, column=0, sticky="nsew")

        # 3. Barra de Botones de Acción (Fila 2 - siempre fija al pie)
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(15, 0))

        ttk.Button(
            btn_frame,
            text="💵 Registrar Cobro",
            command=self._cobrar_multa,
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            btn_frame,
            text="🏷️ Condonar Multa",
            command=self._condonar_multa,
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            btn_frame,
            text="Cerrar",
            command=self.destroy,
        ).pack(side="right")

        self.cargar_multas()

    def cargar_multas(self) -> None:
        """Carga el historial de multas del socio y calcula la deuda pendiente."""
        todas_multas = self.session.query(Multa).filter(Multa.socio_id == self.socio.id).all()
        pendientes = [m for m in todas_multas if m.estado == "Pendiente"]
        total_deuda = sum(float(m.monto or 0) for m in pendientes)

        # Actualizar texto de resumen
        estado_socio = "Habilitado" if self.socio.activo else "Inhabilitado por Deuda"
        color_deuda = "#DC2626" if total_deuda > 0 else "#16A34A"
        self.lbl_resumen.configure(
            text=f"Estado de cuenta: {estado_socio}  |  Deuda total pendiente: ${total_deuda:,.2f}"
        )

        filas = [
            {
                "id": str(m.id),
                "prestamo_id": str(m.prestamo_id) if m.prestamo_id else "-",
                "monto": f"${float(m.monto):,.2f}",
                "estado": m.estado,
                "fecha": str(m.fecha_emision)[:10] if hasattr(m, "fecha_emision") and m.fecha_emision else "-",
            }
            for m in todas_multas
        ]
        self.tabla.cargar_datos(filas)

    def _obtener_multa_seleccionada(self) -> Optional[Multa]:
        fila = self.tabla.get_selected_row()
        if not fila or not fila.get("id"):
            messagebox.showwarning("Selección requerida", "Seleccione una multa de la tabla.", parent=self)
            return None
        try:
            multa_id = int(fila["id"])
            multa = self.multa_dao.obtener_por_id(multa_id)
            if not multa:
                messagebox.showerror("Error", "No se encontró el registro de la multa.", parent=self)
                return None
            return multa
        except (ValueError, TypeError):
            return None

    def _cobrar_multa(self) -> None:
        multa = self._obtener_multa_seleccionada()
        if not multa:
            return

        if multa.estado != "Pendiente":
            messagebox.showinfo("Información", f"La multa seleccionada ya se encuentra '{multa.estado}'.", parent=self)
            return

        confirmar = messagebox.askyesno(
            "Confirmar Pago",
            f"¿Desea registrar el cobro de la multa ID {multa.id} por un monto de ${float(multa.monto):,.2f}?",
            parent=self,
        )
        if not confirmar:
            return

        try:
            self.multa_service.registrar_pago(multa.id)
            if self.on_actualizar_callback:
                self.on_actualizar_callback()

            # Verificar si liquidó todas sus deudas
            pendientes = self.multa_dao.obtener_pendientes_por_socio(self.socio.id)
            if not pendientes:
                messagebox.showinfo(
                    "Cobro Registrado y Regularizado",
                    f"El cobro fue asentado correctamente.\nEl socio {self.socio.nombre} {self.socio.apellido} no registra más deudas pendientes y su cuenta ha sido reactivada.",
                    parent=self,
                )
                self.destroy()
                return

            messagebox.showinfo(
                "Cobro Registrado",
                "El pago fue asentado correctamente.",
                parent=self,
            )
            self.cargar_multas()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el pago: {e}", parent=self)

    def _condonar_multa(self) -> None:
        multa = self._obtener_multa_seleccionada()
        if not multa:
            return

        if multa.estado != "Pendiente":
            messagebox.showinfo("Información", f"La multa seleccionada ya se encuentra '{multa.estado}'.", parent=self)
            return

        confirmar = messagebox.askyesno(
            "Confirmar Condonación",
            f"¿Está seguro de condonar la multa ID {multa.id} por un monto de ${float(multa.monto):,.2f}?",
            parent=self,
        )
        if not confirmar:
            return

        try:
            self.multa_service.condonar_multa(multa.id)
            if self.on_actualizar_callback:
                self.on_actualizar_callback()

            # Verificar si liquidó todas sus deudas
            pendientes = self.multa_dao.obtener_pendientes_por_socio(self.socio.id)
            if not pendientes:
                messagebox.showinfo(
                    "Multa Condonada y Regularizada",
                    f"La multa ha sido condonada exitosamente.\nEl socio {self.socio.nombre} {self.socio.apellido} no registra más deudas y su cuenta ha sido reactivada.",
                    parent=self,
                )
                self.destroy()
                return

            messagebox.showinfo("Multa Condonada", "La multa ha sido condonada exitosamente.", parent=self)
            self.cargar_multas()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo condonar la multa: {e}", parent=self)


class SociosView(ttk.Frame):
    """Pestaña de Gestión de Socios (Consulta, Búsqueda, Filtros, Alta, Edición y Cobro de Multas)."""

    def __init__(self, parent: tk.Widget, session: Session, **kwargs):
        super().__init__(parent, **kwargs)
        self.session = session
        self.socio_dao = SocioDAO(session)
        self.multa_dao = MultaDAO(session)

        self._crear_interfaz()

    def _crear_interfaz(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Encabezado
        header_frame = ttk.Frame(self, padding="15 10")
        header_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            header_frame,
            text="👥 Gestión de Socios",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            header_frame,
            text="Consulta y administración del padrón de socios, verificación de estados de cuenta y regularización de multas.",
            font=("Segoe UI", 10),
            foreground="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        # 2. Barra de Búsqueda y Filtros
        filter_frame = ttk.Frame(self, padding="15 5")
        filter_frame.grid(row=1, column=0, sticky="ew")

        ttk.Label(filter_frame, text="Buscar socio:", font=("Segoe UI", 9, "bold")).pack(side="left")
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

        # Filtro de Estado
        ttk.Label(filter_frame, text="Estado:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(5, 5))
        self.combo_filtro_estado = ttk.Combobox(
            filter_frame,
            values=["Todos", "Solo Habilitados", "Solo Inhabilitados"],
            state="readonly",
            width=17,
            font=("Segoe UI", 9),
        )
        self.combo_filtro_estado.set("Todos")
        self.combo_filtro_estado.pack(side="left")
        self.combo_filtro_estado.bind("<<ComboboxSelected>>", lambda e: self.cargar_datos())

        # 3. Contenedor central (Tabla de socios)
        main_content = ttk.Frame(self, padding="15 5")
        main_content.grid(row=2, column=0, sticky="nsew")
        main_content.grid_rowconfigure(0, weight=1)
        main_content.grid_columnconfigure(0, weight=1)

        columnas = [
            ("id", "ID", 50),
            ("numero_socio", "Nro. Socio", 90),
            ("nombre_completo", "Nombre y Apellido", 220),
            ("documento", "DNI / Doc.", 100),
            ("telefono", "Teléfono", 110),
            ("email", "Email", 210),
            ("estado", "Estado Cuenta", 110),
            ("deuda", "Deuda Pendiente", 120),
        ]

        self.tabla = TreeviewTable(
            main_content,
            columns=columnas,
            on_double_click=lambda row: self._abrir_modal_modificar(),
        )
        self.tabla.grid(row=0, column=0, sticky="nsew")

        # 4. Barra de Acciones inferior (Botones ABMC y Multas)
        actions_frame = ttk.Frame(self, padding="15 10")
        actions_frame.grid(row=3, column=0, sticky="ew")

        ttk.Button(
            actions_frame,
            text="➕ Nuevo Socio",
            command=self._abrir_modal_alta,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="✏️ Modificar",
            command=self._abrir_modal_modificar,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="💰 Gestionar Multas",
            command=self._abrir_modal_multas,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="🔄 Cambiar Estado (Habilitar / Inhabilitar)",
            command=self._cambiar_estado_socio,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="🗑️ Eliminar",
            command=self._eliminar_socio,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="🔄 Actualizar",
            command=self.cargar_datos,
        ).pack(side="right")

        self.cargar_datos()

    def _limpiar_filtro(self) -> None:
        self.txt_buscar.delete(0, tk.END)
        self.combo_filtro_estado.set("Todos")
        self.cargar_datos()

    def cargar_datos(self) -> None:
        """Carga y filtra los socios con su estado de habilitación y balance de deudas."""
        filtro_texto = self.txt_buscar.get().strip().lower()
        filtro_estado = self.combo_filtro_estado.get()

        if filtro_estado == "Solo Habilitados":
            socios = self.socio_dao.obtener_activos()
        elif filtro_estado == "Solo Inhabilitados":
            socios = [s for s in self.socio_dao.obtener_todos() if not s.activo]
        else:
            socios = self.socio_dao.obtener_todos()

        if filtro_texto:
            socios = [
                s for s in socios
                if filtro_texto in (s.nombre or "").lower()
                or filtro_texto in (s.apellido or "").lower()
                or filtro_texto in str(getattr(s, "documento", getattr(s, "dni", ""))).lower()
                or filtro_texto in (s.numero_socio or "").lower()
            ]

        filas = []
        for s in socios:
            # Calcular deuda pendiente
            multas_pendientes = self.multa_dao.obtener_pendientes_por_socio(s.id)
            total_deuda = sum(float(m.monto or 0) for m in multas_pendientes)

            doc = getattr(s, "documento", getattr(s, "dni", "-"))
            filas.append({
                "id": str(s.id),
                "numero_socio": s.numero_socio or "-",
                "nombre_completo": f"{s.nombre} {s.apellido}",
                "documento": str(doc or "-"),
                "telefono": s.telefono or "-",
                "email": s.email or "-",
                "estado": "Habilitado" if s.activo else "Inhabilitado",
                "deuda": f"${total_deuda:,.2f}" if total_deuda > 0 else "$0.00",
            })

        self.tabla.cargar_datos(filas)

    def _obtener_socio_seleccionado(self) -> Optional[Socio]:
        fila = self.tabla.get_selected_row()
        if not fila or not fila.get("id"):
            messagebox.showwarning("Selección requerida", "Por favor seleccione un socio de la lista.")
            return None
        try:
            socio_id = int(fila["id"])
            socio = self.socio_dao.obtener_por_id(socio_id)
            if not socio:
                messagebox.showerror("Error", "No se encontró el socio seleccionado en la base de datos.")
                return None
            return socio
        except (ValueError, TypeError):
            return None

    def _abrir_modal_alta(self) -> None:
        SocioFormModal(
            parent=self.winfo_toplevel(),
            socio_dao=self.socio_dao,
            on_guardar_callback=self.cargar_datos,
        )

    def _abrir_modal_modificar(self) -> None:
        socio = self._obtener_socio_seleccionado()
        if not socio:
            return
        SocioFormModal(
            parent=self.winfo_toplevel(),
            socio_dao=self.socio_dao,
            socio=socio,
            on_guardar_callback=self.cargar_datos,
        )

    def _abrir_modal_multas(self) -> None:
        socio = self._obtener_socio_seleccionado()
        if not socio:
            return

        multas_pendientes = self.multa_dao.obtener_pendientes_por_socio(socio.id)
        if not multas_pendientes:
            messagebox.showinfo(
                "Sin Deudas Pendientes",
                f"El socio {socio.nombre} {socio.apellido} ({socio.numero_socio}) no registra multas ni deudas pendientes de pago.\n\n"
                "Su estado de cuenta se encuentra al día y no requiere ninguna regularización.",
                parent=self.winfo_toplevel(),
            )
            return

        MultasModal(
            parent=self.winfo_toplevel(),
            session=self.session,
            socio=socio,
            on_actualizar_callback=self.cargar_datos,
        )

    def _cambiar_estado_socio(self) -> None:
        socio = self._obtener_socio_seleccionado()
        if not socio:
            return

        nuevo_estado = 0 if socio.activo else 1
        accion_desc = "inhabilitar" if nuevo_estado == 0 else "habilitar"

        confirmar = messagebox.askyesno(
            "Confirmar Cambio de Estado",
            f"¿Está seguro de que desea {accion_desc} al socio {socio.nombre} {socio.apellido}?",
        )
        if not confirmar:
            return

        try:
            socio.activo = nuevo_estado
            self.socio_dao.actualizar()
            messagebox.showinfo(
                "Estado Actualizado",
                f"El socio se encuentra ahora: '{'Habilitado' if nuevo_estado else 'Inhabilitado'}'.",
            )
            self.cargar_datos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el estado: {e}")

    def _eliminar_socio(self) -> None:
        socio = self._obtener_socio_seleccionado()
        if not socio:
            return

        confirmar = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar permanentemente al socio {socio.nombre} {socio.apellido}?\n\n"
            "Nota: Si el socio posee préstamos o multas registradas, la operación no podrá completarse.",
        )
        if not confirmar:
            return

        try:
            self.socio_dao.eliminar(socio)
            messagebox.showinfo("Socio Eliminado", "El socio ha sido eliminado del sistema.")
            self.cargar_datos()
        except Exception as e:
            self.session.rollback()
            messagebox.showerror(
                "Operación Denegada",
                f"No es posible eliminar al socio porque posee registros asociados (préstamos o historial de multas).\n"
                f"Sugerencia: Utilice la opción de 'Cambiar Estado' para inhabilitarlo.\n\nDetalle: {e}",
            )
