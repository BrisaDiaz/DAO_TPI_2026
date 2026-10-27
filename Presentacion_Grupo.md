# Trabajo Práctico Integrador — Documento de Referencia de Desarrollo

---

## 1. Grupo

| Campo | Detalle |
|---|---|
| **Número de grupo:** | *(Completar número de grupo)* |
| **Tema:** | **Tema 1 — Biblioteca: Sistema de Préstamos Interbibliotecarios** |

### Integrantes

| Legajo | Nombre y Apellido |
|---|---|
| 400042 | Enzo Valentino Cardelli |
| *(Completar)* | Brisa Abigaíl Díaz |
| 87917 | Augusto Bossi |
| *(Completar)* | *(Integrante 4)* |

---

## 2. Propuesta

### 2.1. Objetivos del Sistema

#### Objetivo General
Desarrollar un sistema de escritorio orientado a objetos para la administración centralizada y logística de una **Red de Bibliotecas Públicas**, que permita gestionar múltiples sedes, el catálogo general de obras y sus ejemplares físicos distribuidos, el padrón de socios, los préstamos locales e interbibliotecarios con trazabilidad de remitos en tránsito, el control de reservas y la aplicación automatizada de multas y notificaciones.

#### Objetivos Específicos
1. **Centralizar el inventario bibliográfico multisede:** Registrar obras, autores (relación $N:M$) y ejemplares físicos identificando de forma unívoca su código de inventario, estado físico y sede de pertenencia.
2. **Garantizar la trazabilidad de préstamos interbibliotecarios:** Controlar el ciclo de vida completo de los traslados de ejemplares entre sedes mediante la emisión de remitos y la gestión de sus estados (`Empaquetado`, `Despachado`, `Recibido` y `Con incidencias`) aplicando el patrón de diseño **State**.
3. **Automatizar el control de vencimientos y sanciones:** Calcular multas por mora al momento de la devolución utilizando políticas tarifarias intercambiables mediante el patrón **Strategy**, aplicando además cargos automáticos por deterioro o extravío e inhabilitando preventivamente a los socios con deuda.
4. **Gestionar reservas y notificaciones desacopladas:** Permitir la reserva de obras sin stock disponible en una sede y notificar automáticamente a los socios en lista de espera cuando un ejemplar vuelve a estar disponible mediante el patrón **Observer**.
5. **Brindar información analítica para la toma de decisiones:** Proveer reportes no triviales en tiempo real sobre préstamos activos y en tránsito, morosidad acumulada, ranking de demanda inter-sedes y disponibilidad de catálogo por sucursal.

---

### 2.2. Alcances del Sistema

#### Procesos de Negocio Obligatorios Cubiertos
1. **Administración de Sedes:** Alta, baja lógica, modificación y consulta de sedes de la red (dirección, contacto, horarios y estado `activo` / `baja`).
2. **Administración de Socios:** ABMC completo de socios con control de unicidad (DNI y número de socio) y estado de habilitación (`activo` / `inhabilitado`).
3. **Administración de Catálogo y Ejemplares Físicos:** Gestión de libros (ISBN único), autores asociados y unidades físicas vinculadas a su sede de radicación.
4. **Registro de Solicitudes de Préstamo (Local e Interbibliotecario):** Validación preventiva de disponibilidad del ejemplar (RN-01), habilitación del socio (RN-02), pertenencia de sede en préstamos locales (RN-03), estado activo de sedes origen/destino (RN-04) y límite máximo de 3 préstamos activos simultáneos (SUP-04).
5. **Logística de Remitos (Empaquetar, Despachar y Recibir):** Emisión automática de remito en préstamos interbibliotecarios y trazabilidad de transiciones de estado mediante el patrón **State**, incluyendo reporte y resolución de incidencias en tránsito.
6. **Consulta de Disponibilidad:** Búsqueda y filtrado en vivo de ejemplares por sede, obra y estado físico.
7. **Gestión de Reservas:** Registro de reservas sobre obras con stock disponible igual a cero en la sede solicitada (SUP-06), cancelación manual y procesamiento de caducidad automática a las 48 horas (SUP-05).
8. **Registro de Devoluciones y Estado Físico:** Recepción del ejemplar (exigiendo remito `Recibido` en préstamos interbibliotecarios, SUP-03), actualización del estado físico (`Disponible`, `Dañado`, `Extraviado`), generación automática de multas por mora con el patrón **Strategy** (SUP-01) o cargos por daño/extravío (SUP-07), y disparo automático del patrón **Observer** cuando el ejemplar queda disponible.

#### Procesos Opcionales Incorporados
* **Envío de notificaciones automáticas (Patrón Observer):** Aviso automático a todos los socios con reserva pendiente cuando se devuelve un ejemplar en estado `Disponible`.
* **Inventario con códigos únicos:** Identificación individual de ejemplares (`codigo_inventario`) y remitos (`codigo_remito`).
* **Revisión de estado de recepción de ejemplares:** Control de devoluciones con daño o extravío y aplicación automática de cargo por reposición.

#### Reportes No Triviales Implementados
1. **Préstamos Activos y Material en Tránsito:** Cruce entre préstamos, ejemplares, libros, socios, sedes de origen/destino y estado logístico del remito.
2. **Préstamos Vencidos y Multas Acumuladas:** Detalle de préstamos con mora, cálculo de días de retraso, multas registradas/estimadas y causa.
3. **Libros Más Solicitados para Préstamos Inter-sedes:** Ranking agrupado por obra con conteo de solicitudes interbibliotecarias.
4. **Disponibilidad de Catálogo por Sede:** Totales de ejemplares por sucursal activa discriminando unidades disponibles y no disponibles.

---

### 2.3. DER y Diagrama de Clases UML

#### A. Diagrama Entidad-Relación (DER)

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

#### B. Diagrama de Clases UML (Modelo de Dominio y Patrones State, Strategy y Observer)

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

    %% Patrón State
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
    class EstadoEmpaquetado
    class EstadoDespachado
    class EstadoRecibido
    class EstadoConIncidencias

    %% Patrón Strategy
    class MultaService {
        +EstrategiaMulta estrategia
        +cambiar_estrategia(nueva_estrategia)
        +generar_multa(prestamo, tipo)
    }
    class EstrategiaMulta {
        <<abstract>>
        +calcular_multa(dias_retraso)* float
    }
    class MultaEstandar
    class MultaReducidaEstudiante
    class SinMultaPromocional

    %% Patrón Observer
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
