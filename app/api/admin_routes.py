
# from flask import Blueprint, jsonify, request
# from app.models.models import Report, User
# from app.utils.decorators import admin_required
# from app.models import db
# from sqlalchemy import func
# from datetime import datetime, timedelta
# import traceback

# admin_bp = Blueprint("admin", __name__)

# # --- MOCK SETTINGS DATABASE ---
# # In a real application, this would come from a database table or a config file.
# mock_settings_db = {
#     "maintenance_mode": False,
#     "api_keys": {
#         "openai": "sk-...",
#         "google_gemini": "AIza...",
#         "openrouter": "sk-or-v1..."
#     },
#     "report_categories": [
#         "Online Financial Fraud",
#         "Cyber Harassment",
#         "Cyber Crime Against Women",
#         "Hacking/Unauthorized Access",
#         "Cryptocurrency Scam" # Example of a custom category
#     ]
# }
# # ------------------------------


# @admin_bp.route("/admin/all-reports", methods=["GET"])
# @admin_required()
# def get_all_reports():
#     try:
#         reports = Report.query.order_by(Report.created_at.desc()).all()
#         all_reports_data = [report.to_dict() for report in reports]
#         return jsonify({
#             "status": "success",
#             "total_reports": len(all_reports_data),
#             "reports": all_reports_data
#         }), 200
#     except Exception as e:
#         print(f"Error in /admin/all-reports: {e}")
#         traceback.print_exc()
#         return jsonify({"status": "error", "message": str(e)}), 500

# @admin_bp.route("/admin/report-analytics", methods=["GET"])
# @admin_required()
# def get_report_analytics():
#     try:
#         period = request.args.get('period', '7d')
#         today = datetime.utcnow().date()

#         if period == 'today':
#             start_date = today
#         elif period == '30d':
#             start_date = today - timedelta(days=29)
#         elif period == 'this_month':
#             start_date = today.replace(day=1)
#         else:
#             start_date = today - timedelta(days=6)
        
#         end_date = today + timedelta(days=1)

#         date_labels = []
#         current_date = start_date
#         while current_date < end_date:
#             date_labels.append(current_date)
#             current_date += timedelta(days=1)
        
#         formatted_labels = [d.strftime('%b %d') for d in date_labels]

#         total_reports_in_period = db.session.query(Report).filter(
#             Report.created_at >= start_date,
#             Report.created_at < end_date
#         ).count()

#         if total_reports_in_period == 0:
#             return jsonify({"labels": formatted_labels, "datasets": []})

#         top_users_query = db.session.query(
#             User.username,
#             func.count(Report.id).label('report_count')
#         ).join(Report, Report.user_id == User.id).filter(
#             Report.created_at >= start_date,
#             Report.created_at < end_date
#         ).group_by(User.username).order_by(
#             func.count(Report.id).desc()
#         ).limit(3).all()

#         top_user_usernames = [user.username for user in top_users_query]

#         daily_counts_query = db.session.query(
#             User.username,
#             func.date(Report.created_at).label('report_day'),
#             func.count(Report.id).label('daily_count')
#         ).join(Report, Report.user_id == User.id).filter(
#             User.username.in_(top_user_usernames),
#             Report.created_at >= start_date,
#             Report.created_at < end_date
#         ).group_by(User.username, func.date(Report.created_at)).all()

#         user_data = {username: {label.strftime('%Y-%m-%d'): 0 for label in date_labels} for username in top_user_usernames}

#         for row in daily_counts_query:
#             if row.username in user_data:
#                 if row.report_day:
#                     user_data[row.username][row.report_day] = row.daily_count

#         datasets = []
#         colors = [
#             {'border': 'rgba(63, 114, 175, 1)', 'bg': 'rgba(63, 114, 175, 0.3)'},
#             {'border': 'rgba(40, 167, 69, 1)', 'bg': 'rgba(40, 167, 69, 0.3)'},
#             {'border': 'rgba(253, 126, 20, 1)', 'bg': 'rgba(253, 126, 20, 0.3)'}
#         ]

