
# from flask import Blueprint, request, jsonify
# from app import db
# from app.models import User
# from flask_jwt_extended import create_access_token
# from datetime import timedelta

# auth = Blueprint('auth', __name__)

# # Register
# @auth.route('/register', methods=['POST'])
# def register():
#     data = request.get_json()
#     username = data.get('username')
#     password = data.get('password')

#     if not username or not password:
#         return jsonify({'error': 'Username and password are required'}), 400

#     if User.query.filter_by(username=username).first():
#         return jsonify({'error': 'User already exists'}), 400

#     new_user = User(username=username)
#     new_user.set_password(password)
#     db.session.add(new_user)
#     db.session.commit()

#     return jsonify({'message': 'User registered successfully'}), 201

# # Login
# @auth.route('/login', methods=['POST'])
# def login():
#     data = request.get_json()
#     username = data.get('username')
#     password = data.get('password')

#     user = User.query.filter_by(username=username).first()
#     if user and user.check_password(password):
#         # --- MODIFICATION START ---
#         # Create a dictionary of claims to add to the JWT
#         additional_claims = {"role": user.role}
        
#         # Pass the claims to the create_access_token function
#         access_token = create_access_token(
#             identity=str(user.id), 
#             expires_delta=timedelta(hours=1),
#             additional_claims=additional_claims
#         )
#         # --- MODIFICATION END ---
        
#         return jsonify({'access_token': access_token}), 200

#     return jsonify({'error': 'Invalid username or password'}), 401
# justiceassist/app/routes/auth_routes.py



from flask import Blueprint, request, jsonify
from app.models import db
from app.models.models import User
from flask_jwt_extended import create_access_token
from datetime import timedelta
# --- REMOVED: CORS and re imports are no longer needed here ---
# from flask_cors import CORS
# import re
# ------------------------------------------------------------

auth = Blueprint('auth', __name__)

# --- REMOVED: The local, blueprint-specific CORS configuration is now handled globally ---
# dev_origins_regex = re.compile(r".*")
# CORS(auth, origins=dev_origins_regex, supports_credentials=True)
# --------------------------------------------------------------------------------------

@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'User already exists'}), 400
    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201
@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role_from_request = data.get('role')
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        if role_from_request == 'admin' and user.role != 'admin':
            return jsonify({'error': 'Insufficient permissions to log in as admin'}), 401
        additional_claims = {"role": user.role}
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=1),
            additional_claims=additional_claims
        )
        return jsonify({'access_token': access_token}), 200
    return jsonify({'error': 'Invalid credentials or insufficient permissions'}), 401