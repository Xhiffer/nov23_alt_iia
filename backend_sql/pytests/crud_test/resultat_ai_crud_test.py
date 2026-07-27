from fastapi.testclient import TestClient
import sys
import os
import json

# Permet l'import depuis la racine du projet
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from main import app
from database import SessionLocal
from models.resultat_ai_model import ResultatAi
from sqlalchemy import func

client = TestClient(app)

# Payload conforme au schéma actuel `ResultatAiCreate` : toutes les features BAAC
# sont requises. La création passe par un upload multipart (vidéo + JSON).
FEATURES = {
    "sexe": 1, "obsm": 2, "pr": "10", "jour": 15, "col": 3, "choc": 1, "pr1": "5",
    "mois": 6, "age": 30, "manv": 2, "plan": 1, "an": 2023, "cos_time": 0.5,
    "n_passager": 1, "motor": 1, "larrout": 60, "lum": 1, "sin_time": 0.5,
    "n_pieton": 0, "catr": 3, "surf": 1, "dep": 75, "senc": 1, "circ": 2,
    "infra": 0, "agg": 2, "day_of_week": 3, "catv": 7, "vosp": 0, "situ": 1,
    "int_": 1, "obs": 0, "prof": 1, "atm": 1, "is_holiday": 0,
    "vma_cat": "50-70", "gravite_estimee": 1,
}


def _create_resultat_ai(features: dict) -> None:
    """Crée un ResultatAi via le flux multipart réel (vidéo + JSON form)."""
    resp = client.post(
        "/resultat_ai/",
        files={"video": ("test.mp4", b"fake-video-bytes", "video/mp4")},
        data={"resultat_ai_data": json.dumps(features)},
    )
    assert resp.status_code == 200, resp.text
    # response_model=ResultatAiCreate -> l'id n'est pas renvoyé ; on le récupère via la liste.
    body = resp.json()
    assert body["sexe"] == features["sexe"]


def _latest_id() -> int:
    """Renvoie l'id du ResultatAi le plus récent.

    L'endpoint de création (response_model=ResultatAiCreate) ne renvoie pas l'id,
    et la liste paginée n'a pas d'ORDER BY fiable ; on lit donc directement le
    max(id) en base (déterministe pour un test mono-thread)."""
    db = SessionLocal()
    try:
        latest = db.query(func.max(ResultatAi.id)).scalar()
        assert latest is not None, "aucun ResultatAi en base après création"
        return int(latest)
    finally:
        db.close()


def test_crud_resultat_ai():
    # Step 1: Create (multipart) puis récupération de l'id via la liste
    _create_resultat_ai(FEATURES)
    resultat_ai_id = _latest_id()

    # Step 2: Read (GET)
    get_response = client.get(f"/resultat_ai/{resultat_ai_id}")
    assert get_response.status_code == 200, get_response.text
    resultat_ai = get_response.json()
    assert resultat_ai["id"] == resultat_ai_id
    assert resultat_ai["atm"] == 1
    assert resultat_ai["video_path"]  # vidéo persistée

    # Step 3: Update (JSON, pas multipart)
    updated = {**FEATURES, "mois": 12, "age": 40, "gravite_estimee": 0}
    update_response = client.put(f"/resultat_ai/{resultat_ai_id}", json=updated)
    assert update_response.status_code == 200, update_response.text
    body = update_response.json()
    assert body["mois"] == 12
    assert body["age"] == 40

    # Step 4: Read updated
    get_updated = client.get(f"/resultat_ai/{resultat_ai_id}")
    assert get_updated.status_code == 200
    assert get_updated.json()["mois"] == 12

    # Step 5: Delete
    delete_response = client.delete(f"/resultat_ai/{resultat_ai_id}")
    assert delete_response.status_code == 200
    assert "success" in delete_response.json().get("detail", "").lower()

    # Step 6: Final check (should return 404)
    final_get = client.get(f"/resultat_ai/{resultat_ai_id}")
    assert final_get.status_code == 404