#         for i, username in enumerate(top_user_usernames):
#             color_pair = colors[i % len(colors)]
#             datasets.append({
#                 "label": username,
#                 "data": list(user_data[username].values()),
#                 "borderColor": color_pair['border'],
#                 "backgroundColor": color_pair['bg'],
#                 "fill": True,
#                 "tension": 0.4
#             })
        
#         return jsonify({"labels": formatted_labels, "datasets": datasets})

#     except Exception as e:
#         print(f"Error in /admin/report-analytics: {e}")
#         traceback.print_exc()
#         return jsonify({"status": "error", "message": "An internal server error occurred while generating analytics."}), 500

# @admin_bp.route("/admin/settings", methods=["GET"])
# @admin_required()
# def get_settings():
#     return jsonify(mock_settings_db)

# @admin_bp.route("/admin/settings", methods=["POST"])
# @admin_required()
# def update_settings():
#     global mock_settings_db
#     data = request.get_json()
#     if not data:
#         return jsonify({"error": "Invalid JSON body"}), 400
    
#     if 'maintenance_mode' in data:
#         mock_settings_db['maintenance_mode'] = bool(data['maintenance_mode'])
    
#     if 'api_keys' in data:
#         mock_settings_db['api_keys'].update(data['api_keys'])

#     if 'report_categories' in data:
#         if isinstance(data['report_categories'], list):
#             # Filter out empty lines that might result from splitting
#             mock_settings_db['report_categories'] = [cat for cat in data['report_categories'] if cat.strip()]

#     return jsonify({"message": "Settings updated successfully", "settings": mock_settings_db})

# @admin_bp.route("/admin/users", methods=["GET"])
# @admin_required()
# def get_all_users():
#     try:
#         users = User.query.all()
#         return jsonify([user.to_dict() for user in users]), 200
#     except Exception as e:
#         print(f"Error in /admin/users: {e}")
#         traceback.print_exc()
#         return jsonify({"status": "error", "message": str(e)}), 500

# @admin_bp.route("/admin/users", methods=["POST"])
# @admin_required()
# def create_admin_user():
#     data = request.get_json()
#     username = data.get('username')
#     password = data.get('password')
#     if not username or not password:
#         return jsonify({'error': 'Username and password are required'}), 400
#     if User.query.filter_by(username=username).first():
#         return jsonify({'error': 'User already exists'}), 400
#     new_admin = User(username=username, role='admin')
#     new_admin.set_password(password)
#     db.session.add(new_admin)
#     db.session.commit()
#     return jsonify({'message': f"Admin user '{username}' created successfully.", "user": new_admin.to_dict()}), 201

# @admin_bp.route("/admin/users/<int:user_id>", methods=["DELETE"])
# @admin_required()
# def delete_user(user_id):
#     try:
#         user_to_delete = User.query.get(user_id)
#         if not user_to_delete:
#             return jsonify({"error": "User not found"}), 404
#         db.session.delete(user_to_delete)
#         db.session.commit()
#         return jsonify({"message": f"User with ID {user_id} has been deleted."}), 200
#     except Exception as e:
#         db.session.rollback()
#         print(f"Error deleting user {user_id}: {e}")
#         traceback.print_exc()
#         return jsonify({"status": "error", "message": str(e)}), 500

# app/api/admin_routes.py (Complete, Updated File)

from flask import Blueprint, jsonify, request
from app.models.models import Report, User
from app.utils.decorators import admin_required
from app.models import db
from sqlalchemy import func
from datetime import datetime, timedelta
import traceback
import os

admin_bp = Blueprint("admin", __name__)

# --- NEW HELPER FUNCTIONS for Persistent Maintenance Mode ---
MAINTENANCE_FLAG_FILE = 'maintenance.flag'

