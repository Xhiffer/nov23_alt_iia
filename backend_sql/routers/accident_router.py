import logging
import os
import subprocess
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import SessionLocal
import controllers.accident_controller as accident_ctrl
from schemas.accident_schema import AccidentCreate, AccidentRead

router = APIRouter()

# Dependency pour récupérer la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import CSV vers SQL (facultatif)
@router.post("/accidents/csv-to-sql/")
async def import_csv():
    try:
        logging.info("Starting accidents csv-to-sql import process...")
        script_path = os.path.join("scripts", "csv_to_sql", "accident_csv_to_sql.py")
        subprocess.Popen(["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("Accidents csv-to-sql import process started successfully.")
        return {"message": "Accidents csv-to-sql import started successfully!"}
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

# GET: Un accident par ID
@router.get("/accidents/{accident_id}", response_model=AccidentRead)
def get_accident(accident_id: int, db: Session = Depends(get_db)):
    accident = accident_ctrl.get_accident(db, accident_id)
    if not accident:
        raise HTTPException(status_code=404, detail="Accident not found")
    return accident

# GET: Tous les accidents
@router.get("/accidents", response_model=List[AccidentRead])
def get_all_accidents(db: Session = Depends(get_db)):
    return accident_ctrl.get_all_accidents(db)

# POST: Création d’un accident
@router.post("/accidents/", response_model=AccidentRead)
def create_accident(accident_data: AccidentCreate, db: Session = Depends(get_db)):
    return accident_ctrl.create_accident(accident_data, db)

# PUT: Modification d’un accident
@router.put("/accidents/{accident_id}", response_model=AccidentRead)
def update_accident(accident_id: int, accident_data: AccidentCreate, db: Session = Depends(get_db)):
    return accident_ctrl.update_accident(accident_id, accident_data, db)

# DELETE: Suppression d’un accident
@router.delete("/accidents/{accident_id}")
def delete_accident(accident_id: int, db: Session = Depends(get_db)):
    return accident_ctrl.delete_accident(db, accident_id)
