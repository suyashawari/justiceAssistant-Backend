

# # from flask import Blueprint, request, jsonify
# # from app.models import Report
# # from app import db
# # from app.utils import extract_text
# # from app.utils.refine import refine_extracted_text
# # import os
# # from datetime import datetime
# # from flask_jwt_extended import jwt_required, get_jwt_identity
# # from app.utils.suspect_utils import analyze_evidence # Make sure this is imported

# # main = Blueprint('main', __name__)

# # @main.route('/')
# # def index():
# #     return jsonify({"message": "JusticeAssist backend is running."})

# # @main.route('/protected')
# # @jwt_required()
# # def protected():
# #     return jsonify(message="You are authenticated")

# # @main.route('/extract-text', methods=['POST'])
# # def extract_text_route():
# #     if 'file' not in request.files:
# #         return jsonify({'error': 'No file provided'}), 400
# #     file = request.files['file']
# #     if file.filename == '':
# #         return jsonify({'error': 'Empty file name'}), 400
# #     upload_folder = 'uploads'
# #     os.makedirs(upload_folder, exist_ok=True)
# #     save_path = os.path.join(upload_folder, file.filename)
# #     file.save(save_path)
# #     text = extract_text(save_path)
# #     refined = refine_extracted_text(text)
# #     return jsonify({
# #         'extracted_text': text,
# #         'refined_evidence': refined
# #     })

# # # --- THIS IS THE CORRECTED FUNCTION ---
# # @main.route("/submit-report", methods=["POST"])
# # @jwt_required()
# # def submit_report():
# #     try:
# #         # Use request.form to get data from FormData
# #         data = request.form
        
# #         # --- 1. Get data from the form using the correct keys ---
# #         first_name = data.get('first_name')
# #         last_name = data.get('last_name')
# #         address = data.get('address')
# #         email = data.get('email')
# #         phone = data.get('phone')
# #         state = data.get('state')
# #         city = data.get('city')
# #         complaint_category = data.get('complaint_category')
# #         incident_date = data.get('incident_date')
# #         delay_in_reporting = data.get('delay_in_reporting')
# #         platform = data.get('platform')
# #         description = data.get('description')
# #         user_id = get_jwt_identity()

# #         # --- 2. Perform validation for the essential field ---
# #         if not description:
# #             return jsonify({"error": "Description is a required field"}), 400

# #         evidence_file = request.files.get("evidence_file")
# #         file_path = None
# #         if evidence_file:
# #             upload_folder = "uploads/"
# #             os.makedirs(upload_folder, exist_ok=True)
# #             file_path = os.path.join(upload_folder, evidence_file.filename)
# #             evidence_file.save(file_path)
# #             print(f"📁 Evidence file saved to: {file_path}")
        
# #         # --- 3. (Optional but good) Run forensic analysis ---
# #         # The text for analysis should be the detailed description
# #         forensic_result = analyze_evidence(text=description, file_path=file_path)

# #         # --- 4. Create the Report object with the CORRECT fields that match models.py ---
# #         new_report = Report(
# #             user_id=user_id,
# #             first_name=first_name,
# #             last_name=last_name,
# #             address=address,
# #             email=email,
# #             phone=phone,
# #             state=state,
# #             city=city,
# #             complaint_category=complaint_category,
# #             incident_date=incident_date,
# #             delay_in_reporting=delay_in_reporting,
# #             platform=platform,
# #             description=description,
# #             evidence_file=file_path,
# #             status='submitted',
# #             created_at=datetime.utcnow()
# #         )

# #         # Use the JSON helper methods to store the analysis results
# #         new_report.set_json_field("forensic_summary", forensic_result.get("dashboard", {}))
# #         new_report.set_json_field("forensic_details", forensic_result.get("detailed", {}))

# #         db.session.add(new_report)
# #         db.session.commit()

# #         print("✅ Report successfully created and stored in the database!")
# #         return jsonify({
# #             "status": "success",
# #             "message": "Report submitted successfully",
# #             "report_id": new_report.id
# #         }), 201

# #     except Exception as e:
# #         db.session.rollback()
# #         print(f"❌ Exception in /submit-report: {str(e)}")
# #         # It's good practice to log the full error for debugging
# #         import traceback
# #         traceback.print_exc()
# #         return jsonify({"error": "An internal server error occurred.", "details": str(e)}), 500

# # # The update_report function remains the same
# # @main.route('/update-report/<int:report_id>', methods=['PUT'])
# # @jwt_required()
# # def update_report(report_id):
# #     current_user_id = get_jwt_identity()
# #     data = request.get_json()
# #     report = Report.query.filter_by(id=report_id, user_id=current_user_id).first()
# #     if not report:
# #         return jsonify({"error": "Report not found or access denied"}), 404
# #     if 'status' in data:
# #         report.status = data['status']
# #     if 'description' in data:
# #         report.description = data['description']
# #     try:
# #         db.session.commit()
# #     except Exception as e:
# #         db.session.rollback()
# #         return jsonify({"error": "Failed to update report", "details": str(e)}), 500
# #     return jsonify({"message": "Report updated", "report": report.to_dict()}), 200
# # app/routes/main_routes.py

# import os
# from flask import Blueprint, request, jsonify, current_app
# from app.models import Report
# from app import db
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
#     # A quick check to see if the connection is alive
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
#     # ... (this function remains the same)
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

# # --- THIS IS THE FINAL, CORRECTED FUNCTION ---
# @main.route("/submit-report", methods=["POST"])
# @jwt_required()
# def submit_report():
#     try:
#         data = request.form
#         user_id = get_jwt_identity()

#         if not data.get('description'):
#             return jsonify({"error": "Description is a required field"}), 400

#         file_path = None
#         if 'evidence_file' in request.files:
#             evidence_file = request.files['evidence_file']
#             if evidence_file.filename != '':
#                 upload_folder = "uploads/"
#                 os.makedirs(upload_folder, exist_ok=True)
#                 file_path = os.path.join(upload_folder, evidence_file.filename)
#                 evidence_file.save(file_path)
#                 print(f"📁 Evidence file saved to: {file_path}")

#         # --- 1. Create the Report object with a 'submitted' status ---
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
#             status='submitted',  # The initial status
#             created_at=datetime.utcnow()
#         )
#         db.session.add(new_report)
#         db.session.commit()
        
#         report_id = new_report.id
#         print(f"✅ Report {report_id} saved to DB with 'submitted' status.")

#         # --- 2. Now, send the task to the RQ worker via Redis ---
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

# # The update_report function remains the same
# @main.route('/update-report/<int:report_id>', methods=['PUT'])
# @jwt_required()
# def update_report(report_id):
#     # ... (this function remains the same)
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


# app/routes/main_routes.py

import os
from flask import Blueprint, request, jsonify, current_app
from app.models.models import Report
from app.models import db
from app.utils import extract_text
from app.utils.refine import refine_extracted_text
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity

# --- Imports for RQ ---
from redis import Redis
from rq import Queue
from app.tasks import analyze_report_task
# --------------------

main = Blueprint('main', __name__)

# --- Setup the RQ connection and Queue ---
redis_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
try:
    redis_conn = Redis.from_url(redis_url)
    q = Queue(connection=redis_conn)
    redis_conn.ping()
    print("✅ Successfully connected to Redis for RQ.")
except Exception as e:
    print(f"❌ Could not connect to Redis for RQ: {e}")
    q = None
# ----------------------------------------

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

        # Create the report with an initial "submitted" status. The worker will update it.
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

        # Send the task to the RQ worker via Redis for background processing.
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