import logging
import os
import subprocess
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
import controllers.lieux_controller as lieux_ctrl
from schemas.lieux_schema import LieuCreate, LieuRead

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/lieux/csv-to-sql/")
async def import_csv():
    try:
        logging.info("Starting lieux csv-to-sql import process...")
        script_path = os.path.join("scripts", "csv_to_sql", "lieux_csv_to_sql.py")
        subprocess.Popen(["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("Lieux csv-to-sql import process started successfully.")
        return {"message": "Lieux csv-to-sql import started successfully!"}
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}


@router.get("/lieux/{lieu_id}", response_model=LieuRead)
def get_lieu(lieu_id: int, db: Session = Depends(get_db)):
    lieu = lieux_ctrl.get_lieu(db, lieu_id)
    if not lieu:
        raise HTTPException(status_code=404, detail="Lieu not found")
    return lieu


@router.post("/lieux/", response_model=LieuRead)
def create_lieu(
    lieu_data: LieuCreate,
    db: Session = Depends(get_db),
):
    return lieux_ctrl.create_lieu(lieu_data, db)


@router.put("/lieux/{lieu_id}", response_model=LieuRead)
def update_lieu(
    lieu_id: int,
    lieu_data: LieuCreate,
    db: Session = Depends(get_db),
):
    return lieux_ctrl.update_lieu(lieu_id, lieu_data, db)


@router.delete("/lieux/{lieu_id}")
def delete_lieu(lieu_id: int, db: Session = Depends(get_db)):
    return lieux_ctrl.delete_lieu(db, lieu_id)
