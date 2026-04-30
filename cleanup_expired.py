#!/usr/bin/env python3
"""
Cleanup expired Hysteria users
Runs as a cron job to automatically block users with expired subscriptions
Users remain in database but are removed from Hysteria config
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
import hysteria

def cleanup_expired_users():
    """Remove expired users from Hysteria config (but keep in database)"""
    today = datetime.now().strftime('%Y-%m-%d')

    # Get all clients
    clients = database.get_all_clients()

    expired_users = []
    for client in clients:
        if client['expires_at'] < today:
            expired_users.append(client['username'])

    if not expired_users:
        print(f"[{datetime.now()}] No expired users found")
        return

    print(f"[{datetime.now()}] Found {len(expired_users)} expired users: {', '.join(expired_users)}")

    # Remove from Hysteria config only (keep in database)
    for username in expired_users:
        try:
            # Remove from Hysteria config
            hysteria.remove_user(username)
            print(f"  - Blocked {username} (removed from Hysteria config)")
        except Exception as e:
            print(f"  - Error blocking {username}: {e}")

    # Restart Hysteria service to apply changes
    if expired_users:
        print(f"[{datetime.now()}] Restarting Hysteria service...")
        if hysteria.restart_service():
            print(f"[{datetime.now()}] Hysteria service restarted successfully")
        else:
            print(f"[{datetime.now()}] Failed to restart Hysteria service")

if __name__ == '__main__':
    cleanup_expired_users()
