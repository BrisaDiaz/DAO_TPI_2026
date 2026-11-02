"""
Modelos ORM (SQLAlchemy 2.0) - Todas las entidades del sistema de bibliotecas.

Entidades: Sede, Socio, Autor, Libro, Ejemplar, Prestamo, Multa, Remito, Reserva.
Tabla intermedia: libro_autor (relación N:M entre Libro y Autor).
"""
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import (String, Integer, Float, Date, DateTime,
                        ForeignKey, Table, Column, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


# ─────────────────────────────────────────────────────────────────────────────
# Tabla intermedia: Libro <-> Autor (Relación N:M)
# ─────────────────────────────────────────────────────────────────────────────
libro_autor = Table(
    "libro_autor",
    Base.metadata,
    Column("libro_id", Integer, ForeignKey("libros.id"), primary_key=True),
    Column("autor_id", Integer, ForeignKey("autores.id"), primary_key=True),
)


# ─────────────────────────────────────────────────────────────────────────────
# Sede
# ─────────────────────────────────────────────────────────────────────────────
class Sede(Base):
    __tablename__ = "sedes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    direccion: Mapped[str] = mapped_column(String(200), nullable=False)
    contacto: Mapped[str] = mapped_column(String(100), nullable=False)
    horarios: Mapped[str] = mapped_column(String(200), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="activo")  # activo / baja

    # Relaciones
    ejemplares: Mapped[List["Ejemplar"]] = relationship(back_populates="sede")
    prestamos_origen: Mapped[List["Prestamo"]] = relationship(
        back_populates="sede_origen", foreign_keys="Prestamo.sede_origen_id"
    )
    prestamos_destino: Mapped[List["Prestamo"]] = relationship(
        back_populates="sede_destino", foreign_keys="Prestamo.sede_destino_id"
    )

    def __repr__(self) -> str:
        return f"<Sede(id={self.id}, direccion='{self.direccion}', estado='{self.estado}')>"


# ─────────────────────────────────────────────────────────────────────────────
# Socio
# ─────────────────────────────────────────────────────────────────────────────
class Socio(Base):
    __tablename__ = "socios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    numero_socio: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    documento: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    fecha_alta: Mapped[date] = mapped_column(Date, default=date.today)
    activo: Mapped[int] = mapped_column(Integer, default=1)  # 1=activo, 0=inhabilitado

    # Relaciones
    prestamos: Mapped[List["Prestamo"]] = relationship(back_populates="socio")
    multas: Mapped[List["Multa"]] = relationship(back_populates="socio")
    reservas: Mapped[List["Reserva"]] = relationship(back_populates="socio")

    def __repr__(self) -> str:
        return f"<Socio(id={self.id}, numero_socio='{self.numero_socio}', nombre='{self.nombre} {self.apellido}')>"


# ─────────────────────────────────────────────────────────────────────────────
# Autor
# ─────────────────────────────────────────────────────────────────────────────
class Autor(Base):
    __tablename__ = "autores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    nacionalidad: Mapped[str] = mapped_column(String(80), nullable=False)

    # Relación N:M con Libro
    libros: Mapped[List["Libro"]] = relationship(
        secondary=libro_autor, back_populates="autores"
    )

    def __repr__(self) -> str:
        return f"<Autor(id={self.id}, nombre='{self.nombre} {self.apellido}')>"


# ─────────────────────────────────────────────────────────────────────────────
# Libro (Catálogo general)
# ─────────────────────────────────────────────────────────────────────────────
class Libro(Base):
    __tablename__ = "libros"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    isbn: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    titulo: Mapped[str] = mapped_column(String(250), nullable=False)
    editorial: Mapped[str] = mapped_column(String(150), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relación N:M con Autor
    autores: Mapped[List["Autor"]] = relationship(
        secondary=libro_autor, back_populates="libros"
    )
    # Relación 1:N con Ejemplar
    ejemplares: Mapped[List["Ejemplar"]] = relationship(back_populates="libro")
    # Relación 1:N con Reserva
    reservas: Mapped[List["Reserva"]] = relationship(back_populates="libro")

    def __repr__(self) -> str:
        return f"<Libro(id={self.id}, isbn='{self.isbn}', titulo='{self.titulo}')>"


# ─────────────────────────────────────────────────────────────────────────────
# Ejemplar (Unidades físicas distribuidas por sede)
# ─────────────────────────────────────────────────────────────────────────────
class Ejemplar(Base):
    __tablename__ = "ejemplares"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo_inventario: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True
    )
    estado_fisico: Mapped[str] = mapped_column(
        String(30), default="Disponible"
    )  # Disponible, Prestado, Dañado, Extraviado

    # Claves foráneas
    libro_id: Mapped[int] = mapped_column(ForeignKey("libros.id"), nullable=False)
    sede_id: Mapped[int] = mapped_column(ForeignKey("sedes.id"), nullable=False)

    # Relaciones
    libro: Mapped["Libro"] = relationship(back_populates="ejemplares")
    sede: Mapped["Sede"] = relationship(back_populates="ejemplares")
    prestamos: Mapped[List["Prestamo"]] = relationship(back_populates="ejemplar")

    def __repr__(self) -> str:
        return f"<Ejemplar(id={self.id}, codigo='{self.codigo_inventario}', estado='{self.estado_fisico}')>"


# ─────────────────────────────────────────────────────────────────────────────
# Préstamo (Locales e interbibliotecarios)
# ─────────────────────────────────────────────────────────────────────────────
class Prestamo(Base):
    __tablename__ = "prestamos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha_prestamo: Mapped[date] = mapped_column(Date, default=date.today)
    fecha_devolucion_estimada: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_devolucion_real: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    estado: Mapped[str] = mapped_column(
        String(20), default="Activo"
    )  # Activo, Devuelto, Vencido

    # Claves foráneas
    socio_id: Mapped[int] = mapped_column(ForeignKey("socios.id"), nullable=False)
    ejemplar_id: Mapped[int] = mapped_column(ForeignKey("ejemplares.id"), nullable=False)
    sede_origen_id: Mapped[int] = mapped_column(ForeignKey("sedes.id"), nullable=False)
    sede_destino_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sedes.id"), nullable=True
    )  # NULL = préstamo local | valor = interbibliotecario

    # Relaciones
    socio: Mapped["Socio"] = relationship(back_populates="prestamos")
    ejemplar: Mapped["Ejemplar"] = relationship(back_populates="prestamos")
    sede_origen: Mapped["Sede"] = relationship(
        back_populates="prestamos_origen", foreign_keys=[sede_origen_id]
    )
    sede_destino: Mapped[Optional["Sede"]] = relationship(
        back_populates="prestamos_destino", foreign_keys=[sede_destino_id]
    )
    multa: Mapped[Optional["Multa"]] = relationship(
        back_populates="prestamo", uselist=False
    )
    remito: Mapped[Optional["Remito"]] = relationship(
        back_populates="prestamo", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Prestamo(id={self.id}, estado='{self.estado}', socio_id={self.socio_id})>"


# ─────────────────────────────────────────────────────────────────────────────
# Multa (Sanciones por retrasos en devolución)
# ─────────────────────────────────────────────────────────────────────────────
class Multa(Base):
    __tablename__ = "multas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    monto: Mapped[float] = mapped_column(Float, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20), default="Pendiente"
    )  # Pendiente, Pagada, Condonada
    fecha_emision: Mapped[date] = mapped_column(Date, default=date.today)

    # Claves foráneas
    prestamo_id: Mapped[int] = mapped_column(ForeignKey("prestamos.id"), nullable=False)
    socio_id: Mapped[int] = mapped_column(ForeignKey("socios.id"), nullable=False)

    # Relaciones
    prestamo: Mapped["Prestamo"] = relationship(back_populates="multa")
    socio: Mapped["Socio"] = relationship(back_populates="multas")

    def __repr__(self) -> str:
        return f"<Multa(id={self.id}, monto={self.monto}, estado='{self.estado}')>"


