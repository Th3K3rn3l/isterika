import bcrypt
from functools import wraps
from flask import session, redirect
import database

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Import here to avoid circular import
            from flask import current_app
            secret_path = current_app.config.get('SECRET_PATH', '')
            return redirect(f'/{secret_path}/login')
        return f(*args, **kwargs)
    return decorated_function

def authenticate_user(username, password):
    user = database.get_admin_by_username(username)
    if user and check_password(password, user['password_hash']):
        return user
    return None
