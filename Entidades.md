# Entidades y Relaciones

## 1. Entidades y Atributos

* **Sede**
    * `id` (PK)
    * `direccion`
    * `contacto`
    * `horarios`
    * `estado` (activo / baja)

* **Socio**
    * `id` (PK)
    * `numero_socio` (Único)
    * `documento` (Único)
    * `nombre`
    * `apellido`
    * `email`
    * `telefono`
    * `fecha_alta`
    * `activo` (1 = activo, 0 = inactivo/inhabilitado)

* **Autor**
    * `id` (PK)
    * `nombre`
    * `apellido`
    * `nacionalidad`

* **Libro** (Catálogo general)
    * `id` (PK)
    * `isbn` (Único)
    * `titulo`
    * `editorial`
    * `anio`

* **Ejemplar** (Unidades físicas distribuidas)
    * `id` (PK)
    * `codigo_inventario` (Único)
    * `estado_fisico` (Disponible, Prestado, Dañado, Extraviado)
    * `libro_id` (FK hacia Libro)
    * `sede_id` (FK hacia Sede - indica la sede a la que pertenece físicamente)

* **Prestamo** (Préstamos locales e interbibliotecarios)
    * `id` (PK)
    * `fecha_prestamo`
    * `fecha_devolucion_estimada`
    * `fecha_devolucion_real`
    * `estado` (Activo, Devuelto, Vencido)
    * `socio_id` (FK hacia Socio)
    * `ejemplar_id` (FK hacia Ejemplar)
    * `sede_origen_id` (FK hacia Sede)
    * `sede_destino_id` (FK hacia Sede, en caso de préstamo interbibliotecario)

* **Multa** (Gestión de sanciones por retrasos o daños)
    * `id` (PK)
    * `monto`
    * `estado` (Pendiente, Pagada, Condonada)
    * `fecha_emision`
    * `prestamo_id` (FK hacia Prestamo)
    * `socio_id` (FK hacia Socio)

* **Remito** (Trazabilidad logística del traslado)
    * `id` (PK)
    * `codigo_remito` (Único)
    * `estado` (Empaquetado, Despachado, Recibido, Con incidencias)
    * `fecha_emision`
    * `prestamo_id` (FK hacia Prestamo)

* **Reserva**
    * `id` (PK)
    * `fecha_reserva`
    * `estado` (Pendiente, Concretada, Cancelada, Caducada)
    * `socio_id` (FK hacia Socio)
    * `libro_id` (FK hacia Libro)
    * `sede_id` (FK hacia Sede)

---

## 2. Relaciones y Cardinalidades

* **Autor (N) a (M) Libro**: Relación de muchos a muchos implementada a través de una tabla intermedia `libro_autor`.
* **Libro (1) a (N) Ejemplar**: Un libro del catálogo posee múltiples ejemplares físicos registrados.
* **Sede (1) a (N) Ejemplar**: Una sede aloja múltiples ejemplares físicos; cada ejemplar pertenece de manera estricta a una sede.
* **Socio (1) a (N) Prestamo**: Un socio puede registrar varios préstamos a lo largo del tiempo.
* **Ejemplar (1) a (N) Prestamo**: Un ejemplar físico participa en diversos préstamos históricos.
* **Sede (1) a (N) Prestamo (como Origen / Destino)**: Las sedes actúan como puntos de partida o recepción de los materiales solicitados.
* **Prestamo (1) a (0..1) Multa**: Un préstamo vencido o con daño/extravío puede generar una multa asociada.
* **Socio (1) a (N) Multa**: Un socio acumula multas por sus préstamos vencidos o dañados.
* **Prestamo (1) a (0..1) Remito**: Un préstamo interbibliotecario genera un remito para su trazabilidad logística en el trayecto.
* **Socio (1) a (N) Reserva**: Un socio puede gestionar reservas activas de material sin stock disponible.
* **Libro (1) a (N) Reserva** y **Sede (1) a (N) Reserva**: Una reserva se solicita sobre una obra específica en una sede determinada.

---

## 3. DER (Diagrama Entidad-Relación)

```mermaid
erDiagram
    SEDE {
        int id PK
        string direccion
        string contacto
        string horarios
        string estado
    }
    
    SOCIO {
        int id PK
        string numero_socio
        string documento
        string nombre
        string apellido
        string email
        string telefono
        date fecha_alta
        int activo
    }
    
    AUTOR {
        int id PK
        string nombre
        string apellido
        string nacionalidad
    }
    
    LIBRO {
        int id PK
        string isbn
        string titulo
        string editorial
        int anio
    }
    
    LIBRO_AUTOR {
        int libro_id FK
        int autor_id FK
    }

    EJEMPLAR {
        int id PK
        string codigo_inventario
        string estado_fisico
        int libro_id FK
        int sede_id FK
    }

    PRESTAMO {
        int id PK
        date fecha_prestamo
        date fecha_devolucion_estimada
        date fecha_devolucion_real
        string estado
        int socio_id FK
        int ejemplar_id FK
        int sede_origen_id FK
        int sede_destino_id FK
    }

    MULTA {
        int id PK
        float monto
        string estado
        date fecha_emision
        int prestamo_id FK
        int socio_id FK
    }

    REMITO {
        int id PK
        string codigo_remito
        string estado
        date fecha_emision
        int prestamo_id FK
    }

    RESERVA {
        int id PK
        datetime fecha_reserva
        string estado
        int socio_id FK
        int libro_id FK
        int sede_id FK
    }

    SEDE ||--o{ EJEMPLAR : posee
    LIBRO ||--o{ EJEMPLAR : tiene
    LIBRO ||--o{ LIBRO_AUTOR : escrita_por
    AUTOR ||--o{ LIBRO_AUTOR : escribe
    SOCIO ||--o{ PRESTAMO : realiza
    EJEMPLAR ||--o{ PRESTAMO : participa_en
    SEDE ||--o{ PRESTAMO : origen
    SEDE ||--o{ PRESTAMO : destino
    PRESTAMO ||--o| MULTA : genera
    SOCIO ||--o{ MULTA : posee
    PRESTAMO ||--o| REMITO : genera
    SOCIO ||--o{ RESERVA : solicita
    LIBRO ||--o{ RESERVA : reservado_en
    SEDE ||--o{ RESERVA : radicada_en
```

