from datetime import datetime
from sqlalchemy.orm import Session

from src.db.models import Class, ClassSession


# PUBLIC_INTERFACE
def create_class(db: Session, title: str, description: str | None, capacity: int) -> Class:
    """Create a class type."""
    c = Class(title=title, description=description, capacity=capacity)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# PUBLIC_INTERFACE
def update_class(db: Session, class_id: int, **fields) -> Class:
    """Update a class type."""
    c = db.query(Class).get(class_id)
    if not c:
        raise ValueError("Class not found")
    for k, v in fields.items():
        if v is not None:
            setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


# PUBLIC_INTERFACE
def delete_class(db: Session, class_id: int) -> None:
    """Delete a class type."""
    c = db.query(Class).get(class_id)
    if not c:
        raise ValueError("Class not found")
    db.delete(c)
    db.commit()


# PUBLIC_INTERFACE
def list_classes(db: Session) -> list[Class]:
    """List all classes."""
    return db.query(Class).all()


# PUBLIC_INTERFACE
def create_session(db: Session, class_id: int, start_time: datetime, end_time: datetime, capacity: int) -> ClassSession:
    """Create a session with provided capacity and spots_remaining initialized."""
    if end_time <= start_time:
        raise ValueError("end_time must be after start_time")
    c = db.query(Class).get(class_id)
    if not c:
        raise ValueError("Class not found")
    s = ClassSession(class_id=class_id, start_time=start_time, end_time=end_time, capacity=capacity, spots_remaining=capacity)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# PUBLIC_INTERFACE
def list_sessions(db: Session, class_id: int | None = None) -> list[ClassSession]:
    """List class sessions optionally filtered by class_id."""
    q = db.query(ClassSession)
    if class_id:
        q = q.filter(ClassSession.class_id == class_id)
    return q.order_by(ClassSession.start_time.asc()).all()
