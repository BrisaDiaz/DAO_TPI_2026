# Patrones de Diseño

## 1. Patrón State (Estado)

### Justificación y Motivación en el Dominio

Se exige evaluar críticamente el **ciclo de vida del remito y sus estados** a lo largo de su trayecto interbibliotecario (`Empaquetado`, `Despachado`, `Recibido`, con incidencias). Utilizar estructuras condicionales (`if/elif/else`) para controlar las transiciones de un remito o de un préstamo resulta frágil y dificulta el mantenimiento.
Aplicando el patrón **State**, cada estado del remito se modela como una clase independiente que encapsula el comportamiento permitido. Como se indica en la teoría de la cátedra, el cliente le pide al contexto que avance (`siguiente()`), pero es el propio estado actual quien decide y ejecuta la transición invocando el cambio sobre el contexto.

### Ejemplo de Implementación en Python (Ciclo de Vida del Remito)

```python
from abc import ABC, abstractmethod

# Contexto
class Remito:
    def __init__(self, codigo_remito: str):
        self.codigo_remito = codigo_remito
        self.estado = EstadoEmpaquetado()  # Estado inicial

    def cambiar_estado(self, nuevo_estado):
        self.estado = nuevo_estado

    def avanzar(self):
        self.estado.siguiente(self)

    def obtener_descripcion_estado(self) -> str:
        return self.estado.obtener_nombre()

# Interfaz State
class EstadoRemito(ABC):
    @abstractmethod
    def siguiente(self, remito: Remito):
        pass

    @abstractmethod
    def obtener_nombre(self) -> str:
        pass

# Estados Concretos
class EstadoEmpaquetado(EstadoRemito):
    def siguiente(self, remito: Remito):
        print(f"Remito {remito.codigo_remito}: Empaquetado -> Despachando hacia sede destino...")
        remito.cambiar_estado(EstadoDespachado())

    def obtener_nombre(self) -> str:
        return "Empaquetado"

class EstadoDespachado(EstadoRemito):
    def siguiente(self, remito: Remito):
        print(f"Remito {remito.codigo_remito}: En tránsito -> Recibido en sede destino.")
        remito.cambiar_estado(EstadoRecibido())

    def obtener_nombre(self) -> str:
        return "Despachado"

class EstadoRecibido(EstadoRemito):
    def siguiente(self, remito: Remito):
        print(f"El remito {remito.codigo_remito} ya se encuentra recibido. No hay más transiciones.")

    def obtener_nombre(self) -> str:
        return "Recibido"

# --- Demostración de uso ---
if __name__ == "__main__":
    remito_inter = Remito("REM-2026-001")
    print(f"Estado inicial: {remito_inter.obtener_descripcion_estado()}")
    
    remito_inter.avanzar()  # Pasa a Despachado
    print(f"Estado actual: {remito_inter.obtener_descripcion_estado()}")
    
    remito_inter.avanzar()  # Pasa a Recibido
    print(f"Estado final: {remito_inter.obtener_descripcion_estado()}")

```

---

## 2. Patrón Strategy (Estrategia)

### Justificación y Motivación en el Dominio

El sistema de bibliotecas contempla reglas de negocio asociadas al cálculo de multas por retrasos en devoluciones o políticas de préstamos diferenciadas (por ejemplo, tarifas fijas por día de mora, multas escalonadas según la antigüedad del socio o exenciones).
El patrón **Strategy** permite definir una familia de algoritmos intercambiables encapsulados en clases separadas, permitiendo que el contexto (`CalculadoraMulta`) delegue el cálculo sin conocer los detalles de implementación y permitiendo seleccionar la estrategia en tiempo de ejecución (incluso mediante diccionarios de funciones como muestra la cátedra).

### Ejemplo de Implementación en Python (Cálculo de Multas por Retraso)

