#  Stack Tecnológico y Estructura

## 1. Stack Tecnológico Oficial (Actualizado)

Para cumplir con los estándares de la materia *Desarrollo de Aplicaciones con Objetos* (UTN FRC) y ofrecer una experiencia de usuario amigable, el proyecto utilizará:

* **Lenguaje de Programación:**
* **Python 3.10+** (con tipado estricto `typing`).


* **Gestión de Entorno y Dependencias:**
* **Pip / venv** con el archivo `requirements.txt`.


* **Capa de Persistencia y ORM:**
* **SQLAlchemy 2.0+** (Mapeo objeto-relacional y sesiones transaccionales explícites).


* **Base de Datos:**
* **SQLite** (Base de datos relacional liviana local).


* **Capa de Presentación (Interfaz de Usuario Amigable):**
* **Tkinter:** Biblioteca gráfica nativa de Python para el desarrollo de la interfaz de escritorio (GUI). Se utilizará junto con componentes estructurados como pestañas (`ttk.Notebook`), tablas (`ttk.Treeview`) y formularios modales (`Toplevel`) para que el usuario interactúe de forma visual, intuitiva y amigable con el sistema (altamente valorado para evitar interfaces de solo consola).


* **Testing y Calidad de Código:**
* **Pytest** para pruebas unitarias de la lógica de negocio (cálculo de multas, transiciones de remitos, validaciones).


* **Control de Versiones:**
* **Git & GitHub** (ramas por módulos).



---

## 2. Dependencias Exactas (`requirements.txt`)

```text
SQLAlchemy==2.0.28
pytest==8.1.1

```
---

## 3. Estructura Completa del Proyecto y Arquitectura

```text
TPDao_Biblioteca/
│
├── src/                          # Código fuente principal de la aplicación
│   ├── __init__.py
│   ├── conexion.py               # Configuración del motor SQLAlchemy y SessionLocal
│   │
│   ├── modelo/                   # 1. Capa de Dominio (Entidades y Reglas de Negocio)
│   │   ├── __init__.py
│   │   ├── sede.py               # Entidad Sede (dirección, contacto, horarios, estado)
│   │   ├── socio.py              # Entidad Socio (datos personales, control de inhabilitación)
│   │   ├── autor.py              # Entidad Autor
│   │   ├── libro.py              # Entidad Libro (catálogo y relación N:M con Autor)
│   │   ├── ejemplar.py           # Entidad Ejemplar físico (vinculado a una Sede)
│   │   ├── prestamo.py           # Entidad Préstamo (local e interbibliotecario)
│   │   ├── remito.py             # Entidad Remito (con integración del Patrón State)
│   │   ├── multa.py              # Entidad Multa (gestión de deudas por retrasos)
│   │   └── reserva.py            # Entidad Reserva de material
│   │
│   ├── dao/                      # 2. Capa de Acceso a Datos (Data Access Objects)
│   │   ├── __init__.py
│   │   ├── base_dao.py           # Operaciones genéricas de persistencia
│   │   ├── sede_dao.py           # Operaciones ORM para Sedes
│   │   ├── socio_dao.py          # Operaciones ORM para Socios
│   │   ├── libro_dao.py          # Operaciones ORM para Libros y Autores
│   │   ├── ejemplar_dao.py       # Operaciones ORM para Ejemplares
│   │   ├── prestamo_dao.py       # Operaciones ORM para Préstamos
│   │   ├── remito_dao.py         # Operaciones ORM para Remitos y Trazabilidad
│   │   ├── multa_dao.py          # Operaciones ORM para Multas
│   │   └── reserva_dao.py        # Operaciones ORM para Reservas
│   │
│   ├── servicios/                # 3. Capa de Lógica de Negocio y Orquestadores
│   │   ├── __init__.py
│   │   ├── prestamo_service.py   # Valida disponibilidad, habilitación, pertenencia de sede y préstamos
│   │   ├── logistica_service.py  # Orquesta el empaquetado, despacho, recepción y avance de remitos
│   │   └── multa_service.py      # Calcula días de retraso, genera multas y procesa pagos
│   │
│   ├── reportes/                 # 4. Implementación de Reportes No Triviales
│   │   ├── __init__.py
│   │   └── reporte_service.py    # Consultas complejas (vencidos, demanda inter-sedes, disponibilidad, tránsito)
│   │
│   └── presentacion/             # 5. Capa de Presentación (Interfaz Gráfica de Escritorio - GUI)
│       ├── __init__.py
│       ├── main_window.py        # Ventana principal con pestañas (Notebook de Tkinter) para navegación visual
│       ├── sedes_view.py         # Formatos y tablas (Treeview) para gestión visual de Sedes
│       ├── socios_view.py        # Interfaz gráfica para gestión de Socios y Multas
│       ├── prestamos_view.py     # Interfaz visual para Préstamos y Devoluciones
│       ├── remitos_view.py       # Panel visual de trazabilidad y estados de Remitos
│       └── reportes_view.py      # Visor gráfico en formato tabular de los Reportes No Triviales
│
├── tests/                        # Pruebas Unitarias (Pytest)
│   ├── __init__.py
│   ├── test_prestamos.py         # Valida reglas de negocio de préstamos
│   ├── test_remitos_state.py     # Valida el comportamiento del Patrón State en remitos
│   └── test_multas.py            # Valida cálculo matemático de multas
│
├── main.py                       # Punto de entrada principal (Inicializa la BD e inicia la GUI de Tkinter)
├── requirements.txt              # Dependencias formales del proyecto
└── README.md                     # Documentación general y guía de ejecución

```

---

## 4. Experiencia de Usuario en la GUI (`main_window.py` con Tkinter)

La aplicación de escritorio se estructurará mediante una ventana principal basada en pestañas interactivas (`ttk.Notebook`), permitiendo al usuario realizar todas las operaciones de forma visual y amigable:

* **Pestaña 1 - Sedes & Catálogo:** Botones y tablas para dar de alta, modificar y consultar sucursales, autores, libros y ejemplares físicos.
* **Pestaña 2 - Socios & Multas:** Gestión visual de socios, verificación de estados de cuenta, y botones para registrar el pago o condonación de multas que reactivan automáticamente la habilitación del socio.
* **Pestaña 3 - Préstamos & Reservas:** Formularios desplegables para seleccionar socio, ejemplar y sede, ejecutando préstamos locales o interbibliotecarios con validaciones en tiempo real.
* **Pestaña 4 - Logística (Remitos):** Visualización del trayecto de envíos con botones interactivos para avanzar los estados del Patrón State (`Empaquetado` ➔ `Despachado` ➔ `Recibido`).
* **Pestaña 5 - Reportes No Triviales:** Grillas tabulares interactivas (`ttk.Treeview`) con los 4 reportes de gestión exigidos por la cátedra.