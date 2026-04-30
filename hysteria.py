import yaml
import subprocess
import os
from typing import Dict, List, Optional

CONFIG_PATH = '/etc/hysteria/config.yaml'

def read_config() -> Dict:
    if not os.path.exists(CONFIG_PATH):
        return {}

    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f) or {}

def write_config(config: Dict):
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

def ensure_config_complete():
    """Ensure config has all necessary parameters for proper operation"""
    config = read_config()
    updated = False

    # Add bandwidth settings if missing
    if 'bandwidth' not in config:
        config['bandwidth'] = {
            'up': '1 gbps',
            'down': '1 gbps'
        }
        updated = True

    # CRITICAL: Must be false for per-user bandwidth limits to work
    if 'ignoreClientBandwidth' not in config:
        config['ignoreClientBandwidth'] = False
        updated = True
    elif config.get('ignoreClientBandwidth') == True:
        # Force to false if it was set to true
        config['ignoreClientBandwidth'] = False
        updated = True

    # Add other important settings if missing
    if 'disableUDP' not in config:
        config['disableUDP'] = False
        updated = True

    if 'udpIdleTimeout' not in config:
        config['udpIdleTimeout'] = '60s'
        updated = True

    if 'speedTest' not in config:
        config['speedTest'] = False
        updated = True

    if updated:
        write_config(config)

    return updated

def get_users() -> Dict[str, str]:
    config = read_config()
    users = {}
    if 'auth' in config and 'userpass' in config['auth']:
        for username, user_data in config['auth']['userpass'].items():
            # Handle both simple string format and extended dict format
            if isinstance(user_data, str):
                users[username] = user_data
            elif isinstance(user_data, dict) and 'password' in user_data:
                users[username] = user_data['password']
    return users

def add_user(username: str, password: str, bandwidth_up: str = None, bandwidth_down: str = None):
    config = read_config()

    if 'auth' not in config:
        config['auth'] = {'type': 'userpass', 'userpass': {}}

    if 'userpass' not in config['auth']:
        config['auth']['userpass'] = {}

    # If bandwidth limits are specified, use extended format
    if bandwidth_up or bandwidth_down:
        config['auth']['userpass'][username] = {
            'password': password
        }
        # Only add bandwidth if both up and down are specified
        if bandwidth_up and bandwidth_down:
            # Remove 'mbps' suffix if present and convert to proper format
            up_value = bandwidth_up.replace(' mbps', '').strip()
            down_value = bandwidth_down.replace(' mbps', '').strip()

            config['auth']['userpass'][username]['bandwidth'] = {
                'up': f'{up_value} mbps',
                'down': f'{down_value} mbps'
            }
    else:
        # Simple format: just password string
        config['auth']['userpass'][username] = password

    write_config(config)

def remove_user(username: str):
    config = read_config()

    if 'auth' in config and 'userpass' in config['auth']:
        if username in config['auth']['userpass']:
            del config['auth']['userpass'][username]
            write_config(config)
            return True
    return False

def get_user_bandwidth(username: str) -> Dict[str, str]:
    """Get bandwidth limits for a specific user"""
    config = read_config()
    if 'auth' in config and 'userpass' in config['auth']:
        user_data = config['auth']['userpass'].get(username)
        if isinstance(user_data, dict) and 'bandwidth' in user_data:
            return user_data['bandwidth']
    return None

def get_service_status() -> Dict:
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'hysteria-server.service'],
            capture_output=True,
            text=True,
            timeout=5
        )
        active = result.stdout.strip() == 'active'

        result = subprocess.run(
            ['systemctl', 'is-enabled', 'hysteria-server.service'],
            capture_output=True,
            text=True,
            timeout=5
        )
        enabled = result.stdout.strip() == 'enabled'

        return {
            'active': active,
            'enabled': enabled,
            'status': 'running' if active else 'stopped'
        }
    except Exception as e:
        return {
            'active': False,
            'enabled': False,
            'status': 'error',
            'error': str(e)
        }

def restart_service() -> bool:
    try:
        subprocess.run(
            ['systemctl', 'restart', 'hysteria-server.service'],
            check=True,
            timeout=10
        )
        return True
    except Exception:
        return False

def generate_share_link(username: str) -> Optional[str]:
    try:
        config = read_config()

        users = get_users()
        if username not in users:
            return None

        password = users[username]

        # Get domain from config
        if 'acme' not in config or 'domains' not in config['acme']:
            return None

        domain = config['acme']['domains'][0] if config['acme']['domains'] else None
        if not domain:
            return None

        # Create temporary client config for hysteria share command
        # Format according to official guide: server and auth fields only
        import tempfile
        client_config = {
            'server': f'{domain}:443',
            'auth': f'{username}:{password}'
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(client_config, f, default_flow_style=False)
            temp_config_path = f.name

        try:
            # Use hysteria share command to generate proper link
            result = subprocess.run(
                ['/usr/local/bin/hysteria', 'share', '-c', temp_config_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                link = result.stdout.strip()
                return link
            else:
                return None
        finally:
            # Clean up temp file
            os.unlink(temp_config_path)

    except Exception:
        return None

def generate_password() -> str:
    try:
        result = subprocess.run(
            ['pwgen', '40', '1'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception:
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(40))