```python
from abc import ABC, abstractmethod

# Interfaz Strategy
class EstrategiaMulta(ABC):
    @abstractmethod
    def calcular_multa(self, dias_retraso: int) -> float:
        pass

# Estrategias Concretas
class MultaEstandar(EstrategiaMulta):
    def calcular_multa(self, dias_retraso: int) -> float:
        tarifa_diaria = 150.0
        return dias_retraso * tarifa_diaria

class MultaReducidaEstudiante(EstrategiaMulta):
    def calcular_multa(self, dias_retraso: int) -> float:
        tarifa_reducida = 75.0
        return dias_retraso * tarifa_reducida

class SinMultaPromocional(EstrategiaMulta):
    def calcular_multa(self, dias_retraso: int) -> float:
        return 0.0

# Contexto
class CalculadoraMulta:
    def __init__(self, estrategia: EstrategiaMulta):
        self.estrategia = estrategia

    def cambiar_estrategia(self, nueva_estrategia: EstrategiaMulta):
        self.estrategia = nueva_estrategia

    def calcular(self, dias_retraso: int) -> float:
        return self.estrategia.calcular_multa(dias_retraso)

# --- Demostración de uso (incluyendo diccionario de estrategias alineado a la cátedra) ---
if __name__ == "__main__":
    # Uso clásico con objetos
    calc = CalculadoraMulta(MultaEstandar())
    print(f"Multa estándar (5 días de retraso): ${calc.calcular(5)}")

    calc.cambiar_estrategia(MultaReducidaEstudiante())
    print(f"Multa estudiante (5 días de retraso): ${calc.calcular(5)}")

    # Uso avanzado mediante diccionario de estrategias (según ejemplo de cátedra)
    estrategias_dict = {
        'estandar': MultaEstandar(),
        'estudiante': MultaReducidaEstudiante(),
        'gratis': SinMultaPromocional()
    }
    
    tipo_socio = 'estudiante'
    costo = estrategias_dict[tipo_socio].calcular_multa(4)
    print(f"Multa usando diccionario para socio '{tipo_socio}' (4 días): ${costo}")

```
---

## 3. Patrón Iterator (Iterador)

### Justificación y Motivación en el Dominio

En una red de bibliotecas es común tener que recorrer colecciones complejas y anidadas, como por ejemplo **recorrer todos los ejemplares físicos de una red distribuidos en múltiples sedes**, o filtrar colecciones específicas (como listar secuencialmente únicamente los préstamos vencidos de un socio o los libros de un autor sin exponer la estructura interna de almacenamiento de las listas).
El patrón **Iterator** permite acceder secuencialmente a los elementos de una colección agregada sin exponer su representación subyacente (listas, tuplas o diccionarios).

### Ejemplo de Implementación en Python (Iterador de Ejemplares por Sede)

```python
class Ejemplar:
    def __init__(self, codigo: str, estado: str):
        self.codigo = codigo
        self.estado = estado

class SedeInventario:
    def __init__(self, nombre_sede: str):
        self.nombre_sede = nombre_sede
        self._ejemplares = []

    def agregar_ejemplar(self, ejemplar: Ejemplar):
        self._ejemplares.append(ejemplar)

    # Implementación del patrón Iterator nativo de Python (__iter__)
    def __iter__(self):
        return IteradorEjemplaresDisponibles(self._ejemplares)

class IteradorEjemplaresDisponibles:
    def __init__(self, ejemplares):
        self._ejemplares = [e for e in ejemplares if e.estado == "Disponible"]
        self._indice = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._indice < len(self._ejemplares):
            ejemplar = self._ejemplares[self._indice]
            self._indice += 1
            return ejemplar
        raise StopIteration

# --- Demostración de uso ---
if __name__ == "__main__":
    sede_central = SedeInventario("Sede Centro")
    sede_central.agregar_ejemplar(Ejemplar("EJ-001", "Disponible"))
    sede_central.agregar_ejemplar(Ejemplar("EJ-002", "Préstamo"))
    sede_central.agregar_ejemplar(Ejemplar("EJ-003", "Disponible"))

    print(f"Ejemplares disponibles en {sede_central.nombre_sede}:")
    for ej in sede_central:
        print(f" - Código: {ej.codigo}")

```

---

## 4. Patrón Singleton (Instancia Única)

### Justificación y Motivación en el Dominio

Componentes críticos del sistema como la **Caché de Configuración Global de la Red** (por ejemplo, parámetros generales del sistema, feriados o reglas de préstamo de la red) o un **Gestor de Conexión a Base de Datos / Pool de Conexiones** deben garantizar una única instancia en toda la ejecución para evitar duplicidad de memoria y asegurar la consistencia de los datos globales.

### Ejemplo de Implementación en Python (Configuración de la Red de Bibliotecas)

```python
class ConfiguracionRedBibliotecas:
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super(ConfiguracionRedBibliotecas, cls).__new__(cls)
            # Inicialización única de variables globales de la red
            cls._instancia.dias_maximos_prestamo = 15
            cls._instancia.multa_diaria_base = 150.0
            cls._instancia.nombre_red = "Red Provincial de Bibliotecas Públicas"
        return cls._instancia

# --- Demostración de uso ---
if __name__ == "__main__":
    config1 = ConfiguracionRedBibliotecas()
    config2 = ConfiguracionRedBibliotecas()

    print(f"Nombre de la Red (config1): {config1.nombre_red}")
    print(f"¿Son la misma instancia?: {config1 is config2}")
    
    # Modificar desde una referencia afecta a todo el sistema
    config2.dias_maximos_prestamo = 20
    print(f"Días máximos actualizados (config1): {config1.dias_maximos_prestamo}")

```

