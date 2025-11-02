
# import os
# from flask import Blueprint, request, jsonify, current_app
# from werkzeug.exceptions import BadRequest
# from datetime import datetime
# from redis import Redis
# from rq import Queue
# from app.tasks import analyze_report_task
# from flask_jwt_extended import jwt_required, get_jwt_identity
# from app.models.models import Report

# report = Blueprint("report", __name__)

# redis_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
# try:
#     redis_conn = Redis.from_url(redis_url)
#     q = Queue(connection=redis_conn)
# except Exception as e:
#     current_app.logger.error(f"Could not connect to Redis for RQ: {e}")
#     q = None

# @report.route("/submit", methods=["POST"])
# def submit_report():
#     # This is a minimal route. The primary, more detailed submission logic
#     # is correctly handled in app/routes/main_routes.py
#     data = request.get_json(silent=True)
#     if not data:
#         raise BadRequest("JSON body required")
#     # ... (rest of this function remains the same)
#     from app.models import db
#     new_report = Report(
#         title=data.get("title"),
#         description=data.get("description"),
#         status="pending",
#         created_at=datetime.utcnow()
#     )
#     db.session.add(new_report)
#     db.session.commit()
#     report_id = new_report.id
#     if q:
#         q.enqueue(analyze_report_task, report_id)
#     return jsonify({"status": "accepted", "report_id": report_id}), 202


# # --- CORRECTED AND ENHANCED ENDPOINT ---
# @report.route("/<int:report_id>/details", methods=["GET"])
# @jwt_required()
# def get_report_details(report_id):
#     """
#     Provides a complete report, including both the user's original
#     submission details and the full AI forensic analysis.
#     """
#     current_user_id = get_jwt_identity()
#     report = Report.query.filter_by(id=report_id, user_id=int(current_user_id)).first()

#     if not report:
#         return jsonify({"status": "error", "message": "Report not found or access denied"}), 404

#     analysis_details = report.get_json_field("forensic_details")
    
#     # Check if analysis is complete
#     if report.status != 'analyzed' or not analysis_details:
#         return jsonify({
#             "status": "pending", 
#             "message": "Report analysis is not yet complete.",
#             "data": {
#                 "submission_details": report.to_dict(), # Still send submission data
#                 "analysis_details": None
#             }
#         }), 202

#     if "error" in analysis_details:
#         return jsonify({
#             "status": "error", 
#             "message": "Analysis details are unavailable for this report.",
#             "data": {
#                 "submission_details": report.to_dict(),
#                 "analysis_details": analysis_details
#             }
#         }), 404

#     # Combine both user submission and AI analysis into one response
#     combined_data = {
#         "submission_details": report.to_dict(),
#         "analysis_details": analysis_details
#     }

#     return jsonify({"status": "success", "data": combined_data}), 200


import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest
from datetime import datetime
from redis import Redis
from rq import Queue
from app.tasks import analyze_report_task
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models.models import Report

report = Blueprint("report", __name__)
redis_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
try:
    redis_conn = Redis.from_url(redis_url)
    q = Queue(connection=redis_conn)
except Exception as e:
    current_app.logger.error(f"Could not connect to Redis for RQ: {e}")
    q = None

@report.route("/submit", methods=["POST"])
def submit_report():
    data = request.get_json(silent=True)
    if not data:
        raise BadRequest("JSON body required")
    from app.models import db
    new_report = Report(
        title=data.get("title"),
        description=data.get("description"),
        status="pending",
        created_at=datetime.utcnow()
    )
    db.session.add(new_report)
    db.session.commit()
    report_id = new_report.id
    if q:
        q.enqueue(analyze_report_task, report_id)
    return jsonify({"status": "accepted", "report_id": report_id}), 202

@report.route("/<int:report_id>/details", methods=["GET"])
@jwt_required()
def get_report_details(report_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    user_role = claims.get("role")

    # Fetch the report by its ID first
    report = Report.query.get(report_id)

    # Check if the report exists
    if not report:
        return jsonify({"status": "error", "message": "Report not found"}), 404

    # *** AUTHORIZATION LOGIC UPDATE ***
    # Grant access if the user is an admin OR if they are the owner of the report.
    is_owner = str(report.user_id) == str(current_user_id)
    is_admin = user_role == "admin"

    if not is_owner and not is_admin:
        return jsonify({"status": "error", "message": "Access denied"}), 403 # 403 Forbidden is more accurate

    # If authorization passes, proceed with the original logic
    analysis_details = report.get_json_field("forensic_details")

    if report.status != 'analyzed' or not analysis_details:
        return jsonify({
            "status": "pending",
            "message": "Report analysis is not yet complete.",
            "data": {
                "submission_details": report.to_dict(),
                "analysis_details": None
            }
        }), 202

    if "error" in analysis_details:
        return jsonify({
            "status": "error",
            "message": "Analysis details are unavailable for this report.",
            "data": {
                "submission_details": report.to_dict(),
                "analysis_details": analysis_details
            }
        }), 404

    combined_data = {
        "submission_details": report.to_dict(),
        "analysis_details": analysis_details
    }
    return jsonify({"status": "success", "data": combined_data}), 200