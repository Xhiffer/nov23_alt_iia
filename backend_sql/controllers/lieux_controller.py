from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import exc

from models.lieux_model import Lieu
from database import SessionLocal
from schemas.lieux_schema import LieuCreate, LieuRead
from typing import List

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# GET: Retrieve Lieu by ID
def get_lieu(db: Session, lieu_id: int) -> LieuRead:
    lieu = db.query(Lieu).filter(Lieu.id == lieu_id).first()
    if lieu is None:
        raise HTTPException(status_code=404, detail="Lieu not found")
    return lieu

def get_all_lieux(db: Session) -> List[LieuRead]:
    lieux = db.query(Lieu).all()
    return lieux

# POST: Create new Lieu
def create_lieu(lieu_data: LieuCreate, db: Session) -> LieuRead:
    lieu = Lieu(**lieu_data.model_dump())
    db.add(lieu)
    db.commit()
    db.refresh(lieu)
    return lieu

# PUT: Update existing Lieu
def update_lieu(lieu_id: int, lieu_data: LieuCreate, db: Session) -> LieuRead:
    lieu = db.query(Lieu).filter(Lieu.id == lieu_id).first()
    if lieu is None:
        raise HTTPException(status_code=404, detail="Lieu not found")

    update_data = lieu_data.model_dump()
    for key, value in update_data.items():
        setattr(lieu, key, value)

    try:
        db.commit()
        db.refresh(lieu)
        return lieu
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Lieu: {str(e)}")

# DELETE: Delete Lieu by ID
def delete_lieu(db: Session, lieu_id: int):
    lieu = db.query(Lieu).filter(Lieu.id == lieu_id).first()
    if lieu is None:
        raise HTTPException(status_code=404, detail="Lieu not found")

    try:
        db.delete(lieu)
        db.commit()
        return {"detail": "Lieu deleted successfully"}
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Lieu: {str(e)}")
