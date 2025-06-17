from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_estimer_gravite():
    # Données d'exemple pour tester l'API
    payload = {
        "nombre_vehicules": 3,
        "vitesse_estimee": 60.5,
        "impact_detecte": True,
        "conditions_meteo": "brouillard",
        "presence_pietons": False,
        "type_route": "route nationale"
    }

    response = client.post("/estimer_gravite", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "gravite_estimee" in data
    assert data["gravite_estimee"] in ['mineur', 'modéré', 'sévère', 'mortel']
