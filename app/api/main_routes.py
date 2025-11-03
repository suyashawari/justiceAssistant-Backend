

# import os
# from flask import Blueprint, request, jsonify, current_app
# from app.models.models import Report
# from app.models import db
# from app.utils import extract_text
# from app.utils.refine import refine_extracted_text
# from datetime import datetime
# from flask_jwt_extended import jwt_required, get_jwt_identity

# # --- Imports for RQ ---
# from redis import Redis
# from rq import Queue
# from app.tasks import analyze_report_task
# # --------------------

# main = Blueprint('main', __name__)

# # --- Setup the RQ connection and Queue ---
# redis_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
# try:
#     redis_conn = Redis.from_url(redis_url)
#     q = Queue(connection=redis_conn)
#     redis_conn.ping()
#     print("✅ Successfully connected to Redis for RQ.")
# except Exception as e:
#     print(f"❌ Could not connect to Redis for RQ: {e}")
#     q = None
# # ----------------------------------------

# @main.route('/')
# def index():
#     return jsonify({"message": "JusticeAssist backend is running."})

# @main.route('/protected')
# @jwt_required()
# def protected():
#     return jsonify(message="You are authenticated")

# @main.route('/extract-text', methods=['POST'])
# def extract_text_route():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file provided'}), 400
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({'error': 'Empty file name'}), 400
#     upload_folder = 'uploads'
#     os.makedirs(upload_folder, exist_ok=True)
#     save_path = os.path.join(upload_folder, file.filename)
#     file.save(save_path)
#     text = extract_text(save_path)
#     refined = refine_extracted_text(text)
#     return jsonify({
#         'extracted_text': text,
#         'refined_evidence': refined
#     })

# @main.route("/submit-report", methods=["POST"])
# @jwt_required()
# def submit_report():
#     try:
#         data = request.form
#         user_id = get_jwt_identity()

#         if not data.get('description'):
#             return jsonify({"error": "Description is a required field"}), 400

#         file_path = None
#         if 'evidence_file' in request.files and request.files['evidence_file'].filename != '':
#             evidence_file = request.files['evidence_file']
#             upload_folder = "uploads/"
#             os.makedirs(upload_folder, exist_ok=True)
#             file_path = os.path.join(upload_folder, evidence_file.filename)
#             evidence_file.save(file_path)
#             print(f"📁 Evidence file saved to: {file_path}")

#         # Create the report with an initial "submitted" status. The worker will update it.
#         new_report = Report(
#             user_id=user_id,
#             first_name=data.get('first_name'),
#             last_name=data.get('last_name'),
#             address=data.get('address'),
#             email=data.get('email'),
#             phone=data.get('phone'),
#             state=data.get('state'),
#             city=data.get('city'),
#             complaint_category=data.get('complaint_category'),
#             incident_date=data.get('incident_date'),
#             delay_in_reporting=data.get('delay_in_reporting'),
#             platform=data.get('platform'),
#             description=data.get('description'),
#             evidence_file=file_path,
#             status='submitted',
#             created_at=datetime.utcnow()
#         )
#         db.session.add(new_report)
#         db.session.commit()
        
#         report_id = new_report.id
#         print(f"✅ Report {report_id} saved to DB with 'submitted' status.")

#         # Send the task to the RQ worker via Redis for background processing.
#         if q:
#             q.enqueue(analyze_report_task, report_id)
#             print(f"✅ Task for report {report_id} successfully sent to RQ worker.")
#         else:
#             print("❌ RQ worker not available. Task not dispatched.")

#         return jsonify({
#             "status": "success",
#             "message": "Report submitted and queued for analysis.",
#             "report_id": report_id
#         }), 201

#     except Exception as e:
#         db.session.rollback()
#         import traceback
#         traceback.print_exc()
#         return jsonify({"error": "An internal server error occurred.", "details": str(e)}), 500

