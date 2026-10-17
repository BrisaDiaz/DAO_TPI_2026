"""
Vista de Catálogo Bibliográfico y Gestión de Ejemplares (ABMC Completo).

Permite consultar y registrar obras, autores, información editorial,
así como administrar las unidades físicas (ejemplares) radicadas en cada sede.
"""
from datetime import date
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional, List
from sqlalchemy.orm import Session

from api.models import Libro, Autor, Ejemplar, Sede
from api.dao.libro_dao import LibroDAO, AutorDAO
from api.dao.ejemplar_dao import EjemplarDAO
from api.dao.sede_dao import SedeDAO
from src.components.treeview_table import TreeviewTable


class LibroFormModal(tk.Toplevel):
    """Modal para Alta y Modificación de Obras Bibliográficas."""

    def __init__(
        self,
        parent: tk.Widget,
        session: Session,
        libro_dao: LibroDAO,
        autor_dao: AutorDAO,
        libro: Optional[Libro] = None,
        on_guardar_callback: Optional[callable] = None,
    ):
        super().__init__(parent)
        self.session = session
        self.libro_dao = libro_dao
        self.autor_dao = autor_dao
        self.libro = libro
        self.on_guardar_callback = on_guardar_callback

        es_edicion = libro is not None
        self.title("Modificar Obra" if es_edicion else "Registrar Nuevo Libro")
        self.geometry("540x510")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._centrar(parent)
        self._crear_formulario(es_edicion)

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        ancho, alto = 540, 510
        x = parent.winfo_rootx() + (parent.winfo_width() - ancho) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{max(0, x)}+{max(0, y)}")

    def _crear_formulario(self, es_edicion: bool) -> None:
        padding_frame = ttk.Frame(self, padding="25 20")
        padding_frame.pack(fill="both", expand=True)

        titulo_modal = "✏️ Modificar Datos del Libro" if es_edicion else "➕ Registrar Obra en el Catálogo"
        ttk.Label(
            padding_frame,
            text=titulo_modal,
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 15))

        form_frame = ttk.Frame(padding_frame)
        form_frame.pack(fill="x", expand=True)

        # 1. ISBN
        ttk.Label(form_frame, text="ISBN (*):", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w", pady=6
        )
        self.txt_isbn = ttk.Entry(form_frame, width=36, font=("Segoe UI", 10))
        self.txt_isbn.grid(row=0, column=1, sticky="w", pady=6)
        if self.libro:
            self.txt_isbn.insert(0, self.libro.isbn or "")

        # 2. Título
        ttk.Label(form_frame, text="Título de la Obra (*):", font=("Segoe UI", 9, "bold")).grid(
            row=1, column=0, sticky="w", pady=6
        )
        self.txt_titulo = ttk.Entry(form_frame, width=36, font=("Segoe UI", 10))
        self.txt_titulo.grid(row=1, column=1, sticky="w", pady=6)
        if self.libro:
            self.txt_titulo.insert(0, self.libro.titulo or "")

        # 3. Editorial
        ttk.Label(form_frame, text="Editorial:", font=("Segoe UI", 9)).grid(
            row=2, column=0, sticky="w", pady=6
        )
        self.txt_editorial = ttk.Entry(form_frame, width=36, font=("Segoe UI", 10))
        self.txt_editorial.grid(row=2, column=1, sticky="w", pady=6)
        if self.libro and self.libro.editorial:
            self.txt_editorial.insert(0, self.libro.editorial)

        # 4. Año de edición
        ttk.Label(form_frame, text="Año de Edición:", font=("Segoe UI", 9)).grid(
            row=3, column=0, sticky="w", pady=6
        )
        anio_default = str(self.libro.anio if (self.libro and hasattr(self.libro, "anio") and self.libro.anio) else date.today().year)
        self.txt_anio = ttk.Entry(form_frame, width=15, font=("Segoe UI", 10))
        self.txt_anio.insert(0, anio_default)
        self.txt_anio.grid(row=3, column=1, sticky="w", pady=6)

        # Separador para autor
        sep = ttk.Separator(form_frame, orient="horizontal")
        sep.grid(row=4, column=0, columnspan=2, sticky="ew", pady=12)

        ttk.Label(form_frame, text="Autor Principal", font=("Segoe UI", 10, "bold")).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(0, 6)
        )

        # 5. Nombre del Autor
        ttk.Label(form_frame, text="Nombre del Autor (*):", font=("Segoe UI", 9)).grid(
            row=6, column=0, sticky="w", pady=5
        )
        self.txt_autor_nombre = ttk.Entry(form_frame, width=36, font=("Segoe UI", 10))
        self.txt_autor_nombre.grid(row=6, column=1, sticky="w", pady=5)

        # 6. Apellido del Autor
        ttk.Label(form_frame, text="Apellido del Autor (*):", font=("Segoe UI", 9)).grid(
            row=7, column=0, sticky="w", pady=5
        )
        self.txt_autor_apellido = ttk.Entry(form_frame, width=36, font=("Segoe UI", 10))
        self.txt_autor_apellido.grid(row=7, column=1, sticky="w", pady=5)

        # 7. Nacionalidad del Autor (Selector con sugerencias)
        ttk.Label(form_frame, text="Nacionalidad (*):", font=("Segoe UI", 9)).grid(
            row=8, column=0, sticky="w", pady=5
        )
        self.nacionalidades_comunes = [
            "Argentina",
            "Alemana",
            "Brasileña",
            "Británica",
            "Canadiense",
            "Chilena",
            "Colombiana",
            "Cubana",
            "Española",
            "Estadounidense",
            "Francesa",
            "Irlandesa",
            "Italiana",
            "Japonesa",
            "Mexicana",
            "Peruana",
            "Portuguesa",
            "Rusa",
            "Uruguaya",
            "Venezolana",
            "Otra / Desconocida",
        ]
        self.combo_autor_nacionalidad = ttk.Combobox(
            form_frame,
            values=self.nacionalidades_comunes,
            width=34,
            font=("Segoe UI", 10),
        )
        self.combo_autor_nacionalidad.grid(row=8, column=1, sticky="w", pady=5)

        # Cargar autor previo si edita
        if self.libro and self.libro.autores:
            primer_autor = self.libro.autores[0]
            self.txt_autor_nombre.insert(0, primer_autor.nombre or "")
            self.txt_autor_apellido.insert(0, primer_autor.apellido or "")
            nac_existente = getattr(primer_autor, "nacionalidad", "") or "Argentina"
            self.combo_autor_nacionalidad.set(nac_existente)
        else:
            self.combo_autor_nacionalidad.set("Argentina")

        # Botones
        btn_frame = ttk.Frame(padding_frame)
        btn_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=(10, 0))
        ttk.Button(btn_frame, text="Guardar Obra", command=self._guardar).pack(side="right")

        self.txt_titulo.focus()

    def _guardar(self) -> None:
        isbn = self.txt_isbn.get().strip()
        titulo = self.txt_titulo.get().strip()
        editorial = self.txt_editorial.get().strip()
        anio_str = self.txt_anio.get().strip()
        autor_nom = self.txt_autor_nombre.get().strip()
        autor_ape = self.txt_autor_apellido.get().strip()
        autor_nac = self.combo_autor_nacionalidad.get().strip() or "Argentina"

        if not isbn or not titulo:
            messagebox.showwarning("Campos obligatorios", "El ISBN y el Título son datos obligatorios.", parent=self)
            self.txt_isbn.focus()
            return

        if not autor_nom or not autor_ape:
            messagebox.showwarning("Autor requerido", "Debe ingresar el nombre y apellido del autor principal.", parent=self)
            self.txt_autor_nombre.focus()
            return

        anio = None
        if anio_str:
            try:
                anio = int(anio_str)
            except ValueError:
                messagebox.showwarning("Formato inválido", "El año debe ser un número entero válido (ej. 2024).", parent=self)
                self.txt_anio.focus()
                return

        # Validar no duplicidad de ISBN
        try:
            libro_existente = self.libro_dao.obtener_por_isbn(isbn)
        except Exception:
            self.session.rollback()
            libro_existente = self.libro_dao.obtener_por_isbn(isbn)

        if libro_existente and (not self.libro or libro_existente.id != self.libro.id):
            messagebox.showerror(
                "ISBN duplicado",
                f"Ya existe una obra registrada con el ISBN '{isbn}'.",
                parent=self,
            )
            self.txt_isbn.focus()
            return

        try:
            # Buscar o crear autor
            autor = (
                self.session.query(Autor)
                .filter(Autor.nombre.ilike(autor_nom), Autor.apellido.ilike(autor_ape))
                .first()
            )
            if not autor:
                autor = Autor(nombre=autor_nom, apellido=autor_ape, nacionalidad=autor_nac)
                self.autor_dao.crear(autor)
            else:
                # Si existe pero no tenía nacionalidad cargada
                if hasattr(autor, "nacionalidad") and not autor.nacionalidad:
                    autor.nacionalidad = autor_nac
                    self.autor_dao.actualizar()

            if self.libro:
                # Modificación
                self.libro.isbn = isbn
                self.libro.titulo = titulo
                self.libro.editorial = editorial
                if hasattr(self.libro, "anio"):
                    self.libro.anio = anio
                elif hasattr(self.libro, "anio_edicion"):
                    self.libro.anio_edicion = anio

                # Actualizar autor si no está en la lista
                if autor not in self.libro.autores:
                    self.libro.autores = [autor]

                self.libro_dao.actualizar()
                messagebox.showinfo("Éxito", "Obra bibliográfica actualizada correctamente.", parent=self)
            else:
                # Alta
                nuevo_libro = Libro(
                    isbn=isbn,
                    titulo=titulo,
                    editorial=editorial,
                    anio=anio,
                )
                nuevo_libro.autores.append(autor)
                self.libro_dao.crear(nuevo_libro)
                messagebox.showinfo("Éxito", "Obra registrada exitosamente en el catálogo.", parent=self)

            if self.on_guardar_callback:
                self.on_guardar_callback()
            self.destroy()

        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error al guardar", f"No se pudo guardar el libro: {e}", parent=self)


