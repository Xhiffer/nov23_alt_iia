import logging
import os
import subprocess
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
import controllers.caract_controller as caract_ctrl
from schemas.caract_schema import CaractCreate, CaractRead

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/caracts/csv-to-sql/")
async def import_csv():
    try:
        logging.info("Starting caracts csv-to-sql import process...")
        script_path = os.path.join("scripts", "csv_to_sql", "caract_csv_to_sql.py")
        subprocess.Popen(["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("Caracts csv-to-sql import process started successfully.")
        return {"message": "Caracts csv-to-sql import started successfully!"}
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}


@router.get("/caracts/{caract_id}", response_model=CaractRead)
def get_caract(caract_id: int, db: Session = Depends(get_db)):
    caract = caract_ctrl.get_caract(db, caract_id)
    if not caract:
        raise HTTPException(status_code=404, detail="Caract not found")
    return caract


@router.post("/caracts/", response_model=CaractRead)
def create_caract(
    caract_data: CaractCreate,
    db: Session = Depends(get_db),
):
    return caract_ctrl.create_caract(caract_data, db)


@router.put("/caracts/{caract_id}", response_model=CaractRead)
def update_caract(
    caract_id: int,
    caract_data: CaractCreate,
    db: Session = Depends(get_db),
):
    return caract_ctrl.update_caract(caract_id, caract_data, db)


@router.delete("/caracts/{caract_id}")
def delete_caract(caract_id: int, db: Session = Depends(get_db)):
    return caract_ctrl.delete_caract(db, caract_id)
