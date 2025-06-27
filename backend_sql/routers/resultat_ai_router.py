from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import SessionLocal
import controllers.resultat_ai_controller as resultat_ai_ctrl
from schemas.resultat_ai_schema import ResultatAiCreate, ResultatAiRead
import json
from typing import Optional

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/resultat_ai/{resultat_ai_id}", response_model=ResultatAiRead)
def get_resultat_ai(resultat_ai_id: int, db: Session = Depends(get_db)):
    resultat_ai = resultat_ai_ctrl.get_resultat_ai(db, resultat_ai_id)
    if not resultat_ai:
        raise HTTPException(status_code=404, detail="Resultat AI not found")
    return resultat_ai

@router.post("/resultat_ai/", response_model=ResultatAiCreate)
async def create_resultat_ai(
    video: UploadFile = File(...),
    resultat_ai_data: str = Form(...),  # JSON string of your ResultatAiCreate data without video
    db: Session = Depends(get_db)
):
    # Parse JSON string into your Pydantic model (excluding video)
    data_dict = json.loads(resultat_ai_data)

    # If you want to include video bytes in the model (or handle it separately)
    video_bytes = await video.read()

    # For example, pass both to your controller
    resultat_ai_data_obj = ResultatAiCreate(**data_dict)

    # Now pass video_bytes separately or add as attribute if your controller expects it
    resultat_ai = resultat_ai_ctrl.create_resultat_ai(resultat_ai_data_obj, db, video_bytes=video_bytes)

    return resultat_ai

@router.put("/resultat_ai/{resultat_ai_id}", response_model=ResultatAiRead)
def update_resultat_ai(resultat_ai_id: int, resultat_ai_data: ResultatAiCreate, db: Session = Depends(get_db)):
    return resultat_ai_ctrl.update_resultat_ai(resultat_ai_id, resultat_ai_data, db)

@router.delete("/resultat_ai/{resultat_ai_id}")
def delete_resultat_ai(resultat_ai_id: int, db: Session = Depends(get_db)):
    return resultat_ai_ctrl.delete_resultat_ai(db, resultat_ai_id)