class EjemplarFormModal(tk.Toplevel):
    """Modal para Alta y Modificación de un Ejemplar Físico."""

    def __init__(
        self,
        parent: tk.Widget,
        session: Session,
        libro: Libro,
        ejemplar_dao: EjemplarDAO,
        sede_dao: SedeDAO,
        ejemplar: Optional[Ejemplar] = None,
        on_guardar_callback: Optional[callable] = None,
    ):
        super().__init__(parent)
        self.session = session
        self.libro = libro
        self.ejemplar_dao = ejemplar_dao
        self.sede_dao = sede_dao
        self.ejemplar = ejemplar
        self.on_guardar_callback = on_guardar_callback

        es_edicion = ejemplar is not None
        self.title("Modificar Ejemplar" if es_edicion else "Incorporar Nuevo Ejemplar")
        self.geometry("480x360")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._centrar(parent)
        self._crear_formulario(es_edicion)

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        ancho, alto = 480, 360
        x = parent.winfo_rootx() + (parent.winfo_width() - ancho) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{max(0, x)}+{max(0, y)}")

    def _crear_formulario(self, es_edicion: bool) -> None:
        padding_frame = ttk.Frame(self, padding="25 20")
        padding_frame.pack(fill="both", expand=True)

        titulo_modal = "✏️ Modificar Ejemplar Físico" if es_edicion else "📦 Incorporar Ejemplar a Sede"
        ttk.Label(
            padding_frame,
            text=titulo_modal,
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 5))

        ttk.Label(
            padding_frame,
            text=f"Obra: {self.libro.titulo} (ISBN: {self.libro.isbn})",
            font=("Segoe UI", 9),
            foreground="#64748B",
        ).pack(anchor="w", pady=(0, 15))

        form_frame = ttk.Frame(padding_frame)
        form_frame.pack(fill="x", expand=True)

        # 1. Código de Inventario
        ttk.Label(form_frame, text="Código de Inventario (*):", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w", pady=6
        )
        self.txt_codigo = ttk.Entry(form_frame, width=32, font=("Segoe UI", 10))
        self.txt_codigo.grid(row=0, column=1, sticky="w", pady=6)
        if self.ejemplar:
            self.txt_codigo.insert(0, self.ejemplar.codigo_inventario or "")
        else:
            total_ej = len(self.ejemplar_dao.obtener_todos()) + 1
            self.txt_codigo.insert(0, f"EJ-{total_ej:03d}")

        # 2. Sede de Radicación
        ttk.Label(form_frame, text="Sede de Asignación (*):", font=("Segoe UI", 9, "bold")).grid(
            row=1, column=0, sticky="w", pady=6
        )
        self.sedes_activas = self.sede_dao.obtener_activas()
        nombres_sedes = [f"{s.direccion} (ID {s.id})" for s in self.sedes_activas]

        self.combo_sede = ttk.Combobox(
            form_frame,
            values=nombres_sedes,
            state="readonly",
            width=30,
            font=("Segoe UI", 9),
        )
        self.combo_sede.grid(row=1, column=1, sticky="w", pady=6)

        if self.ejemplar and self.ejemplar.sede:
            self.combo_sede.set(f"{self.ejemplar.sede.direccion} (ID {self.ejemplar.sede.id})")
        elif nombres_sedes:
            self.combo_sede.current(0)

        # 3. Estado Físico
        ttk.Label(form_frame, text="Estado Físico:", font=("Segoe UI", 9, "bold")).grid(
            row=2, column=0, sticky="w", pady=6
        )
        self.combo_estado = ttk.Combobox(
            form_frame,
            values=["Disponible", "Prestado", "Dañado", "Extraviado"],
            state="readonly",
            width=30,
            font=("Segoe UI", 9),
        )
        estado_previo = self.ejemplar.estado_fisico if self.ejemplar else "Disponible"
        self.combo_estado.set(estado_previo)
        self.combo_estado.grid(row=2, column=1, sticky="w", pady=6)

        # Botones
        btn_frame = ttk.Frame(padding_frame)
        btn_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=(10, 0))
        ttk.Button(btn_frame, text="Guardar Ejemplar", command=self._guardar).pack(side="right")

        self.txt_codigo.focus()

    def _guardar(self) -> None:
        codigo = self.txt_codigo.get().strip()
        sede_idx = self.combo_sede.current()
        estado = self.combo_estado.get().strip()

        if not codigo:
            messagebox.showwarning("Código requerido", "El código de inventario es obligatorio.", parent=self)
            self.txt_codigo.focus()
            return

        if sede_idx < 0 or not self.sedes_activas:
            messagebox.showwarning("Sede requerida", "Debe seleccionar una sede válida para radicar el ejemplar.", parent=self)
            return

        sede_seleccionada = self.sedes_activas[sede_idx]

        # Validar no duplicidad de código
        ejemplar_existente = self.ejemplar_dao.obtener_por_codigo_inventario(codigo)
        if ejemplar_existente and (not self.ejemplar or ejemplar_existente.id != self.ejemplar.id):
            messagebox.showerror(
                "Código duplicado",
                f"Ya existe un ejemplar registrado con el código de inventario '{codigo}'.",
                parent=self,
            )
            self.txt_codigo.focus()
            return

        try:
            if self.ejemplar:
                self.ejemplar.codigo_inventario = codigo
                self.ejemplar.sede_id = sede_seleccionada.id
                self.ejemplar.estado_fisico = estado
                self.ejemplar_dao.actualizar()
                messagebox.showinfo("Éxito", "Ejemplar actualizado correctamente.", parent=self)
            else:
                nuevo = Ejemplar(
                    codigo_inventario=codigo,
                    estado_fisico=estado,
                    libro_id=self.libro.id,
                    sede_id=sede_seleccionada.id,
                )
                self.ejemplar_dao.crear(nuevo)
                messagebox.showinfo("Éxito", "Ejemplar incorporado al inventario exitosamente.", parent=self)

            if self.on_guardar_callback:
                self.on_guardar_callback()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error al guardar", f"No se pudo guardar el ejemplar: {e}", parent=self)


