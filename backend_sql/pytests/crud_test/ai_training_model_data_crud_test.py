from fastapi.testclient import TestClient
import sys
import os

# Allow import from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from main import app

client = TestClient(app)


def test_crud_ai_training_model_data():
    # Step 1: Create
    create_response = client.post(
        "/ai-training-data/",
        json={
            "input_data": "sample text",
            "label": "positive",
            "source": "unit-test",
            "added_date": "2025-01-01T00:00:00"
        }
    )
    assert create_response.status_code == 200
    created = create_response.json()
    record_id = created["id"]
    print("Created record:", created)
    assert created["input_data"] == "sample text"
    assert created["label"] == "positive"

    # Step 2: Read (GET)
    get_response = client.get(f"/ai-training-data/{record_id}")
    assert get_response.status_code == 200
    record = get_response.json()
    assert record["input_data"] == "sample text"

    # Step 3: Update
    update_response = client.put(
        f"/ai-training-data/{record_id}",
        json={
            "input_data": "updated text",
            "label": "negative",
            "source": "unit-test-updated",
            "added_date": "2025-02-01T12:00:00"
        }
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    print("Updated record:", updated)
    assert updated["input_data"] == "updated text"
    assert updated["label"] == "negative"

    # Step 4: Read updated
    get_updated = client.get(f"/ai-training-data/{record_id}")
    assert get_updated.status_code == 200
    assert get_updated.json()["input_data"] == "updated text"

    # Step 5: Delete
    delete_response = client.delete(f"/ai-training-data/{record_id}")
    assert delete_response.status_code == 200
    assert (
        delete_response.json().get("detail", "").lower()
        == "ai training model data deleted successfully"
        or "success" in delete_response.json().get("detail", "").lower()
    )

    # Step 6: Final check
    final_get = client.get(f"/ai-training-data/{record_id}")
    assert final_get.status_code == 404
    print("Final GET after deletion correctly returned 404.")
