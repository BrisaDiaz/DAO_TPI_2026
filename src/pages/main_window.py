"""
Ventana Principal de la Aplicación.

Contenedor de navegación por pestañas (ttk.Notebook) para los módulos
del sistema (Sedes, Socios, Catálogo, Préstamos y Reportes), con gestión
de sesión de base de datos y estilo profesional de escritorio.
"""
import tkinter as tk
from tkinter import ttk

from api.database import SessionLocal
from src.pages.sedes_view import SedesView
from src.pages.socios_view import SociosView
from src.pages.catalogo_view import CatalogoView
from src.pages.prestamos_view import PrestamosView
from src.pages.reportes_view import ReportesView
from src.pages.reservas_view import ReservasView

class MainWindow(tk.Tk):
    """Ventana principal del sistema de gestión de bibliotecas."""

    def __init__(self):
        super().__init__()

        # Configuración de ventana
        self.title("Sistema de Gestión de Bibliotecas — Red Interbibliotecaria")
        self.geometry("1180x740")
        self.minsize(980, 620)

        # Centrar ventana en pantalla
        self._centrar_ventana(1180, 740)

        # Sesión transaccional centralizada
        self.db_session = SessionLocal()

        # Estilos visuales
        self._configurar_estilos()

        # Interfaz
        self._crear_widgets()

        # Protocolo de cierre seguro
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _centrar_ventana(self, ancho: int, alto: int) -> None:
        """Centra la ventana en la pantalla del usuario."""
        self.update_idletasks()
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()
        pos_x = max(0, (pantalla_ancho - ancho) // 2)
        pos_y = max(0, (pantalla_alto - alto) // 2)
        self.geometry(f"{ancho}x{alto}+{pos_x}+{pos_y}")

    def _configurar_estilos(self) -> None:
        """Configura el tema y paleta de colores ttk."""
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        COLOR_PRIMARIO = "#1E3A8A"      # Azul marino
        COLOR_FONDO = "#F8FAFC"         # Fondo claro
        self.configure(bg=COLOR_FONDO)

        # Notebook (Pestañas)
        self.style.configure(
            "TNotebook",
            background=COLOR_FONDO,
            borderwidth=0,
        )
        self.style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 10, "bold"),
            padding=(18, 8),
            background="#E2E8F0",
            foreground="#475569",
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", "#FFFFFF"), ("active", "#CBD5E1")],
            foreground=[("selected", COLOR_PRIMARIO), ("active", "#1E293B")],
        )

        # Treeview (Tablas)
        self.style.configure(
            "Treeview",
            font=("Segoe UI", 10),
            rowheight=28,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            borderwidth=1,
        )
        self.style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#F1F5F9",
            foreground="#1E293B",
            relief="flat",
            padding=(6, 6),
        )
        self.style.map(
            "Treeview.Heading",
            background=[("active", "#E2E8F0")],
        )
        self.style.map(
            "Treeview",
            background=[("selected", "#DBEAFE")],
            foreground=[("selected", "#1E3A8A")],
        )

        # Botones
        self.style.configure(
            "TButton",
            font=("Segoe UI", 10),
            padding=(10, 5),
        )

    def _crear_widgets(self) -> None:
        """Crea el encabezado, el contenedor de pestañas y la barra de estado."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Banner superior de encabezado
        header_frame = tk.Frame(self, bg="#1E293B", height=65)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title_lbl = tk.Label(
            header_frame,
            text="🏛️ Red Provincial de Bibliotecas",
            font=("Segoe UI", 15, "bold"),
            fg="#FFFFFF",
            bg="#1E293B",
        )
        title_lbl.pack(side="left", padx=20, pady=(10, 2))

        subtitle_lbl = tk.Label(
            header_frame,
            text="Sistema Integral de Gestión y Logística Interbibliotecaria",
            font=("Segoe UI", 9),
            fg="#94A3B8",
            bg="#1E293B",
        )
        subtitle_lbl.pack(side="left", padx=5, pady=(15, 2))

        # 2. Contenedor de Pestañas (Notebook)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=12, pady=(10, 5))

        # Inicializar vistas modulares
        self.vista_sedes = SedesView(self.notebook, session=self.db_session)
        self.vista_socios = SociosView(self.notebook, session=self.db_session)
        self.vista_catalogo = CatalogoView(self.notebook, session=self.db_session)
        self.vista_prestamos = PrestamosView(self.notebook, session=self.db_session)
        self.vista_reservas = ReservasView(self.notebook, session=self.db_session)
        self.vista_reportes = ReportesView(self.notebook, session=self.db_session)

        # Agregar pestañas
        self.notebook.add(self.vista_sedes, text=" 🏢 Sedes ")
        self.notebook.add(self.vista_socios, text=" 👥 Socios ")
        self.notebook.add(self.vista_catalogo, text=" 📚 Catálogo ")
        self.notebook.add(self.vista_prestamos, text=" 🔄 Préstamos & Remitos ")
        self.notebook.add(self.vista_reservas, text=" 📌 Reservas ")
        self.notebook.add(self.vista_reportes, text=" 📊 Informes & Estadísticas ")

        # 3. Barra de Estado inferior
        status_frame = tk.Frame(self, bg="#F1F5F9", height=26, relief="groove", borderwidth=1)
        status_frame.grid(row=2, column=0, sticky="ew")

        lbl_status = tk.Label(
            status_frame,
            text="🟢 Conectado al servidor | Base de datos activa",
            font=("Segoe UI", 9),
            fg="#334155",
            bg="#F1F5F9",
        )
        lbl_status.pack(side="left", padx=15)

        lbl_info = tk.Label(
            status_frame,
            text="Terminal de Operaciones | Red Interbibliotecaria",
            font=("Segoe UI", 9),
            fg="#64748B",
            bg="#F1F5F9",
        )
        lbl_info.pack(side="right", padx=15)

    def _on_closing(self) -> None:
        """Cierra de forma limpia la sesión de base de datos al salir."""
        try:
            self.db_session.close()
        except Exception:
            pass
        self.destroy()
