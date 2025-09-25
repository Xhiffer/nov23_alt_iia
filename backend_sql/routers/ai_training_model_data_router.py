import logging
import os
import subprocess
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import SessionLocal
import controllers.ai_training_model_data_controller as ai_ctrl
from schemas.ai_training_model_data_schema import (
    AITrainingModelDataCreate,
    AITrainingModelDataRead,
)

router = APIRouter()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Example CSV import endpoint (similar to lieux)
@router.post("/ai-training-data/csv-to-sql/")
async def import_csv():
    try:
        logging.info("Starting AITrainingModelData csv-to-sql import process...")
        script_path = os.path.join("scripts", "csv_to_sql", "ai_training_model_data_csv_to_sql.py")
        subprocess.Popen(["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("AITrainingModelData csv-to-sql import process started successfully.")
        return {"message": "AITrainingModelData csv-to-sql import started successfully!"}
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}


# GET one by ID
@router.get("/ai-training-data/{record_id}", response_model=AITrainingModelDataRead)
def get_ai_training_data(record_id: int, db: Session = Depends(get_db)):
    record = ai_ctrl.get_ai_training_data(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="AITrainingModelData not found")
    return record


# GET all
@router.get("/ai-training-data", response_model=List[AITrainingModelDataRead])
def get_all_ai_training_data(db: Session = Depends(get_db)):
    return ai_ctrl.get_all_ai_training_data(db)


# POST create
@router.post("/ai-training-data/", response_model=AITrainingModelDataRead)
def create_ai_training_data(
    record_data: AITrainingModelDataCreate,
    db: Session = Depends(get_db),
):
    return ai_ctrl.create_ai_training_data(record_data, db)


# PUT update
@router.put("/ai-training-data/{record_id}", response_model=AITrainingModelDataRead)
def update_ai_training_data(
    record_id: int,
    record_data: AITrainingModelDataCreate,
    db: Session = Depends(get_db),
):
    return ai_ctrl.update_ai_training_data(record_id, record_data, db)


# DELETE
@router.delete("/ai-training-data/{record_id}")
def delete_ai_training_data(record_id: int, db: Session = Depends(get_db)):
    return ai_ctrl.delete_ai_training_data(db, record_id)
