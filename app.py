from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import psutil
import threading
import database
import auth
import hysteria
import csrf_protection
import ip_blocker

app = Flask(__name__)

database.init_db()

# Get or generate persistent secret key
flask_secret_key = database.get_setting('flask_secret_key')
if not flask_secret_key:
    import secrets
    flask_secret_key = secrets.token_urlsafe(32)
    database.set_setting('flask_secret_key', flask_secret_key)
    print("Generated new Flask secret key")
app.secret_key = flask_secret_key

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Get or generate secret path
SECRET_PATH = database.get_setting('secret_path')
if not SECRET_PATH:
    import secrets
    SECRET_PATH = secrets.token_urlsafe(16)
    database.set_setting('secret_path', SECRET_PATH)
    print(f"Generated secret path: /{SECRET_PATH}")
else:
    print(f"Loaded secret path: /{SECRET_PATH}")

# Store SECRET_PATH in app config for use in decorators
app.config['SECRET_PATH'] = SECRET_PATH

# WSGI Middleware to strip secret path BEFORE Flask routing
class SecretPathMiddleware:
    def __init__(self, app, secret_path):
        self.app = app
        self.secret_path = secret_path

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '/')

        # Allow static files and API without secret path
        if path.startswith('/static/') or path.startswith('/api/'):
            return self.app(environ, start_response)

        # Check if path starts with secret
        if not path.startswith(f'/{self.secret_path}'):
            start_response('404 Not Found', [('Content-Type', 'text/html')])
            return [b'<!doctype html><html lang=en><title>404 Not Found</title><h1>Not Found</h1><p>The requested URL was not found on the server.</p>']

        # Strip secret path from URL
        new_path = path[len(f'/{self.secret_path}'):]
        if not new_path:
            new_path = '/'
        environ['PATH_INFO'] = new_path

        return self.app(environ, start_response)

# Wrap app with middleware
app.wsgi_app = SecretPathMiddleware(app.wsgi_app, SECRET_PATH)

# Context processor to add secret path and CSRF token to all templates
@app.context_processor
def inject_secret_path():
    return {
        'SECRET_PATH': SECRET_PATH,
        'csrf_token': csrf_protection.generate_csrf_token
    }

