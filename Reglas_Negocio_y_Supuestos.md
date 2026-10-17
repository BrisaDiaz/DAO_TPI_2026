# Reglas de Negocio y Supuestos del Sistema

## 1. Validaciones de Negocio Obligatorias (Reglas de Validación)
* **RN-01 (Disponibilidad de Ejemplar):** El sistema validará que el estado físico del ejemplar sea "Disponible" antes de autorizar cualquier préstamo o reserva.
* **RN-02 (Habilitación del Socio):** El sistema bloqueará de forma automática cualquier intento de préstamo si el socio posee multas pendientes de pago o préstamos vencidos sin devolver.
* **RN-03 (Pertenencia de Sede):** Un préstamo local sólo puede efectuarse utilizando ejemplares físicos asignados a la misma sede donde se procesa la solicitud.
* **RN-04 (Restricción de Sedes dadas de baja):** El sistema denegará operaciones de préstamo, reserva o despacho logístico si la sede de origen o destino se encuentra con estado "Baja".
* **RN-05 (Unicidad de Registros):** Se validará la no duplicidad de socios (por documento), libros del catálogo (por ISBN) y ejemplares físicos (por código de inventario único).

## 2. Supuestos del Dominio
* **SUP-01 (Cálculo de Multas):** Las multas se generan automáticamente al registrar la devolución de un préstamo cuya fecha real supere a la fecha estimada de devolución, aplicando una tarifa diaria configurable.
* **SUP-02 (Trazabilidad Logística):** Todo traslado interbibliotecario requiere de manera obligatoria la emisión de un remito cuyo ciclo de vida avanza mediante los estados: *Empaquetado -> Despachado -> Recibido*.
* **SUP-03 (Restricción de Devolución Interbibliotecaria):** No se podrá registrar la devolución de un préstamo interbibliotecario hasta que el remito asociado se encuentre con estado "Recibido", garantizando así la trazabilidad y recepción física del ejemplar en la sede correspondiente.