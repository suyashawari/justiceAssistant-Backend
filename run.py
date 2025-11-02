# from app import create_app, db

# app = create_app()

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)

# justiceassist/run.py
# justiceassist/run.py

from app.models import create_app, db
from app.models.models import User
import click

app = create_app()

# This is your existing admin creation command (it is correct)
@app.cli.command("create-admin")
@click.argument("username")
@click.argument("password")
def create_admin(username, password):
    """Creates a new user with the 'admin' role."""
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print(f"Error: User '{username}' already exists.")
            return

        new_admin = User(username=username, role='admin')
        new_admin.set_password(password)

        db.session.add(new_admin)
        db.session.commit()
        print(f"Admin user '{username}' created successfully.")


# --- NEW COMMAND ADDED HERE ---
@app.cli.command("delete-user")
@click.argument("username")
def delete_user(username):
    """Deletes a user by their username."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            print(f"User '{username}' has been deleted successfully.")
        else:
            print(f"Error: User '{username}' not found.")
# --- END OF NEW COMMAND ---


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)