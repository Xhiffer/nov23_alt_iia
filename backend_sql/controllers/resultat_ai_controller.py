from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import exc

from models.resultat_ai_model import ResultatAi
from database import SessionLocal
from schemas.resultat_ai_schema import ResultatAiCreate, ResultatAiRead

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# GET: Retrieve ResultatAi by ID
def get_resultat_ai(db: Session, resultat_ai_id: int) -> ResultatAiRead:
    resultat_ai = db.query(ResultatAi).filter(ResultatAi.id == resultat_ai_id).first()
    if resultat_ai is None:
        raise HTTPException(status_code=404, detail="Resultat AI not found")
    return resultat_ai

# POST: Create new ResultatAi
def create_resultat_ai(resultat_ai_data: ResultatAiCreate, db: Session) -> ResultatAiRead:
    resultat_ai = ResultatAi(**resultat_ai_data.model_dump())
    db.add(resultat_ai)
    db.commit()
    db.refresh(resultat_ai)
    return resultat_ai

# PUT: Update existing ResultatAi
def update_resultat_ai(resultat_ai_id: int, resultat_ai_data: ResultatAiCreate, db: Session) -> ResultatAiRead:
    resultat_ai = db.query(ResultatAi).filter(ResultatAi.id == resultat_ai_id).first()
    if resultat_ai is None:
        raise HTTPException(status_code=404, detail="Resultat AI not found")

    update_data = resultat_ai_data.model_dump()
    for key, value in update_data.items():
        setattr(resultat_ai, key, value)

    try:
        db.commit()
        db.refresh(resultat_ai)
        return resultat_ai
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Resultat AI: {str(e)}")

# DELETE: Delete ResultatAi by ID
def delete_resultat_ai(db: Session, resultat_ai_id: int):
    resultat_ai = db.query(ResultatAi).filter(ResultatAi.id == resultat_ai_id).first()
    if resultat_ai is None:
        raise HTTPException(status_code=404, detail="Resultat AI not found")

    try:
        db.delete(resultat_ai)
        db.commit()
        return {"detail": "Resultat AI deleted successfully"}
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Resultat AI: {str(e)}")
