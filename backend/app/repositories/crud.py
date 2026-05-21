from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class CRUDRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    def list(self, db: Session, *, offset: int = 0, limit: int = 100) -> list[ModelT]:
        return list(db.scalars(select(self.model).offset(offset).limit(limit)).all())

    def get(self, db: Session, item_id: int) -> ModelT | None:
        return db.get(self.model, item_id)

    def create(self, db: Session, data: dict) -> ModelT:
        item = self.model(**data)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def update(self, db: Session, item: ModelT, data: dict) -> ModelT:
        for key, value in data.items():
            setattr(item, key, value)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def delete(self, db: Session, item: ModelT) -> None:
        db.delete(item)
        db.commit()
