from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import exc

from models.caract_model import Caract
from database import SessionLocal
from schemas.caract_schema import CaractCreate, CaractRead
from typing import List

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# GET: Retrieve Caract by ID
def get_caract(db: Session, caract_id: int) -> CaractRead:
    caract = db.query(Caract).filter(Caract.id == caract_id).first()
    if caract is None:
        raise HTTPException(status_code=404, detail="Caract not found")
    return caract

def get_all_caracts(db: Session) -> List[CaractRead]:
    caracts = db.query(Caract).all()
    return caracts

# POST: Create new Caract
def create_caract(caract_data: CaractCreate, db: Session) -> CaractRead:
    caract = Caract(**caract_data.model_dump())
    db.add(caract)
    db.commit()
    db.refresh(caract)
    return caract

# PUT: Update existing Caract
def update_caract(caract_id: int, caract_data: CaractCreate, db: Session) -> CaractRead:
    caract = db.query(Caract).filter(Caract.id == caract_id).first()
    if caract is None:
        raise HTTPException(status_code=404, detail="Caract not found")

    update_data = caract_data.model_dump()
    for key, value in update_data.items():
        setattr(caract, key, value)

    try:
        db.commit()
        db.refresh(caract)
        return caract
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Caract: {str(e)}")

# DELETE: Delete Caract by ID
def delete_caract(db: Session, caract_id: int):
    caract = db.query(Caract).filter(Caract.id == caract_id).first()
    if caract is None:
        raise HTTPException(status_code=404, detail="Caract not found")

    try:
        db.delete(caract)
        db.commit()
        return {"detail": "Caract deleted successfully"}
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Caract: {str(e)}")
