# Reportes

## Reporte 1: Préstamos Activos y Material en Tránsito

* **Objetivo de Gestión:** Permite al personal de la red de bibliotecas visualizar de manera centralizada qué material se encuentra actualmente prestado de forma local y cuál se encuentra en traslado logístico entre sedes, ayudando a controlar el inventario fuera de las estanterías.
* **Consulta SQL / Lógica de Base de Datos:**
```sql
SELECT 
    P.id AS id_prestamo,
    L.titulo AS titulo_libro,
    E.codigo_inventario,
    SO.direccion AS sede_origen,
    SD.direccion AS sede_destino,
    CASE WHEN P.sede_origen_id = P.sede_destino_id THEN 'Local' ELSE 'Interbibliotecario' END AS tipo_prestamo,
    CONCAT(S.nombre, ' ', S.apellido) AS socio_nombre,
    P.fecha_prestamo,
    COALESCE(R.estado, 'Activo (Sin Tránsito)') AS estado_logistico
FROM PRESTAMO P
JOIN EJEMPLAR E ON P.ejemplar_id = E.id
JOIN LIBRO L ON E.libro_id = L.id
JOIN SOCIO S ON P.socio_id = S.id
JOIN SEDE SO ON P.sede_origen_id = SO.id
LEFT JOIN SEDE SD ON P.sede_destino_id = SD.id
LEFT JOIN REMITO R ON P.id = R.prestamo_id
WHERE P.estado = 'Activo';

```


* **Formato Visual Tabular:**

| ID Préstamo | Título del Libro | Código Ejemplar | Sede Origen | Sede Destino | Tipo | Socio | Fecha Préstamo | Estado Logístico |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **105** | Arquitectura de Software | EJ-402 | Sede Centro | Sede Centro | Local | Juan Pérez | 2026-06-01 | Activo (Sin Tránsito) |
| **108** | Base de Datos Avanzada | EJ-115 | Sede Norte | Sede Sur | Interbib. | María Gómez | 2026-06-03 | Empaquetado |

---

## Reporte 2: Préstamos Vencidos y Multas Acumuladas

* **Objetivo de Gestión:** Identificar de forma inmediata a los socios que mantienen retrasos en la devolución de material y calcular el impacto económico de las multas acumuladas para proceder con las suspensiones o regularizaciones pertinentes.
* **Consulta SQL / Lógica de Base de Datos:**
```sql
SELECT 
    S.numero_socio,
    CONCAT(S.nombre, ' ', S.apellido) AS socio_nombre,
    S.email,
    L.titulo AS titulo_libro,
    P.fecha_devolucion_estimada,
    DATEDIFF(CURRENT_DATE, P.fecha_devolucion_estimada) AS dias_retraso,
    (DATEDIFF(CURRENT_DATE, P.fecha_devolucion_estimada) * 150.0) AS multa_acumulada,
    CASE WHEN S.activo = 0 THEN 'Inhabilitado (Deuda)' ELSE 'Activo' END AS estado_cuenta
FROM PRESTAMO P
JOIN SOCIO S ON P.socio_id = S.id
JOIN EJEMPLAR E ON P.ejemplar_id = E.id
JOIN LIBRO L ON E.libro_id = L.id
WHERE P.estado = 'Activo' AND P.fecha_devolucion_estimada < CURRENT_DATE;

```


* **Formato Visual Tabular:**

| Nro. Socio | Socio | Email | Título del Libro | F. Est. Devolución | Días Retraso | Multa Acumulada | Estado Cuenta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **SOC-042** | Carlos Ruiz | cruiz@mail.com | Redes de Computadoras | 2026-05-20 | 25 dias | $3.750,00 | Inhabilitado (Deuda) |
| **SOC-089** | Ana Torres | atorres@mail.com | Sistemas Operativos | 2026-05-28 | 17 dias | $2.550,00 | Inhabilitado (Deuda) |

---

## Reporte 3: Libros Más Solicitados para Préstamos Inter-sedes

* **Objetivo de Gestión:** Analizar la demanda de títulos a nivel global de la red para optimizar la distribución del inventario físico, identificando qué libros requieren mayor rotación o la adquisición de ejemplares adicionales en sedes específicas.
* **Consulta SQL / Lógica de Base de Datos (Con Agregación y Ranking):**
```sql
SELECT 
    L.isbn,
    L.titulo,
    COUNT(P.id) AS total_solicitudes_intersedes
FROM PRESTAMO P
JOIN EJEMPLAR E ON P.ejemplar_id = E.id
JOIN LIBRO L ON E.libro_id = L.id
WHERE P.sede_origen_id <> P.sede_destino_id
GROUP BY L.isbn, L.titulo
HAVING COUNT(P.id) > 0
ORDER BY total_solicitudes_intersedes DESC;

```


* **Formato Visual Tabular:**

| Ranking | ISBN | Título del Libro | Total Solicitudes Inter-sedes | Sede Mayor Demanda Destino |
| --- | --- | --- | --- | --- |
| **1** | 978-987-123-456-7 | Ingeniería de Software Aplicada | **14** | Sede Sur |
| **2** | 978-950-555-789-2 | Programación Orientada a Objetos | **9** | Sede Este |

---

## Reporte 4: Disponibilidad de Catálogo por Sede

* **Objetivo de Gestión:** Proveer al personal y a los usuarios una radiografía clara del inventario físico disponible discriminado sucursal por sucursal, facilitando la consulta de disponibilidad antes de generar una reserva o un préstamo interbibliotecario.
* **Consulta SQL / Lógica de Base de Datos (Con Cruces y Agregación):**
```sql
SELECT 
    SE.direccion AS sede,
    L.isbn,
    L.titulo,
    COUNT(E.id) AS ejemplares_totales,
    SUM(CASE WHEN E.estado_fisico = 'Disponible' THEN 1 ELSE 0 END) AS ejemplares_disponibles,
    SUM(CASE WHEN E.estado_fisico <> 'Disponible' THEN 1 ELSE 0 END) AS ejemplares_no_disponibles
FROM SEde SE
JOIN EJEMPLAR E ON SE.id = E.sede_id
JOIN LIBRO L ON E.libro_id = L.id
WHERE SE.estado = 'activo'
GROUP BY SE.id, SE.direccion, L.isbn, L.titulo;

```


* **Formato Visual Tabular:**

| Sede | ISBN | Título del Libro | Ejemplares Totales | Ejemplares Disponibles | Ejemplares No Disponibles |
| --- | --- | --- | --- | --- | --- |
| **Sede Centro** | 978-987-111-222-3 | Algoritmos y Estructuras | 5 | **4** | 1 |
| **Sede Norte** | 978-987-111-222-3 | Algoritmos y Estructuras | 3 | **0** | 3 |