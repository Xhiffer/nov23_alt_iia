from flask import Blueprint, jsonify, request, render_template
from models import ResultatAi
from schemas import ResultatAiRead


alerts = Blueprint("alerts", __name__)

@alerts.route('/ajax/resultats_ai', methods=['GET'])
def get_resultats_ai():
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))

    query = ResultatAi.query  # optionally add filters here
    total = query.count()
    resultats = query.offset((page - 1) * size).limit(size).all()

    result_list = [ResultatAiRead.model_validate(r).model_dump() for r in resultats]
    return jsonify({
        "last_page": (total + size - 1) // size,
        "data": result_list
    })


@alerts.route("/alerts")
def alerts():
    return render_template("alerts.html")  # Don't keep the stray "return 'hi'"

