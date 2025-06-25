from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import controllers.resultat_ai_controller as resultat_ai_ctrl
from schemas.resultat_ai_schema import ResultatAiCreate, ResultatAiRead

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

@router.post("/resultat_ai/", response_model=ResultatAiRead)
def create_resultat_ai(resultat_ai_data: ResultatAiCreate, db: Session = Depends(get_db)):
    return resultat_ai_ctrl.create_resultat_ai(resultat_ai_data, db)

@router.put("/resultat_ai/{resultat_ai_id}", response_model=ResultatAiRead)
def update_resultat_ai(resultat_ai_id: int, resultat_ai_data: ResultatAiCreate, db: Session = Depends(get_db)):
    return resultat_ai_ctrl.update_resultat_ai(resultat_ai_id, resultat_ai_data, db)

@router.delete("/resultat_ai/{resultat_ai_id}")
def delete_resultat_ai(resultat_ai_id: int, db: Session = Depends(get_db)):
    return resultat_ai_ctrl.delete_resultat_ai(db, resultat_ai_id)
