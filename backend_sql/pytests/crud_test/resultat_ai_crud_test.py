from fastapi.testclient import TestClient
import sys
import os

# Permet l'import depuis la racine du projet
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from main import app

client = TestClient(app)

def test_crud_resultat_ai():
    # Step 1: Create
    create_response = client.post(
        "/resultat_ai/",
        json={
            "nombre_vehicules": 3,
            "vitesse_estimee": 45.5,
            "impact_detecte": True,
            "conditions_meteo": "ensoleille",
            "presence_pietons": False,
            "type_route": "autoroute"
        }
    )
    assert create_response.status_code == 200
    created = create_response.json()
    resultat_ai_id = created["id"]
    print("Created Resultat AI:", created)
    assert created["nombre_vehicules"] == 3
    assert created["conditions_meteo"] == "ensoleille"

    # Step 2: Read (GET)
    get_response = client.get(f"/resultat_ai/{resultat_ai_id}")
    assert get_response.status_code == 200
    resultat_ai = get_response.json()
    assert resultat_ai["id"] == resultat_ai_id
    assert resultat_ai["impact_detecte"] is True

    # Step 3: Update
    update_response = client.put(
        f"/resultat_ai/{resultat_ai_id}",
        json={
            "nombre_vehicules": 1,
            "vitesse_estimee": 30.0,
            "impact_detecte": False,
            "conditions_meteo": "pluvieux",
            "presence_pietons": True,
            "type_route": "ville"
        }
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    print("Updated Resultat AI:", updated)
    assert updated["nombre_vehicules"] == 1
    assert updated["conditions_meteo"] == "pluvieux"
    assert updated["presence_pietons"] is True

    # Step 4: Read updated
    get_updated = client.get(f"/resultat_ai/{resultat_ai_id}")
    assert get_updated.status_code == 200
    assert get_updated.json()["nombre_vehicules"] == 1

    # Step 5: Delete
    delete_response = client.delete(f"/resultat_ai/{resultat_ai_id}")
    assert delete_response.status_code == 200
    detail_msg = delete_response.json().get("detail", "").lower()
    assert "deleted successfully" in detail_msg or "success" in detail_msg

    # Step 6: Final check (should return 404)
    final_get = client.get(f"/resultat_ai/{resultat_ai_id}")
    assert final_get.status_code == 404
    print("Final GET after deletion correctly returned 404.")
