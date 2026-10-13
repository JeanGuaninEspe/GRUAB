"""
Clase base y utilidades para la capa de repositorios.
"""
from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy.orm import Session
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get_by_id(self, db: Session, id_val: Any) -> Optional[ModelType]:
        return db.get(self.model, id_val)

    def list_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()