---

## 4. Diagrama de Clases UML (Dominio y Patrones de Diseño)

```mermaid
classDiagram
    class Sede {
        +int id
        +str direccion
        +str contacto
        +str horarios
        +str estado
    }

    class Socio {
        +int id
        +str numero_socio
        +str documento
        +str nombre
        +str apellido
        +str email
        +str telefono
        +date fecha_alta
        +int activo
    }

    class Autor {
        +int id
        +str nombre
        +str apellido
        +str nacionalidad
    }

    class Libro {
        +int id
        +str isbn
        +str titulo
        +str editorial
        +int anio
    }

    class Ejemplar {
        +int id
        +str codigo_inventario
        +str estado_fisico
        +int libro_id
        +int sede_id
    }

    class Prestamo {
        +int id
        +date fecha_prestamo
        +date fecha_devolucion_estimada
        +date fecha_devolucion_real
        +str estado
        +int socio_id
        +int ejemplar_id
        +int sede_origen_id
        +int sede_destino_id
    }

    class Multa {
        +int id
        +float monto
        +str estado
        +date fecha_emision
        +int prestamo_id
        +int socio_id
    }

    class Remito {
        +int id
        +str codigo_remito
        +str estado
        +date fecha_emision
        +int prestamo_id
    }

    class Reserva {
        +int id
        +datetime fecha_reserva
        +str estado
        +int socio_id
        +int libro_id
        +int sede_id
    }

    %% Patrón State (Ciclo de vida del Remito)
    class RemitoContexto {
        +Remito remito
        +EstadoRemito estado_actual
        +avanzar()
        +reportar_incidencia()
    }

    class EstadoRemito {
        <<abstract>>
        +siguiente(contexto)*
        +obtener_nombre()*
        +reportar_incidencia(contexto)
    }

    class EstadoEmpaquetado {
        +siguiente(contexto)
        +obtener_nombre()
    }
    class EstadoDespachado {
        +siguiente(contexto)
        +reportar_incidencia(contexto)
        +obtener_nombre()
    }
    class EstadoRecibido {
        +siguiente(contexto)
        +obtener_nombre()
    }
    class EstadoConIncidencias {
        +siguiente(contexto)
        +obtener_nombre()
    }

    %% Patrón Strategy (Cálculo de Multas)
    class MultaService {
        +EstrategiaMulta estrategia
        +cambiar_estrategia(nueva_estrategia)
        +generar_multa(prestamo, tipo)
    }

    class EstrategiaMulta {
        <<abstract>>
        +calcular_multa(dias_retraso)* float
    }
    class MultaEstandar {
        +calcular_multa(dias_retraso) float
    }
    class MultaReducidaEstudiante {
        +calcular_multa(dias_retraso) float
    }
    class SinMultaPromocional {
        +calcular_multa(dias_retraso) float
    }

    %% Patrón Observer (Notificación de Reservas)
    class Subject {
        -List~Observer~ _observers
        +attach(observer)
        +detach(observer)
        +notify()
    }
    class DisponibilidadEjemplarSubject {
        +str codigo_inventario
        +str titulo_libro
        +cambiar_estado(nuevo_estado)
    }
    class Observer {
        <<abstract>>
        +update()*
    }
    class SocioObserver {
        +str nombre
        +str email
        +update()
    }

    %% Relaciones de Dominio
    Libro "*" -- "*" Autor
    Libro "1" -- "*" Ejemplar
    Sede "1" -- "*" Ejemplar
    Socio "1" -- "*" Prestamo
    Ejemplar "1" -- "*" Prestamo
    Prestamo "1" -- "0..1" Multa
    Socio "1" -- "*" Multa
    Prestamo "1" -- "0..1" Remito
    Socio "1" -- "*" Reserva
    Libro "1" -- "*" Reserva
    Sede "1" -- "*" Reserva

    %% Relaciones Patrones
    RemitoContexto --> Remito
    RemitoContexto o-- EstadoRemito
    EstadoRemito <|-- EstadoEmpaquetado
    EstadoRemito <|-- EstadoDespachado
    EstadoRemito <|-- EstadoRecibido
    EstadoRemito <|-- EstadoConIncidencias

    MultaService o-- EstrategiaMulta
    EstrategiaMulta <|-- MultaEstandar
    EstrategiaMulta <|-- MultaReducidaEstudiante
    EstrategiaMulta <|-- SinMultaPromocional

    Subject <|-- DisponibilidadEjemplarSubject
    Subject o-- Observer
    Observer <|-- SocioObserver
```
