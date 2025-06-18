from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from main import app

client = TestClient(app)

def test_crud_vehicule():
    # Step 1: Create
    create_response = client.post(
    "/vehicules/",
    json={
        "id_accident": 1,
        "id_vehicule": 9,
        "num_veh": "NUM456",
        "senc": 2,
        "catv": 3,
        "obs": 4,
        "obsm": 5,
        "choc": 6,
        "manv": 7,
        "motor": 8
    }
)
    assert create_response.status_code == 200
    created = create_response.json()
    vehicule_id = created["id"]  # adjust if your controller returns differently
    print("Created vehicule:", created)

    # Step 2: Read (check created)
    get_response = client.get(f"/vehicules/{vehicule_id}")
    assert get_response.status_code == 200
    vehicule = get_response.json()
    assert vehicule["id_vehicule"] == 9

    # Step 3: Update
    update_response = client.put(
        f"/vehicules/{vehicule_id}",
        json={
            "id_accident": 2,
            "id_vehicule": 16,
            "num_veh": "NUM999",
            "senc": 9,
            "catv": 10,
            "obs": 11,
            "obsm": 12,
            "choc": 13,
            "manv": 14,
            "motor": 15
        }
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["id_vehicule"] == 16
    print("Updated vehicule:", updated)

    # Step 4: Read (check updated)
    get_updated = client.get(f"/vehicules/{vehicule_id}")
    assert get_updated.status_code == 200
    assert get_updated.json()["id_vehicule"] == 16

    # Step 5: Delete
    delete_response = client.delete(f"/vehicules/{vehicule_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["detail"] == "Vehicule deleted successfully" or "success" in delete_response.json()

    # Step 6: Read (check deletion)
    final_get = client.get(f"/vehicules/{vehicule_id}")
    assert final_get.status_code == 404
    print("Final get after deletion returned 404 as expected.")