---

## 5. Patrón Factory (Fábrica)

### Justificación y Motivación en el Dominio

El sistema contempla la generación de **múltiples reportes no triviales** (préstamos activos, vencidos y multas, demanda inter-sedes, disponibilidad, etc.) o la creación de distintos tipos de **Notificaciones** (Email, SMS, Impresión).
El patrón **Factory** centraliza la lógica de creación de objetos complejos, permitiendo que el cliente solicite una instancia pasando un parámetro (tipo de reporte o canal de notificación) sin acoplarse a las clases concretas.

### Ejemplo de Implementación en Python (Fábrica de Reportes)

```python
from abc import ABC, abstractmethod

# Interfaz del Producto
class Reporte(ABC):
    @abstractmethod
    def generar(self) -> str:
        pass

# Productos Concretos
class ReportePrestamosVencidos(Reporte):
    def generar(self) -> str:
        return "Generando reporte de préstamos vencidos y multas acumuladas..."

class ReporteDisponibilidadSede(Reporte):
    def generar(self) -> str:
        return "Generando reporte de disponibilidad de catálogo por sede..."

# Fábrica (Factory)
class ReporteFactory:
    @staticmethod
    def crear_reporte(tipo: str) -> Reporte:
        if tipo == "vencidos":
            return ReportePrestamosVencidos()
        elif tipo == "disponibilidad":
            return ReporteDisponibilidadSede()
        else:
            raise ValueError(f"Tipo de reporte desconocido: {tipo}")

# --- Demostración de uso ---
if __name__ == "__main__":
    tipo_solicitado = "vencidos"
    reporte = ReporteFactory.crear_reporte(tipo_solicitado)
    print(reporte.generar())

```

---

## 6. Patrón Observer (Observador)

### Justificación y Motivación en el Dominio

En el proceso opcional de **Gestión de Reservas y Notificaciones**, cuando un ejemplar físico es devuelto o cambia su estado a "Disponible", el sistema debe notificar automáticamente a los socios que se encontraban en lista de espera (`Reserva`).
Mediante el patrón **Observer**, el `Ejemplar` (sujeto observable) mantiene una lista de socios subscritos (`Observadores`) y les notifica de manera automática ante un cambio de estado sin acoplar la lógica de negocio de los préstamos con el sistema de mensajería.

### Ejemplo de Implementación en Python (Aviso de Disponibilidad de Material)

```python
from abc import ABC, abstractmethod

# Interfaz Observer
class ObservadorSocio(ABC):
    @abstractmethod
    def actualizar(self, mensaje: str):
        pass

# Observador Concreto (Socio)
class SocioObserver(ObservadorSocio):
    def __init__(self, nombre: str, email: str):
        self.nombre = nombre
        self.email = email

    def actualizar(self, mensaje: str):
        print(f"Notificación enviada a {self.nombre} ({self.email}): {mensaje}")

# Sujeto Observable (Ejemplar / Reserva)
class EjemplarObservable:
    def __init__(self, codigo: str, titulo_libro: str):
        self.codigo = codigo
        self.titulo_libro = titulo_libro
        self._observadores = []
        self._estado = "Prestado"

    def agregar_observador(self, observador: ObservadorSocio):
        self._observadores.append(observador)

    def quitar_observador(self, observador: ObservadorSocio):
        self._observadores.remove(observador)

    def notificar_observadores(self, mensaje: str):
        for obs in self._observadores:
            obs.actualizar(mensaje)

    def cambiar_estado(self, nuevo_estado: str):
        self._estado = nuevo_estado
        if self._estado == "Disponible":
            self.notificar_observadores(f"El libro '{self.titulo_libro}' (Ejemplar: {self.codigo}) ya se encuentra disponible para retiro.")

# --- Demostración de uso ---
if __name__ == "__main__":
    # Sujeto
    ejemplar = EjemplarObservable("EJ-999", "Arquitectura de Software")

    # Suscriptores (Socios en lista de espera)
    socio1 = SocioObserver("Ana Gómez", "ana@mail.com")
    socio2 = SocioObserver("Carlos Ruiz", "carlos@mail.com")

    ejemplar.agregar_observador(socio1)
    ejemplar.agregar_observador(socio2)

    print("--- Al registrarse la devolución del ejemplar ---")
    ejemplar.cambiar_estado("Disponible")

```