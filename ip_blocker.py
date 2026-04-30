"""
IP blocking system for failed login attempts
"""
import time
from typing import Dict, Optional
from datetime import datetime, timedelta

# In-memory storage for failed attempts
# Format: {ip: {'count': int, 'first_attempt': timestamp, 'blocked_until': timestamp}}
failed_attempts: Dict[str, Dict] = {}

# Configuration
MAX_ATTEMPTS = 5  # Maximum failed attempts before blocking
ATTEMPT_WINDOW = 300  # Time window in seconds (5 minutes)
BLOCK_DURATION = 900  # Block duration in seconds (15 minutes)

def record_failed_attempt(ip: str) -> None:
    """Record a failed login attempt for an IP address"""
    current_time = time.time()

    if ip not in failed_attempts:
        failed_attempts[ip] = {
            'count': 1,
            'first_attempt': current_time,
            'blocked_until': None
        }
    else:
        attempt_data = failed_attempts[ip]

        # If blocked period expired, reset
        if attempt_data['blocked_until'] and current_time > attempt_data['blocked_until']:
            failed_attempts[ip] = {
                'count': 1,
                'first_attempt': current_time,
                'blocked_until': None
            }
            return

        # If attempt window expired, reset counter
        if current_time - attempt_data['first_attempt'] > ATTEMPT_WINDOW:
            failed_attempts[ip] = {
                'count': 1,
                'first_attempt': current_time,
                'blocked_until': None
            }
            return

        # Increment counter
        attempt_data['count'] += 1

        # Block if threshold reached
        if attempt_data['count'] >= MAX_ATTEMPTS:
            attempt_data['blocked_until'] = current_time + BLOCK_DURATION

def is_ip_blocked(ip: str) -> bool:
    """Check if an IP address is currently blocked"""
    if ip not in failed_attempts:
        return False

    attempt_data = failed_attempts[ip]

    if not attempt_data['blocked_until']:
        return False

    current_time = time.time()

    # Check if block period expired
    if current_time > attempt_data['blocked_until']:
        # Clean up expired block
        del failed_attempts[ip]
        return False

    return True

def get_block_time_remaining(ip: str) -> Optional[int]:
    """Get remaining block time in seconds for an IP"""
    if ip not in failed_attempts:
        return None

    attempt_data = failed_attempts[ip]

    if not attempt_data['blocked_until']:
        return None

    current_time = time.time()
    remaining = int(attempt_data['blocked_until'] - current_time)

    return remaining if remaining > 0 else None

def clear_failed_attempts(ip: str) -> None:
    """Clear failed attempts for an IP (called on successful login)"""
    if ip in failed_attempts:
        del failed_attempts[ip]

def get_failed_attempts_count(ip: str) -> int:
    """Get number of failed attempts for an IP"""
    if ip not in failed_attempts:
        return 0

    current_time = time.time()
    attempt_data = failed_attempts[ip]

    # Check if attempt window expired
    if current_time - attempt_data['first_attempt'] > ATTEMPT_WINDOW:
        return 0

    return attempt_data['count']

def cleanup_old_entries() -> None:
    """Clean up expired entries from memory"""
    current_time = time.time()
    expired_ips = []

    for ip, data in failed_attempts.items():
        # Remove if block expired or attempt window expired
        if data['blocked_until'] and current_time > data['blocked_until']:
            expired_ips.append(ip)
        elif current_time - data['first_attempt'] > ATTEMPT_WINDOW:
            expired_ips.append(ip)

    for ip in expired_ips:
        del failed_attempts[ip]

def get_all_blocked_ips() -> Dict[str, Dict]:
    """Get all currently blocked IPs with their info"""
    current_time = time.time()
    blocked = {}

    for ip, data in failed_attempts.items():
        if data['blocked_until'] and current_time < data['blocked_until']:
            blocked[ip] = {
                'attempts': data['count'],
                'blocked_until': datetime.fromtimestamp(data['blocked_until']).strftime('%Y-%m-%d %H:%M:%S'),
                'remaining_seconds': int(data['blocked_until'] - current_time)
            }

    return blocked
