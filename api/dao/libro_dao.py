"""DAO para las entidades Libro y Autor."""
from typing import List
from sqlalchemy.orm import Session

from api.dao.base_dao import BaseDAO
from api.models import Libro, Autor


class LibroDAO(BaseDAO[Libro]):

    def __init__(self, session: Session):
        super().__init__(session, Libro)

    def obtener_por_isbn(self, isbn: str) -> Libro | None:
        """Busca un libro por su ISBN único."""
        return self.session.query(Libro).filter(Libro.isbn == isbn).first()

    def buscar_por_titulo(self, titulo: str) -> List[Libro]:
        """Busca libros cuyo título contenga el texto indicado."""
        return self.session.query(Libro).filter(
            Libro.titulo.ilike(f"%{titulo}%")
        ).all()

    def agregar_autor(self, libro: Libro, autor: Autor) -> None:
        """Asocia un autor a un libro (relación N:M)."""
        if autor not in libro.autores:
            libro.autores.append(autor)
            self.session.commit()


class AutorDAO(BaseDAO[Autor]):

    def __init__(self, session: Session):
        super().__init__(session, Autor)

    def buscar_por_apellido(self, apellido: str) -> List[Autor]:
        """Busca autores cuyo apellido contenga el texto indicado."""
        return self.session.query(Autor).filter(
            Autor.apellido.ilike(f"%{apellido}%")
        ).all()
