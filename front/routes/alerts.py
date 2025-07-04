from flask import Blueprint, jsonify, request, render_template
# from schemas.resultat_ai_schema import ResultatAiRead
import requests


bp_alerts = Blueprint("alerts", __name__)

@bp_alerts.route('/ajax/resultats_ai', methods=['GET'])
def get_resultats_ai():
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))

    # Call FastAPI
    try:
        response = requests.get(
            "http://backend_sql:8000/resultat_ai",
            params={"page": page, "per_page": size},
            timeout=5
        )
        response.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

    json_data = response.json()

    return jsonify({
        "last_page": (json_data["count"] + size - 1) // size,
        "data": json_data["items"]
    })

@bp_alerts.route("/alerts")
def alerts():
    return render_template("alerts.html")  # Don't keep the stray "return 'hi'"


@bp_alerts.route("/alert")
def alert():
    alert_id = request.args.get("id")
    return render_template("alert.html", alert_id=alert_id)

