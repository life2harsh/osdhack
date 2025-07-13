import sqlite3
from contextlib import contextmanager
from typing import Optional, Dict, Any
import os
import bcrypt
import uuid

AUTH_DB_PATH = os.path.join(os.path.dirname(__file__), '../auth.sqlite3')

@contextmanager
def get_auth_db():
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_auth_db():
    """Initialize the authentication database"""
    with get_auth_db() as db:
        with open(os.path.join(os.path.dirname(__file__), 'auth_schema.sql'), 'r') as f:
            db.executescript(f.read())

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_user(username: str, email: Optional[str] = None, password: Optional[str] = None, 
                firstname: Optional[str] = None, lastname: Optional[str] = None, 
                is_anonymous: bool = True) -> int:
    """Create a new user in the auth database"""
    with get_auth_db() as db:
        password_hash = hash_password(password) if password else None
        
        cur = db.execute(
            '''INSERT INTO users (useruid, firstname, lastname, email, password_hash, is_anonymous) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            (username, firstname, lastname, email, password_hash, is_anonymous)
        )
        return cur.lastrowid or 0

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email from auth database"""
    with get_auth_db() as db:
        cur = db.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cur.fetchone()
        return dict(row) if row else None

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username from auth database"""
    with get_auth_db() as db:
        cur = db.execute('SELECT * FROM users WHERE useruid = ?', (username,))
        row = cur.fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID from auth database"""
    with get_auth_db() as db:
        cur = db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def update_user_last_seen(user_id: int):
    """Update user's last seen timestamp"""
    with get_auth_db() as db:
        db.execute('UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))

def update_user_profile(user_id: int, firstname: Optional[str] = None, 
                       lastname: Optional[str] = None, avatar: Optional[str] = None):
    """Update user profile information"""
    with get_auth_db() as db:
        updates = []
        params = []
        
        if firstname is not None:
            updates.append('firstname = ?')
            params.append(firstname)
        if lastname is not None:
            updates.append('lastname = ?')
            params.append(lastname)
        if avatar is not None:
            updates.append('avatar = ?')
            params.append(avatar)
        
        if updates:
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            db.execute(query, params)

def change_password(user_id: int, new_password: str) -> bool:
    """Change user's password"""
    try:
        password_hash = hash_password(new_password)
        with get_auth_db() as db:
            db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
        return True
    except Exception as e:
        print(f"Error changing password: {e}")
        return False

def delete_user(user_id: int) -> bool:
    """Delete a user from auth database (soft delete by marking inactive could be better)"""
    try:
        with get_auth_db() as db:
            db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        return True
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False