class EjemplaresModal(tk.Toplevel):
    """Ventana para gestionar todas las unidades físicas de una obra seleccionada."""

    def __init__(
        self,
        parent: tk.Widget,
        session: Session,
        libro: Libro,
        on_actualizar_callback: Optional[callable] = None,
    ):
        super().__init__(parent)
        self.session = session
        self.libro = libro
        self.on_actualizar_callback = on_actualizar_callback

        self.ejemplar_dao = EjemplarDAO(session)
        self.sede_dao = SedeDAO(session)

        self.title(f"Unidades Físicas en Red — {libro.titulo}")
        self.geometry("740x480")
        self.minsize(640, 400)
        self.transient(parent)
        self.grab_set()

        self._centrar(parent)
        self._crear_interfaz()

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        ancho, alto = 740, 480
        x = parent.winfo_rootx() + (parent.winfo_width() - ancho) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{max(0, x)}+{max(0, y)}")

    def _crear_interfaz(self) -> None:
        main_frame = ttk.Frame(self, padding="20 15")
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # 1. Encabezado
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(
            info_frame,
            text=f"Inventario Físico: {self.libro.titulo}",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        self.lbl_resumen = ttk.Label(
            info_frame,
            text="",
            font=("Segoe UI", 10),
            foreground="#64748B",
        )
        self.lbl_resumen.pack(anchor="w", pady=(2, 0))

        # 2. Tabla de Ejemplares (expandible)
        table_container = ttk.Frame(main_frame)
        table_container.grid(row=1, column=0, sticky="nsew", pady=5)
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        columnas = [
            ("id", "ID", 60),
            ("codigo", "Cód. Inventario", 140),
            ("sede", "Sede de Radicación", 300),
            ("estado", "Estado Físico", 140),
        ]

        self.tabla = TreeviewTable(
            table_container,
            columns=columnas,
            on_double_click=lambda row: self._editar_ejemplar(),
        )
        self.tabla.grid(row=0, column=0, sticky="nsew")

        # 3. Barra de Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(15, 0))

        ttk.Button(
            btn_frame,
            text="➕ Nuevo Ejemplar",
            command=self._nuevo_ejemplar,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            btn_frame,
            text="✏️ Modificar",
            command=self._editar_ejemplar,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            btn_frame,
            text="🗑️ Dar de Baja Ejemplar",
            command=self._eliminar_ejemplar,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            btn_frame,
            text="Cerrar",
            command=self.destroy,
        ).pack(side="right")

        self.cargar_ejemplares()

    def cargar_ejemplares(self) -> None:
        """Carga las unidades físicas de este libro en particular."""
        ejemplares = self.ejemplar_dao.obtener_por_libro(self.libro.id)
        disponibles = sum(1 for e in ejemplares if e.estado_fisico == "Disponible")
        total = len(ejemplares)

        self.lbl_resumen.configure(
            text=f"ISBN: {self.libro.isbn}  |  Total de unidades: {total}  |  Disponibles para retiro: {disponibles}"
        )

        filas = [
            {
                "id": str(e.id),
                "codigo": e.codigo_inventario or "-",
                "sede": e.sede.direccion if e.sede else f"Sede ID {e.sede_id}",
                "estado": e.estado_fisico or "Disponible",
            }
            for e in ejemplares
        ]
        self.tabla.cargar_datos(filas)

        if self.on_actualizar_callback:
            self.on_actualizar_callback()

    def _obtener_ejemplar_seleccionado(self) -> Optional[Ejemplar]:
        fila = self.tabla.get_selected_row()
        if not fila or not fila.get("id"):
            messagebox.showwarning("Selección requerida", "Por favor seleccione un ejemplar de la tabla.", parent=self)
            return None
        try:
            ej_id = int(fila["id"])
            ejemplar = self.ejemplar_dao.obtener_por_id(ej_id)
            if not ejemplar:
                messagebox.showerror("Error", "No se encontró el registro del ejemplar.", parent=self)
                return None
            return ejemplar
        except (ValueError, TypeError):
            return None

    def _nuevo_ejemplar(self) -> None:
        EjemplarFormModal(
            parent=self,
            session=self.session,
            libro=self.libro,
            ejemplar_dao=self.ejemplar_dao,
            sede_dao=self.sede_dao,
            on_guardar_callback=self.cargar_ejemplares,
        )

    def _editar_ejemplar(self) -> None:
        ej = self._obtener_ejemplar_seleccionado()
        if not ej:
            return
        EjemplarFormModal(
            parent=self,
            session=self.session,
            libro=self.libro,
            ejemplar_dao=self.ejemplar_dao,
            sede_dao=self.sede_dao,
            ejemplar=ej,
            on_guardar_callback=self.cargar_ejemplares,
        )

    def _eliminar_ejemplar(self) -> None:
        ej = self._obtener_ejemplar_seleccionado()
        if not ej:
            return

        if ej.estado_fisico == "Prestado":
            messagebox.showwarning(
                "No permitido",
                f"El ejemplar '{ej.codigo_inventario}' se encuentra actualmente prestado y no puede darse de baja.",
                parent=self,
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar Baja de Ejemplar",
            f"¿Está seguro de que desea retirar del inventario el ejemplar '{ej.codigo_inventario}'?",
            parent=self,
        )
        if not confirmar:
            return

        try:
            self.ejemplar_dao.eliminar(ej)
            messagebox.showinfo("Baja confirmada", "El ejemplar fue retirado del inventario.", parent=self)
            self.cargar_ejemplares()
        except Exception as e:
            self.session.rollback()
            messagebox.showerror(
                "Error al eliminar",
                f"No se pudo eliminar el ejemplar por poseer registros asociados (historial de préstamos): {e}",
                parent=self,
            )


class CatalogoView(ttk.Frame):
    """Pestaña de Catálogo de Libros y Ejemplares (ABMC Completo con Filtros)."""

    def __init__(self, parent: tk.Widget, session: Session, **kwargs):
        super().__init__(parent, **kwargs)
        self.session = session
        self.libro_dao = LibroDAO(session)
        self.autor_dao = AutorDAO(session)
        self.sede_dao = SedeDAO(session)
        self.ejemplar_dao = EjemplarDAO(session)

        self._crear_interfaz()

    def _crear_interfaz(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Encabezado
        header_frame = ttk.Frame(self, padding="15 10")
        header_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            header_frame,
            text="📚 Catálogo Bibliográfico & Unidades Físicas",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            header_frame,
            text="Búsqueda de títulos, registro de obras, autores y gestión del stock físico radicado en cada sede.",
            font=("Segoe UI", 10),
            foreground="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        # 2. Barra de Búsqueda y Filtros
        filter_frame = ttk.Frame(self, padding="15 5")
        filter_frame.grid(row=1, column=0, sticky="ew")

        ttk.Label(filter_frame, text="Buscar título o ISBN:", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.txt_buscar = ttk.Entry(filter_frame, width=26, font=("Segoe UI", 9))
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

        # Filtro por Sede de radicación
        ttk.Label(filter_frame, text="Sede:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(5, 5))
        self.sedes_lista = self.sede_dao.obtener_todos()
        opciones_sedes = ["Todas las Sedes"] + [s.direccion for s in self.sedes_lista]

        self.combo_sede_filtro = ttk.Combobox(
            filter_frame,
            values=opciones_sedes,
            state="readonly",
            width=24,
            font=("Segoe UI", 9),
        )
        self.combo_sede_filtro.set("Todas las Sedes")
        self.combo_sede_filtro.pack(side="left")
        self.combo_sede_filtro.bind("<<ComboboxSelected>>", lambda e: self.cargar_datos())

        # 3. Contenedor central (Tabla de catálogo)
        main_content = ttk.Frame(self, padding="15 5")
        main_content.grid(row=2, column=0, sticky="nsew")
        main_content.grid_rowconfigure(0, weight=1)
        main_content.grid_columnconfigure(0, weight=1)

        columnas = [
            ("id", "ID", 50),
            ("isbn", "ISBN", 130),
            ("titulo", "Título de la Obra", 270),
            ("autores", "Autor(es)", 190),
            ("editorial", "Editorial", 140),
            ("anio", "Año", 65),
            ("ejemplares", "Total Ejemplares", 110),
            ("disponibles", "Disponibles", 100),
        ]

        self.tabla = TreeviewTable(
            main_content,
            columns=columnas,
            on_double_click=lambda row: self._abrir_modal_ejemplares(),
        )
        self.tabla.grid(row=0, column=0, sticky="nsew")

        # 4. Barra de Acciones inferior (Botones ABMC)
        actions_frame = ttk.Frame(self, padding="15 10")
        actions_frame.grid(row=3, column=0, sticky="ew")

        ttk.Button(
            actions_frame,
            text="➕ Nuevo Libro",
            command=self._abrir_modal_alta_libro,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="✏️ Modificar Obra",
            command=self._abrir_modal_modificar_libro,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="📦 Gestionar Ejemplares en Sedes",
            command=self._abrir_modal_ejemplares,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="🗑️ Eliminar Obra",
            command=self._eliminar_libro,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions_frame,
            text="🔄 Actualizar",
            command=self.cargar_datos,
        ).pack(side="right")

        self.cargar_datos()

    def _limpiar_filtro(self) -> None:
        self.txt_buscar.delete(0, tk.END)
        self.combo_sede_filtro.set("Todas las Sedes")
        self.cargar_datos()

    def cargar_datos(self) -> None:
        """Carga y filtra el catálogo de obras con balance de ejemplares."""
        filtro_texto = self.txt_buscar.get().strip().lower()
        filtro_sede = self.combo_sede_filtro.get()

        libros = self.libro_dao.obtener_todos()

        # Filtrar por sede si se seleccionó una sede específica
        if filtro_sede != "Todas las Sedes":
            sede_obj = next((s for s in self.sedes_lista if s.direccion == filtro_sede), None)
            if sede_obj:
                libros = [
                    l for l in libros
                    if any(e.sede_id == sede_obj.id for e in l.ejemplares)
                ]

        if filtro_texto:
            libros = [
                l for l in libros
                if filtro_texto in (l.titulo or "").lower()
                or filtro_texto in (l.isbn or "").lower()
                or any(filtro_texto in (a.apellido or "").lower() or filtro_texto in (a.nombre or "").lower() for a in l.autores)
            ]

        filas = []
        for l in libros:
            autores_str = ", ".join(f"{a.nombre} {a.apellido}" for a in l.autores) if l.autores else "Sin autor"
            ejemplares_lista = l.ejemplares if hasattr(l, "ejemplares") else []
            total_ej = len(ejemplares_lista)
            disp_ej = sum(1 for e in ejemplares_lista if e.estado_fisico == "Disponible")
            anio_val = getattr(l, "anio", getattr(l, "anio_edicion", "-"))

            filas.append({
                "id": str(l.id),
                "isbn": l.isbn or "-",
                "titulo": l.titulo or "-",
                "autores": autores_str,
                "editorial": l.editorial or "-",
                "anio": str(anio_val or "-"),
                "ejemplares": str(total_ej),
                "disponibles": str(disp_ej),
            })

        self.tabla.cargar_datos(filas)

    def _obtener_libro_seleccionado(self) -> Optional[Libro]:
        fila = self.tabla.get_selected_row()
        if not fila or not fila.get("id"):
            messagebox.showwarning("Selección requerida", "Por favor seleccione una obra bibliográfica de la lista.")
            return None
        try:
            libro_id = int(fila["id"])
            libro = self.libro_dao.obtener_por_id(libro_id)
            if not libro:
                messagebox.showerror("Error", "No se encontró el libro seleccionado en la base de datos.")
                return None
            return libro
        except (ValueError, TypeError):
            return None

    def _abrir_modal_alta_libro(self) -> None:
        LibroFormModal(
            parent=self.winfo_toplevel(),
            session=self.session,
            libro_dao=self.libro_dao,
            autor_dao=self.autor_dao,
            on_guardar_callback=self.cargar_datos,
        )

    def _abrir_modal_modificar_libro(self) -> None:
        libro = self._obtener_libro_seleccionado()
        if not libro:
            return
        LibroFormModal(
            parent=self.winfo_toplevel(),
            session=self.session,
            libro_dao=self.libro_dao,
            autor_dao=self.autor_dao,
            libro=libro,
            on_guardar_callback=self.cargar_datos,
        )

    def _abrir_modal_ejemplares(self) -> None:
        libro = self._obtener_libro_seleccionado()
        if not libro:
            return
        EjemplaresModal(
            parent=self.winfo_toplevel(),
            session=self.session,
            libro=libro,
            on_actualizar_callback=self.cargar_datos,
        )

    def _eliminar_libro(self) -> None:
        libro = self._obtener_libro_seleccionado()
        if not libro:
            return

        confirmar = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar la obra '{libro.titulo}' (ISBN: {libro.isbn})?\n\n"
            "Nota: Solo podrá eliminarse si no cuenta con ejemplares físicos ni préstamos asociados.",
        )
        if not confirmar:
            return

        try:
            self.libro_dao.eliminar(libro)
            messagebox.showinfo("Obra Eliminada", "El libro ha sido eliminado del catálogo general.")
            self.cargar_datos()
        except Exception as e:
            self.session.rollback()
            messagebox.showerror(
                "Operación Denegada",
                f"No es posible eliminar el libro porque posee ejemplares físicos o historial registrado.\n"
                f"Elimine primero los ejemplares desde el panel de gestión.\n\nDetalle: {e}",
            )
