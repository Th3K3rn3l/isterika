import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), 'isterika.db')

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_login INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS hysteria_clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                expires_at DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL
            )
        ''')

        # Add expires_at column if it doesn't exist (migration)
        try:
            conn.execute('ALTER TABLE hysteria_clients ADD COLUMN expires_at DATE')
        except:
            pass

        # Add bandwidth columns if they don't exist (migration)
        try:
            conn.execute('ALTER TABLE hysteria_clients ADD COLUMN bandwidth_up TEXT')
        except:
            pass

        try:
            conn.execute('ALTER TABLE hysteria_clients ADD COLUMN bandwidth_down TEXT')
        except:
            pass

        conn.commit()

def get_admin_by_username(username):
    with get_db() as conn:
        cursor = conn.execute('SELECT * FROM admin_users WHERE username = ?', (username,))
        return cursor.fetchone()

def create_admin(username, password_hash):
    with get_db() as conn:
        conn.execute('INSERT INTO admin_users (username, password_hash) VALUES (?, ?)',
                    (username, password_hash))
        conn.commit()

def update_admin_password(username, new_password_hash):
    with get_db() as conn:
        conn.execute('UPDATE admin_users SET password_hash = ?, first_login = 0 WHERE username = ?',
                    (new_password_hash, username))
        conn.commit()

def update_admin_username(old_username, new_username):
    with get_db() as conn:
        conn.execute('UPDATE admin_users SET username = ? WHERE username = ?',
                    (new_username, old_username))
        conn.commit()

def get_all_clients():
    with get_db() as conn:
        cursor = conn.execute('SELECT * FROM hysteria_clients ORDER BY created_at DESC')
        return cursor.fetchall()

def get_client_by_username(username):
    with get_db() as conn:
        cursor = conn.execute('SELECT * FROM hysteria_clients WHERE username = ?', (username,))
        return cursor.fetchone()

def create_client(username, password, expires_at=None, bandwidth_up=None, bandwidth_down=None):
    with get_db() as conn:
        if expires_at:
            conn.execute(
                'INSERT INTO hysteria_clients (username, password, expires_at, bandwidth_up, bandwidth_down) VALUES (?, ?, ?, ?, ?)',
                (username, password, expires_at, bandwidth_up, bandwidth_down)
            )
        else:
            # Default to 30 days from now if not specified
            from datetime import datetime, timedelta
            default_expires = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            conn.execute(
                'INSERT INTO hysteria_clients (username, password, expires_at, bandwidth_up, bandwidth_down) VALUES (?, ?, ?, ?, ?)',
                (username, password, default_expires, bandwidth_up, bandwidth_down)
            )
        conn.commit()

def delete_client(username):
    with get_db() as conn:
        conn.execute('DELETE FROM hysteria_clients WHERE username = ?', (username,))
        conn.commit()

def update_client_expires(username, new_expires_at):
    with get_db() as conn:
        conn.execute('UPDATE hysteria_clients SET expires_at = ? WHERE username = ?',
                    (new_expires_at, username))
        conn.commit()

def update_client_bandwidth(username, bandwidth_up, bandwidth_down):
    """Update bandwidth limits for a client"""
    with get_db() as conn:
        conn.execute(
            'UPDATE hysteria_clients SET bandwidth_up = ?, bandwidth_down = ? WHERE username = ?',
            (bandwidth_up, bandwidth_down, username)
        )
        conn.commit()

def get_active_clients():
    """Get only clients with valid (not expired) subscriptions"""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    with get_db() as conn:
        cursor = conn.execute(
            'SELECT * FROM hysteria_clients WHERE expires_at >= ? ORDER BY expires_at ASC',
            (today,)
        )
        return cursor.fetchall()

def is_client_active(username):
    """Check if client subscription is still active"""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    with get_db() as conn:
        cursor = conn.execute(
            'SELECT expires_at FROM hysteria_clients WHERE username = ?',
            (username,)
        )
        result = cursor.fetchone()
        if result and result['expires_at']:
            return result['expires_at'] >= today
        return False

def get_setting(key, default=None):
    with get_db() as conn:
        cursor = conn.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        return result['value'] if result else default

def set_setting(key, value):
    with get_db() as conn:
        conn.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        conn.commit()
