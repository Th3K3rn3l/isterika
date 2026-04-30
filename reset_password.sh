#!/bin/bash

cd /opt/isterika
source venv/bin/activate

python3 -c "
import database
import auth

new_password = 'admin123'
password_hash = auth.hash_password(new_password)

with database.get_db() as conn:
    conn.execute('UPDATE admin_users SET password_hash = ? WHERE username = ?', (password_hash, 'admin'))
    conn.commit()

print('Password reset successfully!')
print('Username: admin')
print('Password: admin123')
"