# Custom url_for that includes secret path
@app.template_global()
def secret_url_for(endpoint, **values):
    return f'/{SECRET_PATH}{url_for(endpoint, **values)}'

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(f'/{SECRET_PATH}/dashboard')
    return redirect(f'/{SECRET_PATH}/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    client_ip = get_remote_address()

    # Check if IP is blocked
    if ip_blocker.is_ip_blocked(client_ip):
        remaining = ip_blocker.get_block_time_remaining(client_ip)
        minutes = remaining // 60
        seconds = remaining % 60
        error_msg = f'Too many failed attempts. Your IP is blocked for {minutes}m {seconds}s'
        return render_template('login.html', error=error_msg), 403

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = auth.authenticate_user(username, password)
        if user:
            # Clear failed attempts on successful login
            ip_blocker.clear_failed_attempts(client_ip)
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(f'/{SECRET_PATH}/dashboard')
        else:
            # Record failed attempt
            ip_blocker.record_failed_attempt(client_ip)
            attempts_left = ip_blocker.MAX_ATTEMPTS - ip_blocker.get_failed_attempts_count(client_ip)

            if attempts_left > 0:
                error_msg = f'Неверное имя пользователя или пароль. Осталось попыток: {attempts_left}'
            else:
                error_msg = 'Too many failed attempts. Your IP has been blocked for 15 minutes'

            return render_template('login.html', error=error_msg)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(f'/{SECRET_PATH}/login')

@app.route('/dashboard')
@auth.login_required
def dashboard():
    user = database.get_admin_by_username(session['username'])
    return render_template('dashboard_v2.html', first_login=user['first_login'] if user else 0)

@app.route('/users')
@auth.login_required
def users():
    return render_template('users.html')

@app.route('/settings')
@auth.login_required
def settings():
    return render_template('settings.html')

@app.route('/api/settings/password', methods=['POST'])
@auth.login_required
@csrf_protection.csrf_protect
def api_change_password():
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({'error': 'All fields required'}), 400

    user = database.get_admin_by_username(session['username'])
    if not auth.check_password(current_password, user['password_hash']):
        return jsonify({'error': 'Current password incorrect'}), 400

    new_hash = auth.hash_password(new_password)
    database.update_admin_password(session['username'], new_hash)

    return jsonify({'success': True})

@app.route('/api/settings/username', methods=['POST'])
@auth.login_required
@csrf_protection.csrf_protect
def api_change_username():
    data = request.json
    new_username = data.get('new_username')
    password = data.get('password')

    if not new_username or not password:
        return jsonify({'error': 'All fields required'}), 400

    user = database.get_admin_by_username(session['username'])
    if not auth.check_password(password, user['password_hash']):
        return jsonify({'error': 'Password incorrect'}), 400

    if database.get_admin_by_username(new_username):
        return jsonify({'error': 'Username already exists'}), 400

    database.update_admin_username(session['username'], new_username)
    session['username'] = new_username

    return jsonify({'success': True})

@app.route('/api/settings/secret-path', methods=['POST'])
@auth.login_required
@csrf_protection.csrf_protect
def api_change_secret_path():
    data = request.json
    new_path = data.get('new_path')
    password = data.get('password')

    if not new_path or not password:
        return jsonify({'error': 'All fields required'}), 400

    user = database.get_admin_by_username(session['username'])
    if not auth.check_password(password, user['password_hash']):
        return jsonify({'error': 'Password incorrect'}), 400

    # Validate path format (alphanumeric, dash, underscore)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', new_path):
        return jsonify({'error': 'Invalid path format. Use only letters, numbers, dash, and underscore'}), 400

    database.set_setting('secret_path', new_path)

    # Note: SECRET_PATH change requires application restart to take effect
    # The middleware is initialized at startup with the old path
    return jsonify({
        'success': True,
        'new_url': f'/{new_path}',
        'warning': 'Please restart the application for the new secret path to take effect'
    })

@app.route('/api/settings/secret-path', methods=['GET'])
@auth.login_required
def api_get_secret_path():
    return jsonify({'secret_path': SECRET_PATH})

@app.route('/api/security/blocked-ips', methods=['GET'])
@auth.login_required
def api_get_blocked_ips():
    """Get list of currently blocked IPs"""
    blocked_ips = ip_blocker.get_all_blocked_ips()
    return jsonify(blocked_ips)

@app.route('/api/stats')
@auth.login_required
def api_stats():
    from datetime import datetime

    # Get all clients
    clients = database.get_all_clients()
    total_clients = len(clients)

    # Count active clients (not expired)
    today = datetime.now().strftime('%Y-%m-%d')
    active_clients = sum(1 for c in clients if c['expires_at'] >= today)

    # Calculate total traffic (network I/O)
    net_io = psutil.net_io_counters()
    total_bytes = net_io.bytes_sent + net_io.bytes_recv
    total_traffic_gb = round(total_bytes / (1024**3), 2)

    return jsonify({
        'total_clients': total_clients,
        'active_clients': active_clients,
        'total_traffic': f'{total_traffic_gb} GB'
    })

# Store speedtest results in memory
speedtest_results = {'download': None, 'upload': None, 'running': False, 'error': None}
speedtest_lock = threading.Lock()

def run_speedtest_download():
    """Background thread for download speedtest"""
    global speedtest_results
    try:
        import speedtest
        st = speedtest.Speedtest()
        st.get_best_server()
        download = st.download() / 1_000_000

        with speedtest_lock:
            speedtest_results['download'] = round(download, 2)
    except Exception as e:
        with speedtest_lock:
            speedtest_results['error'] = str(e)

def run_speedtest_upload():
    """Background thread for upload speedtest"""
    global speedtest_results
    try:
        import speedtest
        st = speedtest.Speedtest()
        st.get_best_server()
        upload = st.upload() / 1_000_000

        with speedtest_lock:
            speedtest_results['upload'] = round(upload, 2)
            speedtest_results['running'] = False
    except Exception as e:
        with speedtest_lock:
            speedtest_results['error'] = str(e)
            speedtest_results['running'] = False

@app.route('/api/speedtest', methods=['POST'])
@auth.login_required
def api_speedtest():
    global speedtest_results

    with speedtest_lock:
        if speedtest_results['running']:
            return jsonify({'success': False, 'error': 'Speedtest already running'}), 429

        # Reset results
        speedtest_results = {'download': None, 'upload': None, 'running': True, 'error': None}

    # Start download test in background
    thread = threading.Thread(target=run_speedtest_download, daemon=True)
    thread.start()

    return jsonify({'success': True, 'message': 'Speedtest started'})

@app.route('/api/speedtest/status', methods=['GET'])
@auth.login_required
def api_speedtest_status():
    with speedtest_lock:
        return jsonify({
            'running': speedtest_results['running'],
            'download': speedtest_results['download'],
            'upload': speedtest_results['upload'],
            'error': speedtest_results['error']
        })

@app.route('/api/speedtest/upload', methods=['POST'])
@auth.login_required
def api_speedtest_upload():
    with speedtest_lock:
        if speedtest_results['running']:
            return jsonify({'success': False, 'error': 'Speedtest already running'}), 429
        if speedtest_results['download'] is None:
            return jsonify({'success': False, 'error': 'Run download test first'}), 400

        speedtest_results['running'] = True

    # Start upload test in background
    thread = threading.Thread(target=run_speedtest_upload, daemon=True)
    thread.start()

    return jsonify({'success': True, 'message': 'Upload test started'})

@app.route('/api/server/status')
@auth.login_required
def api_server_status():
    return jsonify(hysteria.get_service_status())

@app.route('/api/server/restart', methods=['POST'])
@auth.login_required
@csrf_protection.csrf_protect
def api_server_restart():
    success = hysteria.restart_service()
    return jsonify({'success': success})

@app.route('/api/clients')
@auth.login_required
def api_clients():
    clients = database.get_all_clients()
    return jsonify([dict(c) for c in clients])

@app.route('/api/clients', methods=['POST'])
@auth.login_required
@csrf_protection.csrf_protect
def api_add_client():
    data = request.json
    username = data.get('username')
    expires_at = data.get('expires_at')

    if not username:
        return jsonify({'error': 'Username required'}), 400

    if not expires_at:
        return jsonify({'error': 'Expiration date required'}), 400

    if database.get_client_by_username(username):
        return jsonify({'error': 'User already exists'}), 400

    password = hysteria.generate_password()

    # Add user to Hysteria config without bandwidth limits
    hysteria.add_user(username, password)

    # Save to database
    database.create_client(username, password, expires_at, None, None)

    hysteria.restart_service()

    return jsonify({'success': True, 'username': username})

@app.route('/api/clients/<username>', methods=['DELETE'])
@auth.login_required
@csrf_protection.csrf_protect
def api_delete_client(username):
    hysteria.remove_user(username)
    database.delete_client(username)

    hysteria.restart_service()

    return jsonify({'success': True})

@app.route('/api/clients/<username>/expires', methods=['PUT'])
@auth.login_required
@csrf_protection.csrf_protect
def api_update_client_expires(username):
    data = request.json
    new_expires = data.get('expires_at')

    if not new_expires:
        return jsonify({'error': 'Expiration date required'}), 400

    # Update expiration date in database
    database.update_client_expires(username, new_expires)

    # Check if subscription is now active (not expired)
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')

    if new_expires >= today:
        # Subscription is active - ensure user is in Hysteria config
        client = database.get_client_by_username(username)
        if client:
            # Add user to Hysteria config (will update if already exists)
            hysteria.add_user(username, client['password'], client.get('bandwidth_up'), client.get('bandwidth_down'))
            hysteria.restart_service()

    return jsonify({'success': True})

@app.route('/api/clients/<username>/bandwidth', methods=['PUT'])
@auth.login_required
@csrf_protection.csrf_protect
def api_update_client_bandwidth(username):
    data = request.json
    bandwidth_up = data.get('bandwidth_up')
    bandwidth_down = data.get('bandwidth_down')

    # Update bandwidth in database
    database.update_client_bandwidth(username, bandwidth_up, bandwidth_down)

    # Update Hysteria config
    client = database.get_client_by_username(username)
    if client:
        hysteria.add_user(username, client['password'], bandwidth_up, bandwidth_down)
        hysteria.restart_service()

    return jsonify({'success': True})

@app.route('/api/clients/<username>/share')
@auth.login_required
def api_client_share(username):
    link = hysteria.generate_share_link(username)
    if link:
        return jsonify({'link': link})
    return jsonify({'error': 'Could not generate link'}), 500

@app.route('/api/clients/<username>/qr')
@auth.login_required
def api_client_qr(username):
    import qrcode
    import io
    import base64

    link = hysteria.generate_share_link(username)
    if not link:
        return jsonify({'error': 'Could not generate link'}), 500

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return jsonify({
        'qr': f'data:image/png;base64,{img_base64}',
        'link': link
    })

if __name__ == '__main__':
    import os
    import glob

    # Try to find Hysteria SSL certificates in ACME directory
    cert_file = None
    key_file = None

    acme_base = '/var/lib/hysteria/acme/certificates'

    if os.path.exists(acme_base):
        # Find certificate files recursively
        for root, dirs, files in os.walk(acme_base):
            for file in files:
                if file.endswith('.crt'):
                    cert_file = os.path.join(root, file)
                    # Look for corresponding key file
                    key_file = cert_file.replace('.crt', '.key')
                    if os.path.exists(key_file):
                        break
            if cert_file and key_file:
                break

    # Run with SSL if certificates found, otherwise HTTP
    if cert_file and key_file and os.path.exists(cert_file) and os.path.exists(key_file):
        print(f"Starting with SSL")
        print(f"Certificate: {cert_file}")
        print(f"Key: {key_file}")
        app.run(host='0.0.0.0', port=8443, debug=False, ssl_context=(cert_file, key_file))
    else:
        print("SSL certificates not found, starting without SSL on port 8080")
        app.run(host='0.0.0.0', port=8080, debug=False)

