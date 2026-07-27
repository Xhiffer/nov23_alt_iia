from fastapi.testclient import TestClient
import sys
import os

# Allow import from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from main import app

client = TestClient(app)

# Payload conforme au schéma actuel `AITrainingModelDataCreate` : `id_accident`
# est requis (BigInteger, sans FK), les features BAAC sont optionnelles.
BASE_PAYLOAD = {
    "id_accident": 999001,
    "id_usager": 42,
    "id_vehicule": 7,
    "grav": 1,
    "sexe": 1,
    "manv": 2,
    "mois": 6,
    "an": 2023,
    "dep": "75",
    "pr": "12",
}


def test_crud_ai_training_model_data():
    # Step 1: Create
    create_response = client.post("/ai-training-data/", json=BASE_PAYLOAD)
    assert create_response.status_code == 200, create_response.text
    created = create_response.json()
    record_id = created["id"]
    assert created["id_accident"] == 999001
    assert created["grav"] == 1

    # Step 2: Read (GET)
    get_response = client.get(f"/ai-training-data/{record_id}")
    assert get_response.status_code == 200
    record = get_response.json()
    assert record["id_accident"] == 999001
    assert record["sexe"] == 1

    # Step 3: Update
    updated_payload = {**BASE_PAYLOAD, "grav": 0, "sexe": 2, "manv": 3}
    update_response = client.put(f"/ai-training-data/{record_id}", json=updated_payload)
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["grav"] == 0
    assert updated["sexe"] == 2

    # Step 4: Read updated
    get_updated = client.get(f"/ai-training-data/{record_id}")
    assert get_updated.status_code == 200
    assert get_updated.json()["grav"] == 0

    # Step 5: Delete
    delete_response = client.delete(f"/ai-training-data/{record_id}")
    assert delete_response.status_code == 200
    assert "success" in delete_response.json().get("detail", "").lower()

    # Step 6: Final check
    final_get = client.get(f"/ai-training-data/{record_id}")
    assert final_get.status_code == 404
