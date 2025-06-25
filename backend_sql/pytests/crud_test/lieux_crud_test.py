from fastapi.testclient import TestClient
import sys
import os

# Allow import from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from main import app

client = TestClient(app)

def test_crud_lieu():
    # Step 1: Create
    create_response = client.post(
        "/lieux/",
        json={
            "id_accident": 1,
            "catr": 1,
            "voie": "A1",
            "v1": 1,
            "v2": "bis",
            "circ": 1,
            "nbv": "2",
            "vosp": 1,
            "prof": 1,
            "pr": "005+3",
            "pr1": "005+4",
            "plan": 1,
            "lartpc": 0.0,
            "larrout": 0.0,
            "surf": 1,
            "infra": 1,
            "situ": 1,
            "vma": 90
        }
    )
    assert create_response.status_code == 200
    created = create_response.json()
    lieu_id = created["id"]
    print("Created lieu:", created)
    assert created["id_accident"] == 1
    assert created["voie"] == "A1"

    # Step 2: Read (GET)
    get_response = client.get(f"/lieux/{lieu_id}")
    assert get_response.status_code == 200
    lieu = get_response.json()
    assert lieu["voie"] == "A1"

    # Step 3: Update
    update_response = client.put(
        f"/lieux/{lieu_id}",
        json={
            "id_accident": 2,
            "catr": 2,
            "voie": "N20",
            "v1": 2,
            "v2": "ter",
            "circ": 2,
            "nbv": "3",
            "vosp": 2,
            "prof": 2,
            "pr": "006+7",
            "pr1": "006+8",
            "plan": 2,
            "lartpc": 1.5,
            "larrout": 2.5,
            "surf": 2,
            "infra": 2,
            "situ": 2,
            "vma": 110
        }
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    print("Updated lieu:", updated)
    assert updated["voie"] == "N20"
    assert updated["vma"] == 110

    # Step 4: Read updated
    get_updated = client.get(f"/lieux/{lieu_id}")
    assert get_updated.status_code == 200
    assert get_updated.json()["voie"] == "N20"

    # Step 5: Delete
    delete_response = client.delete(f"/lieux/{lieu_id}")
    assert delete_response.status_code == 200
    assert delete_response.json().get("detail", "").lower() == "lieu deleted successfully" or "success" in delete_response.json().get("detail", "").lower()

    # Step 6: Final check
    final_get = client.get(f"/lieux/{lieu_id}")
    assert final_get.status_code == 404
    print("Final GET after deletion correctly returned 404.")
