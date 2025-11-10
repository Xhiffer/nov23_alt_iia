from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from database import SessionLocal
import controllers.resultat_ai_controller as resultat_ai_ctrl
from schemas.resultat_ai_schema import ResultatAiCreate, ResultatAiRead
import json
from typing import Optional
from fastapi.responses import StreamingResponse
import io
import os
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
    resultat_ai_data: str = Form(...),
    db: Session = Depends(get_db)
):
    print("📥 RAW incoming data:")
    print(resultat_ai_data[:300])

    try:
        data_dict = json.loads(resultat_ai_data)
        print("✅ Parsed data keys:", list(data_dict.keys()))
    except Exception as e:
        print("❌ JSON parse error:", e)
        raise

    # check for missing or extra fields
    from pydantic import ValidationError
    try:
        resultat_ai_data_obj = ResultatAiCreate(**data_dict)
    except ValidationError as e:
        print("❌ Validation error:", e.json())
        raise

    video_bytes = await video.read()
    print(f"🎥 Video size: {len(video_bytes)} bytes")

    resultat_ai = resultat_ai_ctrl.create_resultat_ai(
        resultat_ai_data_obj, db, video_bytes=video_bytes
    )
    return resultat_ai


@router.put("/resultat_ai/{resultat_ai_id}", response_model=ResultatAiRead)
def update_resultat_ai(resultat_ai_id: int, resultat_ai_data: ResultatAiCreate, db: Session = Depends(get_db)):
    return resultat_ai_ctrl.update_resultat_ai(resultat_ai_id, resultat_ai_data, db)

@router.delete("/resultat_ai/{resultat_ai_id}")
def delete_resultat_ai(resultat_ai_id: int, db: Session = Depends(get_db)):
    return resultat_ai_ctrl.delete_resultat_ai(db, resultat_ai_id)


@router.get("/resultat_ai", response_model=dict)
def get_resultat_ai_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * per_page
    total_count = resultat_ai_ctrl.count_all(db)  # You’ll need to implement this in the controller
    items = resultat_ai_ctrl.get_paginated(db, offset=offset, limit=per_page)
    
    return {
        "count": total_count,
        "page": page,
        "per_page": per_page,
        "items": [ResultatAiRead.from_orm(obj) for obj in items]
    }






from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse, Response
import os

@router.get("/resultat_ai/{resultat_ai_id}/video")
def get_resultat_ai_video(request: Request, resultat_ai_id: int, db: Session = Depends(get_db)):
    resultat_ai = resultat_ai_ctrl.get_resultat_ai(db, resultat_ai_id)
    if not resultat_ai or not resultat_ai.video_path:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = resultat_ai.video_path
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    file_size = os.path.getsize(video_path)
    range_header = request.headers.get('range')

    if range_header is None:
        # No Range header — return entire file with 200 status
        return StreamingResponse(open(video_path, "rb"), media_type="video/mp4")

    # Parse range header, e.g., "bytes=0-1023"
    bytes_range = range_header.strip().lower().replace("bytes=", "").split("-")
    try:
        start = int(bytes_range[0])
        end = int(bytes_range[1]) if bytes_range[1] else file_size - 1
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Range header")

    if start >= file_size or end >= file_size or start > end:
        raise HTTPException(status_code=416, detail="Requested Range Not Satisfiable")

    chunk_size = end - start + 1

    def iterfile():
        with open(video_path, "rb") as f:
            f.seek(start)
            bytes_left = chunk_size
            while bytes_left > 0:
                read_length = min(4096, bytes_left)
                data = f.read(read_length)
                if not data:
                    break
                bytes_left -= len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(chunk_size),
        "Content-Type": "video/mp4",
    }

    return StreamingResponse(iterfile(), status_code=206, headers=headers)



from fastapi.responses import FileResponse

@router.get("/test_video")
def test_video():
    path = "videos/video_6d9c1f9e50214a249f797e8ec9ea9e98.mp4"  # put here a static file you verified
    return FileResponse(path, media_type="video/mp4")