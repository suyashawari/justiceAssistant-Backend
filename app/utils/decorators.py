# justiceassist/app/utils/decorators.py

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def admin_required():
    """
    A custom decorator that verifies the JWT is present and checks that the
    'role' claim in the token is 'admin'.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # First, verify that a valid JWT is present in the request
            verify_jwt_in_request()
            
            # Get the claims from the access token
            claims = get_jwt()
            
            # Check if the 'role' claim is present and is set to 'admin'
            if claims.get("role") == "admin":
                # If the user is an admin, call the original function
                return fn(*args, **kwargs)
            else:
                # If not an admin, return a forbidden error
                return jsonify(msg="Admins only! Access forbidden."), 403
        return decorator
    return wrapper