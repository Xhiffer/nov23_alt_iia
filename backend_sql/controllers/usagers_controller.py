from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import exc

from models.usagers_model import Usager
from database import SessionLocal
from schemas.usagers_schema import UsagerCreate, UsagerRead
from typing import List

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# GET: Retrieve Usager by ID
def get_usager(db: Session, usager_id: int) -> UsagerRead:
    usager = db.query(Usager).filter(Usager.id == usager_id).first()
    if usager is None:
        raise HTTPException(status_code=404, detail="Usager not found")
    return usager

def get_all_usagers(db: Session) -> List[UsagerRead]:
    usagers = db.query(Usager).all()
    return usagers

# POST: Create new Usager
def create_usager(usager_data: UsagerCreate, db: Session) -> UsagerRead:
    usager = Usager(**usager_data.model_dump())
    db.add(usager)
    db.commit()
    db.refresh(usager)
    return usager

# PUT: Update existing Usager
def update_usager(usager_id: int, usager_data: UsagerCreate, db: Session) -> UsagerRead:
    usager = db.query(Usager).filter(Usager.id == usager_id).first()
    if usager is None:
        raise HTTPException(status_code=404, detail="Usager not found")

    update_data = usager_data.model_dump()
    for key, value in update_data.items():
        setattr(usager, key, value)

    try:
        db.commit()
        db.refresh(usager)
        return usager
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Usager: {str(e)}")

# DELETE: Delete Usager by ID
def delete_usager(db: Session, usager_id: int):
    usager = db.query(Usager).filter(Usager.id == usager_id).first()
    if usager is None:
        raise HTTPException(status_code=404, detail="Usager not found")

    try:
        db.delete(usager)
        db.commit()
        return {"detail": "Usager deleted successfully"}
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Usager: {str(e)}")
