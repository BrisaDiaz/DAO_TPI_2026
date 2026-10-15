# Alcance del Sistema

## 1. Gestión de Sedes

* **Alta de Sede**: Registrar una nueva sede en la red indicando dirección, datos de contacto, horarios y estado inicial.
* **Baja de Sede**: Dar de baja lógica o física una sede existente en el sistema.
* **Modificación de Sede**: Actualizar los datos de una sede (dirección, contacto, horarios o estado activo).
* **Consulta de Sede**: Retornar el listado completo de sedes registradas en la red o buscar una sede en particular para verificar su estado actual.

## 2. Gestión de Socios

* **Alta de Socio**: Registrar un nuevo socio en el sistema con sus datos personales y número identificatorio.
* **Baja de Socio**: Eliminar o dar de baja a un socio del sistema.
* **Modificación de Socio**: Actualizar la información del socio o gestionar su estado de habilitación/inhabilitación.
* **Consulta de Socio**: Retornar el listado completo de socios registrados y verificar su estado actual (activo/inhabilitado) para el control de préstamos.

## 3. Gestión de Catálogo de Libros y Autores

* **Alta de Libro y Autor**: Registrar nuevos libros en el catálogo general, asociando sus autores, editorial, año e ISBN.
* **Baja de Libro**: Dar de baja registros obsoletos o libros del catálogo.
* **Modificación de Libro**: Actualizar la información o los datos de los libros del catálogo.
* **Consulta de Libro**: Retornar el listado completo de libros y autores disponibles en el sistema o consultar su información general.

## 4. Gestión de Ejemplares Físicos

* **Alta de Ejemplar**: Registrar nuevas unidades físicas de los libros, indicando de forma obligatoria la sede a la que pertenecen.
* **Baja de Ejemplar**: Dar de baja un ejemplar físico del inventario.
* **Modificación de Ejemplar**: Modificar el estado físico o la ubicación de un ejemplar.
* **Consulta de Ejemplar**: Retornar el listado completo de ejemplares o consultar la disponibilidad de ejemplares detallada por sede.

## 5. Gestión de Préstamos

* **Alta de Préstamo (Local e Interbibliotecario)**: Registrar un nuevo préstamo de un ejemplar (localmente o indicando sede origen y sede destino).
* **Baja de Préstamo**: Eliminar o anular el registro de un préstamo de forma excepcional.
* **Modificación de Préstamo**: Actualizar los datos de un préstamo activo (como fechas o estados de devolución).
* **Consulta de Préstamo**: Retornar el listado completo de préstamos, así como consultar préstamos activos, vencidos, material en tránsito o el historial por socio.

## 6. Gestión de Multas y Sanciones

* **Alta de Multa**: Registrar y generar una multa por retraso en la devolución de un préstamo.
* **Baja de Multa**: Anular o eliminar un registro de multa de forma excepcional.
* **Modificación de Multa**: Registrar el pago, condonación o actualización del estado de una multa para regularizar la habilitación del socio.
* **Consulta de Multa**: Retornar el listado completo de multas o consultar el estado de deudas pendientes por socio.

## 7. Gestión Logística y Trazabilidad de Remitos

* **Alta de Remito**: Generar y emitir un nuevo remito asignado a un traslado interbibliotecario de ejemplares.
* **Baja de Remito**: Eliminar un registro de remito en caso de error administrativo.
* **Modificación de Remito**: Actualizar el estado del remito a lo largo de su trayecto (empaquetado, despachado, recibido o con incidencias).
* **Consulta de Remito**: Retornar el listado completo de remitos y permitir la trazabilidad de los mismos a lo largo de su trayecto.

## 8. Gestión de Reservas

* **Alta de Reserva**: Registrar y generar una nueva reserva de material solicitada por un socio.
* **Baja / Cancelar Reserva**: Cancelar o eliminar una reserva existente según las reglas de negocio.
* **Modificación de Reserva**: Actualizar el estado o los detalles de una reserva pendiente.
* **Consulta de Reserva**: Retornar el listado completo de reservas y su estado actual en el sistema.

## 9. Generación de Reportes

* **Consulta de Reporte de Préstamos y Tránsito**: Retornar el listado completo de préstamos activos y material en tránsito.
* **Consulta de Reporte de Vencimientos y Multas**: Retornar el listado de préstamos vencidos junto con sus multas acumuladas.
* **Consulta de Reporte de Demanda Inter-sedes**: Retornar el listado de los libros más solicitados para préstamos entre distintas sedes.
* **Consulta de Reporte de Disponibilidad**: Retornar el estado y disponibilidad del catálogo detallada por cada sede.
* **Consulta de Reporte de Logística e Incidencias**: Listar la tasa de envíos logísticos exitosos y las incidencias reportadas.
* **Consulta de Reporte de Movimiento de Ejemplares**: Retornar el flujo de envíos por sede origen/destino y el tiempo promedio de tránsito.