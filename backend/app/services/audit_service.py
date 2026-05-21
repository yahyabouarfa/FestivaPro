from sqlalchemy.orm import Session

from app.models.domain import AuditLog, User


def record_audit(db: Session, *, user: User | None, action: str, entity: str, entity_id: int | None = None, metadata: dict | None = None) -> AuditLog:
    audit = AuditLog(user_id=user.id if user else None, action=action, entity=entity, entity_id=entity_id, metadata_json=metadata)
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit
