# Biblioteca: Sistema de Préstamos Interbibliotecarios

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-48%20passed-brightgreen.svg)](tests/)
[![ORM](https://img.shields.io/badge/ORM-SQLAlchemy%202.0-red.svg)](https://www.sqlalchemy.org/)
[![GUI](https://img.shields.io/badge/GUI-Tkinter-orange.svg)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/license-Academic%20%2F%20MIT-lightgrey.svg)]()

> **Trabajo Práctico Integrador (TPI 2026)**  
> **Cátedra:** Desarrollo de Aplicaciones con Objetos (DAO) — 4° Año  
> **Institución:** Universidad Tecnológica Nacional - Facultad Regional Córdoba (UTN FRC)  
> **Integrantes:**  
> * Brisa Abigaíl Díaz (Legajo: 97287)
> * Enzo Valentino Cardelli (Legajo: 400042)  
> * Augusto Bossi (Legajo: 87917)  

---

## 📖 Descripción Breve

**Biblioteca** es una solución integral de escritorio orientada a objetos para la administración y logística de una red de bibliotecas públicas interconectadas. El sistema resuelve la problemática habitual del seguimiento manual y disperso del inventario bibliográfico, permitiendo coordinar traslados físicos de ejemplares entre distintas sedes mediante remitos con trazabilidad de estados en tiempo real.

A diferencia de los sistemas de biblioteca convencionales monosede, esta aplicación incorpora de manera nativa la gestión de **préstamos interbibliotecarios**, el control automatizado de sanciones económicas por mora o deterioro, notificaciones automáticas de reservas y una arquitectura por capas estrictamente desacoplada (**DAO + Servicios + Modelos ORM**) que implementa patrones de diseño formales (**GoF**) para modelar procesos críticos de negocio.

---

## ✨ Características (Features)

* **Gestión Multisede:** Administración completa de sucursales (altas, bajas lógicas, contactos y verificación de disponibilidad operativa).
* **Catálogo y Control de Ejemplares Físicos:** Registro de libros y autores con relación muchos a muchos ($N:M$), asignando cada unidad física estrictamente a su sede de radicación.
* **Préstamos Locales e Interbibliotecarios:** Diferenciación operativa entre retiros en sede y traslados logísticos inter-sedes.
* **Trazabilidad Logística con Patrón State:** Ciclo de vida estricto del remito interbibliotecario (`Empaquetado` $\rightarrow$ `Despachado` $\rightarrow$ `Recibido`, con soporte para registro y resolución de incidencias en tránsito).
* **Cálculo de Sanciones con Patrón Strategy:** Políticas dinámicas e intercambiables para el cálculo de multas diarias por mora (`MultaEstandar`, `MultaReducidaEstudiante`, `SinMultaPromocional`), con reactivación automática del socio al regularizar la deuda.
* **Notificaciones de Reservas con Patrón Observer:** Cuando un ejemplar prestado es devuelto en estado `Disponible`, el sujeto observable (`DisponibilidadEjemplarSubject`) notifica automáticamente a todos los socios suscriptos en lista de espera (`SocioObserver`).
* **Validaciones de Negocio Obligatorias (RN-01 a RN-05 y SUP-01 a SUP-08):** Bloqueo preventivo de socios con deuda o inhabilitados, límite de préstamos simultáneos, verificación de disponibilidad física del material, pertenencia de sede y bloqueo de operaciones en sedes dadas de baja.
* **Reportes Analíticos No Triviales:** Consultas analíticas avanzadas con JOINs múltiples, funciones de agregación, agrupamientos y filtros (`CASE`, `COALESCE`, `COUNT`, `SUM`).
* **Arquitectura Desacoplada:** División limpia entre el backend local (`api/`) y la interfaz visual (`src/`).

---

## 🛠️ Requisitos Previos (Prerequisites)

Antes de comenzar, asegúrate de contar con las siguientes herramientas instaladas en tu sistema:

* **Python 3.10 o superior** (probado y verificado en Python 3.12 / 3.13).
* **Git** (para clonado y gestión de versiones).
* **Tkinter:** Generalmente incluido de forma nativa en las instalaciones estándar de Python para Windows. En distribuciones Linux basadas en Debian/Ubuntu, puede requerir: `sudo apt-get install python3-tk`.

---

## 🚀 Instalación y Puesta en Marcha

Sigue estos pasos para clonar el repositorio, configurar el entorno virtual y levantar la aplicación:

### 1. Clonar el repositorio
```bash
git clone https://github.com/BrisaDiaz/DAO_TPI_2026.git
cd DAO_TPI_2026
```

### 2. Crear y activar el entorno virtual
* **En Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
* **En Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 4. Inicializar la base de datos (SQLite)
La base de datos se genera y puebla con datos iniciales (*seed*) automáticamente en la primera ejecución, pero puedes forzar la creación de tablas ejecutando:
```bash
python -c "from api.database import crear_tablas; crear_tablas()"
```

### 5. Ejecutar la aplicación
```bash
python main.py
```

---

## 🧪 Ejecución de Pruebas (Tests)

El proyecto cuenta con una batería de **48 pruebas unitarias automatizadas** utilizando **Pytest**, cubriendo el ciclo de vida de los patrones y las reglas de validación:

```bash
pytest tests/ -v
```

### Cobertura de las suites actuales:
* **`tests/test_remitos_state.py` (9 tests):** Valida las transiciones del patrón State (`Empaquetado` $\rightarrow$ `Despachado` $\rightarrow$ `Recibido`), prohibición de transiciones inválidas, manejo y resolución de incidencias en trayecto.
* **`tests/test_multas.py` (12 tests):** Valida las estrategias concretas del patrón Strategy, el selector dinámico de tarifas, cálculo por días de mora, cargos por daño/extravío, pago, condonación y reactivación del socio.
* **`tests/test_prestamos.py` (11 tests):** Valida las reglas de negocio RN-01 a RN-04, los supuestos SUP-04, SUP-07 y SUP-08, préstamos locales vs. interbibliotecarios y devoluciones.
* **`tests/test_reservas.py` (7 tests):** Valida la creación de reservas con stock agotado (SUP-06), límite de préstamos (SUP-04), cancelaciones y caducidad automática a las 48h (SUP-05).
* **`tests/test_observer.py` (5 tests):** Valida la estructura del patrón Observer (`Subject`, `Observer`, `attach`, `detach`, `notify`) y su disparo automático al registrar la devolución de un ejemplar con reservas pendientes.
* **`tests/test_reportes.py` (4 tests):** Valida la ejecución y estructura de los 4 reportes analíticos no triviales.

---

## 🏛️ Estructura del Proyecto y Guía para Desarrolladores / IAs

El proyecto está diseñado siguiendo una separación de responsabilidades estricta entre la lógica de negocio y la interfaz:

```text
DAO_TPI_2026/
├── api/                           # Backend local (Persistencia y Lógica de Negocio)
│   ├── database.py                # Conexión SQLAlchemy 2.0 y sesión transaccional (SessionLocal)
│   ├── models.py                  # Entidades ORM (Sede, Socio, Libro, Ejemplar, Prestamo, etc.)
│   ├── seed.py                    # Script de población de datos iniciales (Seed)
│   ├── dao/                       # Capa DAO (BaseDAO genérico y DAOs específicos por entidad)
│   │   ├── base_dao.py
│   │   ├── sede_dao.py
│   │   ├── socio_dao.py
│   │   ├── libro_dao.py
│   │   ├── ejemplar_dao.py
│   │   ├── prestamo_dao.py
│   │   ├── multa_dao.py
│   │   ├── remito_dao.py
│   │   └── reserva_dao.py
│   └── services/                  # Orquestadores de negocio y aplicación de patrones
│       ├── prestamo_service.py     # Orquestación de préstamos, validaciones y disparo de Observer
│       ├── logistica_service.py    # Patrón State para ciclo de vida de Remitos
│       ├── multa_service.py        # Patrón Strategy para cálculo de multas y regularización
│       ├── notificacion_service.py # Patrón Observer (Subject / Observer) para reservas disponibles
│       ├── reserva_service.py      # Lógica de negocio y gestión de reservas de ejemplares
│       └── reporte_service.py      # Consultas analíticas para los 4 Reportes No Triviales
│
├── src/                           # Frontend local (Interfaz Gráfica de Usuario en Tkinter)
│   ├── pages/                     # Ventanas y vistas (Notebook por pestañas, Sedes, Socios, etc.)
│   └── components/                # Componentes reutilizables (Treeviews tabulares, modales, formularios)
│
├── tests/                         # Suites de pruebas automatizadas con Pytest
├── main.py                        # Punto de entrada de la aplicación
├── requirements.txt               # Lista formal de dependencias (SQLAlchemy, Pytest)
└── *.md                           # Documentación de análisis y diseño académico
```

### 🤖 Directrices para Asistentes de IA (AI Guidelines)
Si estás asistiendo en el desarrollo de este repositorio:
1. **Nunca violes el patrón DAO:** La capa visual (`src/`) y los servicios (`api/services/`) no deben ejecutar queries directas de SQLAlchemy contra la base de datos si dicha operación corresponde a un DAO (`api/dao/`).
2. **Preserva el desacoplamiento `api/` vs `src/`:** Toda regla de negocio (validaciones, cálculos, transiciones) debe resolverse en `api/services/`. `src/` sólo debe manejar eventos de UI, captura de inputs y renderizado visual.
3. **Tipado Estricto:** Mantener el uso de `typing` (`Optional`, `List`, `Dict`, `Union`, type hints de Python 3.10+) en todas las firmas públicas.
4. **Respeto a las Reglas de Negocio:** Toda nueva funcionalidad de préstamo debe respetar las directivas RN-01 a RN-05 y SUP-01 a SUP-08 descritas en [Reglas_Negocio_y_Supuestos.md](file:///e:/Escritorio/UTN/4%20Cuarto%20A%C3%B1o/TP-DAO/DAO_TPI_2026/Reglas_Negocio_y_Supuestos.md).

---

## 📌 Próximos Cambios (Roadmap)

- [X] **Desarrollo de Vistas en Tkinter (`src/pages/`):**
  - [X] `main_window.py`: Ventana principal con navegación por pestañas (`ttk.Notebook`).
  - [X] `sedes_view.py`: Alta, modificación y listado con estado de sedes.
  - [X] `socios_view.py`: Gestión de socios, panel de multas pendientes y botón de regularización/pago.
  - [X] `prestamos_view.py`: Formulario para registrar préstamos locales e interbibliotecarios con validación en vivo.
  - [X] `remitos_view.py`: Panel visual de seguimiento de envíos con botones interactivos para avanzar estados (`Empaquetado` $\rightarrow$ `Despachado` $\rightarrow$ `Recibido`).
  - [X] `reportes_view.py`: Visor tabular interactivo para los 4 reportes no triviales exigidos.
  - [X] `reservas_view.py`: Interfaz para la gestión, alta, consulta, cancelación de reservas y visor de notificaciones Observer.
- [X] **Lógica de Negocio y Backend (`api/services/`):**
  - [X] `reserva_service.py`: Orquestador de reglas de negocio para la gestión de reservas, validación de stock no disponible y caducidad.
  - [X] Implementación y validación formal en servicios de los nuevos supuestos del dominio (`SUP-04` a `SUP-08`).
  - [X] Creación de un script o rutina de inicialización de datos (*seed* de datos iniciales) para poblar la base de datos con registros de prueba (sedes, autores, libros, ejemplares, socios y préstamos).
- [X] **Pruebas Automatizadas (`tests/`):**
  - [X] Creación de nuevas suites de prueba en Pytest para cubrir el servicio de reservas y la validación de los supuestos del dominio agregados.
- [X] **Componentes Reutilizables (`src/components/`):**
  - [X] Grilla estándar (`ttk.Treeview`) con soporte para ordenamiento por columnas.
  - [X] Modales de confirmación y captura de errores amigables.
- [X] **Opcionales del Dominio:**
  - [X] Implementación del patrón **Observer** (`notificacion_service.py`) para notificaciones automáticas al liberar ejemplares con reservas pendientes.

---

## 🤝 Contribución (Contributing)

Las contribuciones se rigen bajo el flujo de trabajo estándar de Git:

1. **Hacer un Fork** del repositorio.
2. **Crear una rama** temática descriptiva:
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```
3. **Realizar los cambios** asegurando que todos los tests pasen (`pytest tests/`).
4. **Hacer Commit** siguiendo un formato claro:
   ```bash
   git commit -m "feat: implementar visor gráfico para reporte de vencidos"
   ```
5. **Hacer Push** a tu rama:
   ```bash
   git push origin feature/nueva-funcionalidad
   ```
6. **Abrir un Pull Request** detallando las modificaciones realizadas.
