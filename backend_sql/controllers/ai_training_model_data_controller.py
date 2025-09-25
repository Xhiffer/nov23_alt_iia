from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import exc
from typing import List

from models.ai_training_model_data_model import AITrainingModelData
from database import SessionLocal
from schemas.ai_training_model_data_schema import (
    AITrainingModelDataCreate,
    AITrainingModelDataRead,
)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# GET: Retrieve record by ID
def get_ai_training_data(db: Session, record_id: int) -> AITrainingModelDataRead:
    record = db.query(AITrainingModelData).filter(AITrainingModelData.id == record_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="AITrainingModelData not found")
    return record


# GET: Retrieve all records
def get_all_ai_training_data(db: Session) -> List[AITrainingModelDataRead]:
    return db.query(AITrainingModelData).all()


# POST: Create new record
def create_ai_training_data(
    record_data: AITrainingModelDataCreate, db: Session
) -> AITrainingModelDataRead:
    record = AITrainingModelData(**record_data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# PUT: Update existing record
def update_ai_training_data(
    record_id: int, record_data: AITrainingModelDataCreate, db: Session
) -> AITrainingModelDataRead:
    record = db.query(AITrainingModelData).filter(AITrainingModelData.id == record_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="AITrainingModelData not found")

    update_data = record_data.model_dump()
    for key, value in update_data.items():
        setattr(record, key, value)

    try:
        db.commit()
        db.refresh(record)
        return record
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating AITrainingModelData: {str(e)}")


# DELETE: Delete record by ID
def delete_ai_training_data(db: Session, record_id: int):
    record = db.query(AITrainingModelData).filter(AITrainingModelData.id == record_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="AITrainingModelData not found")

    try:
        db.delete(record)
        db.commit()
        return {"detail": "AITrainingModelData deleted successfully"}
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting AITrainingModelData: {str(e)}")
