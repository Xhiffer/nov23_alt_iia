from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import exc
from typing import List

from models.accident_model import Accident
from database import SessionLocal
from schemas.accident_schema import AccidentCreate, AccidentRead

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# GET: Retrieve Accident by ID
def get_accident(db: Session, accident_id: int) -> AccidentRead:
    accident = db.query(Accident).filter(Accident.id == accident_id).first()
    if accident is None:
        raise HTTPException(status_code=404, detail="Accident not found")
    return accident

# GET: Retrieve all Accidents
def get_all_accidents(db: Session) -> List[AccidentRead]:
    return db.query(Accident).all()

# POST: Create new Accident
def create_accident(accident_data: AccidentCreate, db: Session) -> AccidentRead:
    accident = Accident(**accident_data.model_dump())
    db.add(accident)
    db.commit()
    db.refresh(accident)
    return accident

# PUT: Update existing Accident
def update_accident(accident_id: int, accident_data: AccidentCreate, db: Session) -> AccidentRead:
    accident = db.query(Accident).filter(Accident.id == accident_id).first()
    if accident is None:
        raise HTTPException(status_code=404, detail="Accident not found")

    update_data = accident_data.model_dump()
    for key, value in update_data.items():
        setattr(accident, key, value)

    try:
        db.commit()
        db.refresh(accident)
        return accident
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Accident: {str(e)}")

# DELETE: Delete Accident by ID
def delete_accident(db: Session, accident_id: int):
    accident = db.query(Accident).filter(Accident.id == accident_id).first()
    if accident is None:
        raise HTTPException(status_code=404, detail="Accident not found")

    try:
        db.delete(accident)
        db.commit()
        return {"detail": "Accident deleted successfully"}
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Accident: {str(e)}")