def _read_maintenance_status():
    """Reads the maintenance status from the flag file."""
    if os.path.exists(MAINTENANCE_FLAG_FILE):
        with open(MAINTENANCE_FLAG_FILE, 'r') as f:
            status = f.read().strip()
            return status == 'True'
    return False

def _write_maintenance_status(status: bool):
    """Writes the maintenance status to the flag file."""
    with open(MAINTENANCE_FLAG_FILE, 'w') as f:
        f.write(str(status))

# --- END NEW HELPER FUNCTIONS ---


# Initialize the mock DB, now reading the persistent maintenance status
mock_settings_db = {
    "maintenance_mode": _read_maintenance_status(), # MODIFIED LINE
    "api_keys": {
        "openai": "sk-...",
        "google_gemini": "AIza...",
        "openrouter": "sk-or-v1..."
    },
    "report_categories": [
        "Online Financial Fraud",
        "Cyber Harassment",
        "Cyber Crime Against Women",
        "Hacking/Unauthorized Access",
        "Cryptocurrency Scam"
    ]
}

@admin_bp.route("/admin/all-reports", methods=["GET"])
@admin_required()
def get_all_reports():
    try:
        reports = Report.query.order_by(Report.created_at.desc()).all()
        all_reports_data = [report.to_dict() for report in reports]
        return jsonify({
            "status": "success",
            "total_reports": len(all_reports_data),
            "reports": all_reports_data
        }), 200
    except Exception as e:
        print(f"Error in /admin/all-reports: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@admin_bp.route("/admin/report-analytics", methods=["GET"])
@admin_required()
def get_report_analytics():
    try:
        period = request.args.get('period', '7d')
        today = datetime.utcnow().date()
        if period == 'today':
            start_date = today
        elif period == '30d':
            start_date = today - timedelta(days=29)
        elif period == 'this_month':
            start_date = today.replace(day=1)
        else:
            start_date = today - timedelta(days=6)
        end_date = today + timedelta(days=1)
        date_labels = []
        current_date = start_date
        while current_date < end_date:
            date_labels.append(current_date)
            current_date += timedelta(days=1)
        formatted_labels = [d.strftime('%b %d') for d in date_labels]
        total_reports_in_period = db.session.query(Report).filter(
            Report.created_at >= start_date,
            Report.created_at < end_date
        ).count()
        if total_reports_in_period == 0:
            return jsonify({"labels": formatted_labels, "datasets": []})
        top_users_query = db.session.query(
            User.username,
            func.count(Report.id).label('report_count')
        ).join(Report, Report.user_id == User.id).filter(
            Report.created_at >= start_date,
            Report.created_at < end_date
        ).group_by(User.username).order_by(
            func.count(Report.id).desc()
        ).limit(3).all()
        top_user_usernames = [user.username for user in top_users_query]
        daily_counts_query = db.session.query(
            User.username,
            func.date(Report.created_at).label('report_day'),
            func.count(Report.id).label('daily_count')
        ).join(Report, Report.user_id == User.id).filter(
            User.username.in_(top_user_usernames),
            Report.created_at >= start_date,
            Report.created_at < end_date
        ).group_by(User.username, func.date(Report.created_at)).all()
        user_data = {username: {label.strftime('%Y-%m-%d'): 0 for label in date_labels} for username in top_user_usernames}
        for row in daily_counts_query:
            if row.username in user_data:
                if row.report_day:
                    user_data[row.username][row.report_day] = row.daily_count
        datasets = []
        colors = [
            {'border': 'rgba(63, 114, 175, 1)', 'bg': 'rgba(63, 114, 175, 0.3)'},
            {'border': 'rgba(40, 167, 69, 1)', 'bg': 'rgba(40, 167, 69, 0.3)'},
            {'border': 'rgba(253, 126, 20, 1)', 'bg': 'rgba(253, 126, 20, 0.3)'}
        ]
        for i, username in enumerate(top_user_usernames):
            color_pair = colors[i % len(colors)]
            datasets.append({
                "label": username,
                "data": list(user_data[username].values()),
                "borderColor": color_pair['border'],
                "backgroundColor": color_pair['bg'],
                "fill": True,
                "tension": 0.4
            })
        return jsonify({"labels": formatted_labels, "datasets": datasets})
    except Exception as e:
        print(f"Error in /admin/report-analytics: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": "An internal server error occurred while generating analytics."}), 500