# ─────────────────────────────────────────────────────────────────────────────
# Remito (Trazabilidad logística de traslados interbibliotecarios)
# ─────────────────────────────────────────────────────────────────────────────
class Remito(Base):
    __tablename__ = "remitos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo_remito: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(30), default="Empaquetado"
    )  # Empaquetado, Despachado, Recibido, Con incidencias
    fecha_emision: Mapped[date] = mapped_column(Date, default=date.today)

    # Clave foránea
    prestamo_id: Mapped[int] = mapped_column(ForeignKey("prestamos.id"), nullable=False)

    # Relación
    prestamo: Mapped["Prestamo"] = relationship(back_populates="remito")

    def __repr__(self) -> str:
        return f"<Remito(id={self.id}, codigo='{self.codigo_remito}', estado='{self.estado}')>"


# ─────────────────────────────────────────────────────────────────────────────
# Reserva
# ─────────────────────────────────────────────────────────────────────────────
class Reserva(Base):
    __tablename__ = "reservas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha_reserva: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    # Se completa al notificar la disponibilidad del material: inicia el plazo de SUP-05
    fecha_notificacion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estado: Mapped[str] = mapped_column(
        String(20), default="Pendiente"
    )  # Pendiente, Concretada, Cancelada, Caducada

    # Claves foráneas
    socio_id: Mapped[int] = mapped_column(ForeignKey("socios.id"), nullable=False)
    libro_id: Mapped[int] = mapped_column(ForeignKey("libros.id"), nullable=False)
    sede_id: Mapped[int] = mapped_column(ForeignKey("sedes.id"), nullable=False)

    # Relaciones
    socio: Mapped["Socio"] = relationship(back_populates="reservas")
    libro: Mapped["Libro"] = relationship(back_populates="reservas")
    sede: Mapped["Sede"] = relationship()

    def __repr__(self) -> str:
        return f"<Reserva(id={self.id}, estado='{self.estado}', socio_id={self.socio_id}, sede_id={self.sede_id})>"
