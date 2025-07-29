from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import exc

from models.vehicules_model import Vehicule
from database import SessionLocal
from schemas.vehicules_schema import VehiculeCreate, VehiculeRead
from typing import List

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# GET: Retrieve Vehicule by ID
def get_vehicule(db: Session, vehicule_id: int) -> VehiculeRead:
    vehicule = db.query(Vehicule).filter(Vehicule.id == vehicule_id).first()
    if vehicule is None:
        raise HTTPException(status_code=404, detail="Vehicule not found")
    return vehicule

def get_all_vehicules(db: Session) -> List[VehiculeRead]:
    vehicules = db.query(Vehicule).all()
    return vehicules

# POST: Create new Vehicule
def create_vehicule(
    vehicule_data: VehiculeCreate,
    db: Session,
) -> VehiculeRead:
    vehicule = Vehicule(**vehicule_data.model_dump())
    db.add(vehicule)
    db.commit()
    db.refresh(vehicule)
    return vehicule


def update_vehicule(
    vehicule_id: int,
    vehicule_data: VehiculeCreate,
    db: Session  # remove Depends here if you want same signature as create_vehicule
) -> VehiculeRead:
    vehicule = db.query(Vehicule).filter(Vehicule.id == vehicule_id).first()
    if vehicule is None:
        raise HTTPException(status_code=404, detail="Vehicule not found")

    # Update all attributes from vehicule_data
    update_data = vehicule_data.model_dump()
    for key, value in update_data.items():
        setattr(vehicule, key, value)

    try:
        db.commit()
        db.refresh(vehicule)
        return vehicule
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Vehicule: {str(e)}")
    

# DELETE: Delete Vehicule by ID
def delete_vehicule(db: Session, vehicule_id: int):
    vehicule = db.query(Vehicule).filter(Vehicule.id == vehicule_id).first()
    if vehicule is None:
        raise HTTPException(status_code=404, detail="Vehicule not found")

    try:
        db.delete(vehicule)
        db.commit()
        return {"detail": "Vehicule deleted successfully"}
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Vehicule: {str(e)}")

