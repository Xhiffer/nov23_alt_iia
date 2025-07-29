import logging
import os
import subprocess
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import controllers.vehicules_controller as vehicule_ctrl
from schemas.vehicules_schema import VehiculeCreate, VehiculeRead
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/vehicules/csv-to-sql/")
async def import_csv():
    try:
        logging.info("Starting img-to-csv import process...")
        script_path = os.path.join("scripts","csv_to_sql", "vehicules_csv_to_sql.py")
        subprocess.Popen(["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("img-to-csv import process started successfully.")
        return {"message": "img-to-csv import started successfully!"}
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

@router.get("/vehicules/{vehicule_id}", response_model=VehiculeRead)
def get_vehicule(vehicule_id: int, db: Session = Depends(get_db)):
    vehicule = vehicule_ctrl.get_vehicule(db, vehicule_id)
    if not vehicule:
        raise HTTPException(status_code=404, detail="Vehicule not found")
    return vehicule

from typing import List

@router.get("/vehicules", response_model=List[VehiculeRead])
def get_all_vehicules(db: Session = Depends(get_db)):
    return vehicule_ctrl.get_all_vehicules(db)

@router.post("/vehicules/", response_model=VehiculeRead)
def create_vehicule(
    vehicule_data: VehiculeCreate,
    db: Session = Depends(get_db),
):
    return vehicule_ctrl.create_vehicule(vehicule_data, db)  # pass Pydantic first, DB second



@router.put("/vehicules/{vehicule_id}", response_model=VehiculeRead)
def update_vehicule(
    vehicule_id: int,
    vehicule_data: VehiculeCreate,
    db: Session = Depends(get_db),
):
    return vehicule_ctrl.update_vehicule(vehicule_id, vehicule_data, db)


@router.delete("/vehicules/{vehicule_id}")
def delete_vehicule(vehicule_id: int, db: Session = Depends(get_db)):
    return vehicule_ctrl.delete_vehicule(db, vehicule_id)

