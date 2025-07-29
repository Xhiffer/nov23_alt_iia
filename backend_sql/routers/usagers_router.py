import logging
import os
import subprocess
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import controllers.usagers_controller as usager_ctrl

from schemas.usagers_schema import UsagerCreate, UsagerRead

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/usagers/csv-to-sql/")
async def import_csv():
    try:
        logging.info("Starting usagers img-to-csv import process...")
        script_path = os.path.join("scripts", "csv_to_sql", "usagers_csv_to_sql.py")
        subprocess.Popen(["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("Usagers img-to-csv import process started successfully.")
        return {"message": "Usagers img-to-csv import started successfully!"}
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

@router.get("/usagers/{usager_id}", response_model=UsagerRead)
def get_usager(usager_id: int, db: Session = Depends(get_db)):
    usager = usager_ctrl.get_usager(db, usager_id)
    if not usager:
        raise HTTPException(status_code=404, detail="Usager not found")
    return usager

from typing import List

@router.get("/usagers", response_model=List[UsagerRead])
def get_all_usagers(db: Session = Depends(get_db)):
    return usager_ctrl.get_all_usagers(db)

@router.post("/usagers/", response_model=UsagerRead)
def create_usager(
    usager_data: UsagerCreate,
    db: Session = Depends(get_db),
):
    return usager_ctrl.create_usager(usager_data, db)


@router.put("/usagers/{usager_id}", response_model=UsagerRead)
def update_usager(
    usager_id: int,
    usager_data: UsagerCreate,
    db: Session = Depends(get_db),
):
    return usager_ctrl.update_usager(usager_id, usager_data, db)

@router.delete("/usagers/{usager_id}")
def delete_usager(usager_id: int, db: Session = Depends(get_db)):
    return usager_ctrl.delete_usager(db, usager_id)