# @main.route('/update-report/<int:report_id>', methods=['PUT'])
# @jwt_required()
# def update_report(report_id):
#     current_user_id = get_jwt_identity()
#     data = request.get_json()
#     report = Report.query.filter_by(id=report_id, user_id=current_user_id).first()
#     if not report:
#         return jsonify({"error": "Report not found or access denied"}), 404
#     if 'status' in data:
#         report.status = data['status']
#     if 'description' in data:
#         report.description = data['description']
#     try:
#         db.session.commit()
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": "Failed to update report", "details": str(e)}), 500
#     return jsonify({"message": "Report updated", "report": report.to_dict()}), 200
import os
from flask import Blueprint, request, jsonify, current_app
from app.models.models import Report
from app.models import db
from app.utils import extract_text
from app.utils.refine import refine_extracted_text
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from redis import Redis
from rq import Queue
from app.tasks import analyze_report_task
from app.api.admin_routes import mock_settings_db # Import mock settings

main = Blueprint('main', __name__)
redis_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
try:
    redis_conn = Redis.from_url(redis_url)
    q = Queue(connection=redis_conn)
    redis_conn.ping()
    print("✅ Successfully connected to Redis for RQ.")
except Exception as e:
    print(f"❌ Could not connect to Redis for RQ: {e}")
    q = None

@main.route('/')
def index():
    return jsonify({"message": "JusticeAssist backend is running."})

@main.route('/protected')
@jwt_required()
def protected():
    return jsonify(message="You are authenticated")

@main.route('/extract-text', methods=['POST'])
def extract_text_route():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty file name'}), 400
    upload_folder = 'uploads'
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, file.filename)
    file.save(save_path)
    text = extract_text(save_path)
    refined = refine_extracted_text(text)
    return jsonify({
        'extracted_text': text,
        'refined_evidence': refined
    })

@main.route("/submit-report", methods=["POST"])
@jwt_required()
def submit_report():
    try:
        data = request.form
        user_id = get_jwt_identity()
        if not data.get('description'):
            return jsonify({"error": "Description is a required field"}), 400
        file_path = None
        if 'evidence_file' in request.files and request.files['evidence_file'].filename != '':
            evidence_file = request.files['evidence_file']
            upload_folder = "uploads/"
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, evidence_file.filename)
            evidence_file.save(file_path)
            print(f"📁 Evidence file saved to: {file_path}")
        new_report = Report(
            user_id=user_id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            address=data.get('address'),
            email=data.get('email'),
            phone=data.get('phone'),
            state=data.get('state'),
            city=data.get('city'),
            complaint_category=data.get('complaint_category'),
            incident_date=data.get('incident_date'),
            delay_in_reporting=data.get('delay_in_reporting'),
            platform=data.get('platform'),
            description=data.get('description'),
            evidence_file=file_path,
            status='submitted',
            created_at=datetime.utcnow()
        )
        db.session.add(new_report)
        db.session.commit()
        report_id = new_report.id
        print(f"✅ Report {report_id} saved to DB with 'submitted' status.")
        if q:
            q.enqueue(analyze_report_task, report_id)
            print(f"✅ Task for report {report_id} successfully sent to RQ worker.")
        else:
            print("❌ RQ worker not available. Task not dispatched.")
        return jsonify({
            "status": "success",
            "message": "Report submitted and queued for analysis.",
            "report_id": report_id
        }), 201
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An internal server error occurred.", "details": str(e)}), 500

@main.route('/update-report/<int:report_id>', methods=['PUT'])
@jwt_required()
def update_report(report_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()
    report = Report.query.filter_by(id=report_id, user_id=current_user_id).first()
    if not report:
        return jsonify({"error": "Report not found or access denied"}), 404
    if 'status' in data:
        report.status = data['status']
    if 'description' in data:
        report.description = data['description']
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update report", "details": str(e)}), 500
    return jsonify({"message": "Report updated", "report": report.to_dict()}), 200

@main.route('/api/maintenance-status', methods=['GET'])
def get_maintenance_status():
    """Public endpoint to check if the app is in maintenance mode."""
    is_maintenance = mock_settings_db.get('maintenance_mode', False)
    return jsonify({"maintenance_mode": is_maintenance})