@admin_bp.route("/admin/settings", methods=["GET"])
@admin_required()
def get_settings():
    # Make sure the mock DB has the latest from the file before sending to frontend
    mock_settings_db['maintenance_mode'] = _read_maintenance_status()
    return jsonify(mock_settings_db)

def prepend_api_key_to_env(env_var_name, new_key):
    if not new_key:
        return
    env_path = '.env'
    if not os.path.exists(env_path):
        print(f"Warning: .env file not found at {os.path.abspath(env_path)}")
        return
    with open(env_path, 'r') as f:
        lines = f.readlines()
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(env_var_name + "="):
            parts = line.strip().split('=', 1)
            current_values = parts[1] if len(parts) > 1 else ""
            if current_values:
                new_values = f"{new_key},{current_values}"
            else:
                new_values = new_key
            lines[i] = f"{env_var_name}={new_values}\n"
            found = True
            break
    if not found:
        lines.append(f"\n{env_var_name}={new_key}\n")
    with open(env_path, 'w') as f:
        f.writelines(lines)

@admin_bp.route("/admin/settings", methods=["POST"])
@admin_required()
def update_settings():
    global mock_settings_db
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    if 'maintenance_mode' in data:
        is_maintenance = bool(data['maintenance_mode'])
        _write_maintenance_status(is_maintenance) # Persist to file
        mock_settings_db['maintenance_mode'] = is_maintenance # Update in memory
    
    if 'api_keys' in data:
        api_keys = data['api_keys']
        if api_keys.get('google_gemini') and api_keys['google_gemini'] != mock_settings_db['api_keys']['google_gemini']:
             prepend_api_key_to_env('GEMINI_API_KEYS', api_keys['google_gemini'])
        if api_keys.get('openai') and api_keys['openai'] != mock_settings_db['api_keys']['openai']:
             prepend_api_key_to_env('OPENAI_API_KEY', api_keys['openai'])
        if api_keys.get('openrouter') and api_keys['openrouter'] != mock_settings_db['api_keys']['openrouter']:
             prepend_api_key_to_env('OPENROUTER_API_KEY', api_keys['openrouter'])
        mock_settings_db['api_keys'].update(api_keys)

    if 'report_categories' in data:
        if isinstance(data['report_categories'], list):
            mock_settings_db['report_categories'] = [cat for cat in data['report_categories'] if cat.strip()]
            
    return jsonify({"message": "Settings updated. Server restart may be needed for API key changes to take effect."})

@admin_bp.route("/admin/users", methods=["GET"])
@admin_required()
def get_all_users():
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        print(f"Error in /admin/users: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@admin_bp.route("/admin/users", methods=["POST"])
@admin_required()
def create_admin_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'User already exists'}), 400
    new_admin = User(username=username, role='admin')
    new_admin.set_password(password)
    db.session.add(new_admin)
    db.session.commit()
    return jsonify({'message': f"Admin user '{username}' created successfully.", "user": new_admin.to_dict()}), 201

@admin_bp.route("/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required()
def delete_user(user_id):
    try:
        user_to_delete = User.query.get(user_id)
        if not user_to_delete:
            return jsonify({"error": "User not found"}), 404
        db.session.delete(user_to_delete)
        db.session.commit()
        return jsonify({"message": f"User with ID {user_id} has been deleted."}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user {user_id}: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500