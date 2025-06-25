from fastapi.testclient import TestClient
import sys
import os

# Allow import from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from main import app

client = TestClient(app)

def test_crud_caract():
    # Step 1: Create
    create_response = client.post(
        "/caracts/",
        json={
            "id_accident": 1,
            "jour": 15,
            "mois": 6,
            "an": "2025",
            "hrmn": "14:30",
            "lum": 1,
            "dep": "75",
            "com": "75056",
            "agg": 1,
            "int_": 2,
            "atm": 3,
            "col": 4,
            "adr": "Rue de Rivoli",
            "lat": 48.8566,
            "long": 2.3522
        }
    )
    assert create_response.status_code == 200
    created = create_response.json()
    caract_id = created["id"]
    print("Created caract:", created)
    assert created["id_accident"] == 1
    assert created["adr"] == "Rue de Rivoli"

    # Step 2: Read (GET)
    get_response = client.get(f"/caracts/{caract_id}")
    assert get_response.status_code == 200
    caract = get_response.json()
    assert caract["adr"] == "Rue de Rivoli"

    # Step 3: Update
    update_response = client.put(
        f"/caracts/{caract_id}",
        json={
            "id_accident": 2,
            "jour": 20,
            "mois": 12,
            "an": "2024",
            "hrmn": "18:00",
            "lum": 2,
            "dep": "13",
            "com": "13055",
            "agg": 2,
            "int_": 1,
            "atm": 4,
            "col": 5,
            "adr": "Boulevard Michelet",
            "lat": 43.2965,
            "long": 5.3698
        }
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    print("Updated caract:", updated)
    assert updated["adr"] == "Boulevard Michelet"
    assert updated["dep"] == "13"

    # Step 4: Read updated
    get_updated = client.get(f"/caracts/{caract_id}")
    assert get_updated.status_code == 200
    assert get_updated.json()["adr"] == "Boulevard Michelet"

    # Step 5: Delete
    delete_response = client.delete(f"/caracts/{caract_id}")
    assert delete_response.status_code == 200
    assert delete_response.json().get("detail", "").lower() == "caract deleted successfully" or "success" in delete_response.json().get("detail", "").lower()

    # Step 6: Final check
    final_get = client.get(f"/caracts/{caract_id}")
    assert final_get.status_code == 404
    print("Final GET after deletion correctly returned 404.")
