from fastapi.testclient import TestClient
import sys
import os

# Allow import from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from main import app

client = TestClient(app)

def test_crud_usager():
    # Step 1: Create
    create_response = client.post(
        "/usagers/",
                json={
            "id_accident": 1,
            "id_usager": 42,        
            "id_vehicule": 101,      
            "num_veh": "01",
            "place": 1,
            "catu": 1,
            "grav": 1,
            "sexe": 1,
            "an_nais": 1990,
            "trajet": 1,
            "secu1": 1,               
            "secu2": None,
            "secu3": None,
            "locp": 1,
            "actp": "traversait",     
            "etatp": 1
        }
    )
    assert create_response.status_code == 200
    created = create_response.json()
    usager_id = created["id"]
    print("Created usager:", created)
    assert created["id_usager"] == 42

    # Step 2: Read (GET)
    get_response = client.get(f"/usagers/{usager_id}")
    assert get_response.status_code == 200
    usager = get_response.json()
    assert usager["id_usager"] == 42

    # Step 3: Update
    update_response = client.put(
        f"/usagers/{usager_id}",
           json={
        "id_accident": 2,
        "id_usager": 84,
        "id_vehicule": 202,
        "num_veh": "02",
        "place": 2,
        "catu": 2,
        "grav": 2,
        "sexe": 2,
        "an_nais": 1985,
        "trajet": 2,
        "secu1": 2,           
        "secu2": None,
        "secu3": None,
        "locp": 2,
        "actp": "marchait",  
        "etatp": 2
    }
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    print("Updated usager:", updated)
    assert updated["id_usager"] == 84

    # Step 4: Read updated
    get_updated = client.get(f"/usagers/{usager_id}")
    assert get_updated.status_code == 200
    assert get_updated.json()["id_usager"] == 84

    # Step 5: Delete
    delete_response = client.delete(f"/usagers/{usager_id}")
    assert delete_response.status_code == 200
    assert delete_response.json().get("detail", "").lower() == "usager deleted successfully" or "success" in delete_response.json().get("detail", "").lower()

    # Step 6: Final check
    final_get = client.get(f"/usagers/{usager_id}")
    assert final_get.status_code == 404
    print("Final GET after deletion correctly returned 404.")
