from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.domain import User
from app.repositories.crud import CRUDRepository
from app.services.audit_service import record_audit


class DomainService:
    def __init__(self, entity_name: str, repository: CRUDRepository) -> None:
        self.entity_name = entity_name
        self.repository = repository

    def list(self, db: Session, *, offset: int, limit: int) -> list:
        return self.repository.list(db, offset=offset, limit=min(limit, 250))

    def get_or_404(self, db: Session, item_id: int):
        item = self.repository.get(db, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{self.entity_name} not found")
        return item

    def create(self, db: Session, payload: BaseModel, user: User):
        item = self.repository.create(db, payload.model_dump(exclude_unset=True))
        record_audit(db, user=user, action="create", entity=self.entity_name, entity_id=item.id)
        return item

    def update(self, db: Session, item_id: int, payload: BaseModel, user: User):
        item = self.get_or_404(db, item_id)
        update_data = payload.model_dump(exclude_unset=True)
        item = self.repository.update(db, item, update_data)
        record_audit(db, user=user, action="update", entity=self.entity_name, entity_id=item.id, metadata=update_data)
        return item

    def delete(self, db: Session, item_id: int, user: User) -> None:
        item = self.get_or_404(db, item_id)
        self.repository.delete(db, item)
        record_audit(db, user=user, action="delete", entity=self.entity_name, entity_id=item_id)
