from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import exc
import os
import uuid

from models.resultat_ai_model import ResultatAi
from database import SessionLocal
from schemas.resultat_ai_schema import ResultatAiCreate, ResultatAiRead
from models.gravites_tags import GraviteTag
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
def save_video_to_disk(video_bytes: bytes, folder: str = "videos") -> str:
    os.makedirs(folder, exist_ok=True)
    filename = f"video_{uuid.uuid4().hex}.mp4"  # or any suitable extension
    filepath = os.path.join(folder, filename)
    with open(filepath, "wb") as f:
        f.write(video_bytes)
    return filepath

def create_resultat_ai(resultat_ai_data: ResultatAiCreate, db: Session, video_bytes: bytes = None) -> ResultatAiRead:
    gravite_tag_id = None

    if resultat_ai_data.gravite_estimee:
        tag = db.query(GraviteTag).filter(
            GraviteTag.label.ilike(resultat_ai_data.gravite_estimee.strip())
        ).first()
        if not tag:
            raise HTTPException(status_code=400, detail=f"Gravité inconnue: {resultat_ai_data.gravite_estimee}")
        gravite_tag_id = tag.id

    # Save the video file if provided and get path
    video_path = None
    if video_bytes:
        video_path = save_video_to_disk(video_bytes)

    # Prepare dict for DB model
    data_dict = resultat_ai_data.model_dump(exclude={"gravite_estimee"})
    data_dict["gravite_tag_id"] = gravite_tag_id
    if video_path:
        data_dict["video_path"] = video_path

    resultat_ai = ResultatAi(**data_dict)
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
    
    
def get_paginated(db: Session, offset: int = 0, limit: int = 10):

    return db.query(ResultatAi).offset(offset).limit(limit).all()

def count_all(db: Session):
    return db.query(ResultatAi).count()
