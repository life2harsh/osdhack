import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import os

CHAT_DB_PATH = os.path.join(os.path.dirname(__file__), '../chatdb.sqlite3')

@contextmanager
def get_db():
    conn = sqlite3.connect(CHAT_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    """Initialize the chat database"""
    with get_db() as db:
        with open(os.path.join(os.path.dirname(__file__), 'chat_schema.sql'), 'r') as f:
            db.executescript(f.read())

def save_global_message(user_id: int, message: str, message_type: str = 'text', file_id: Optional[int] = None):
    with get_db() as db:
        db.execute(
            'INSERT INTO global_messages (user_id, message, message_type, file_id) VALUES (?, ?, ?, ?)',
            (user_id, message, message_type, file_id)
        )

def save_file_attachment(filename: str, blob: str, file_size: Optional[int] = None, mime_type: Optional[str] = None) -> int:
    """Save file attachment and return file_id"""
    with get_db() as db:
        cur = db.execute(
            'INSERT INTO file_attachments (filename, blob, file_size, mime_type) VALUES (?, ?, ?, ?)',
            (filename, blob, file_size, mime_type)
        )
        return cur.lastrowid or 0

def get_global_messages(limit: int = 50) -> List[Dict[str, Any]]:
    with get_db() as db:
        cur = db.execute(
            'SELECT * FROM global_messages ORDER BY created_at DESC LIMIT ?', (limit,)
        )
        return [dict(row) for row in cur.fetchall()]

def save_room_message(room_id: int, user_id: int, message: str, message_type: str = 'text', file_id: Optional[int] = None):
    with get_db() as db:
        db.execute(
            'INSERT INTO room_messages (room_id, user_id, message, message_type, file_id) VALUES (?, ?, ?, ?, ?)',
            (room_id, user_id, message, message_type, file_id)
        )

def save_private_message(inbox_uid: str, user_id: int, message: str, message_type: str = 'text', file_id: Optional[int] = None):
    with get_db() as db:
        db.execute(
            'INSERT INTO messages (inbox_uid, user_id, message, message_type, file_id) VALUES (?, ?, ?, ?, ?)',
            (inbox_uid, user_id, message, message_type, file_id)
        )

def get_or_create_user(username: str, is_anonymous: bool = True) -> int:
    """Get user ID by username, or create if doesn't exist (chat database only stores basic user info)"""
    with get_db() as db:
        cur = db.execute('SELECT id FROM users WHERE useruid = ?', (username,))
        row = cur.fetchone()
        if row:
            return row['id']
        
        cur = db.execute(
            'INSERT INTO users (useruid, is_anonymous) VALUES (?, ?)',
            (username, is_anonymous)
        )
        return cur.lastrowid or 0

def get_room_by_name(room_name: str) -> Optional[int]:
    """Get room ID by name, return None if doesn't exist"""
    with get_db() as db:
        cur = db.execute('SELECT id FROM rooms WHERE name = ?', (room_name,))
        row = cur.fetchone()
        return row['id'] if row else None

def create_new_room(room_name: str, description: str = '', is_adventure: bool = False) -> int:
    """Create a new room and return room ID"""
    with get_db() as db:
        cur = db.execute(
            'INSERT INTO rooms (name, description, is_adventure) VALUES (?, ?, ?)',
            (room_name, description, is_adventure)
        )
        return cur.lastrowid or 0

def get_or_create_inbox(user1_id: int, user2_id: int) -> str:
    """Get or create private inbox between two users"""
    # Create a consistent inbox UID regardless of user order
    user_ids = sorted([user1_id, user2_id])
    inbox_uid = f"inbox_{user_ids[0]}_{user_ids[1]}"
    
    with get_db() as db:
        # Check if inbox exists
        cur = db.execute('SELECT inboxuid FROM inbox WHERE inboxuid = ?', (inbox_uid,))
        if cur.fetchone():
            return inbox_uid
        
        # Create new inbox
        db.execute('INSERT INTO inbox (inboxuid) VALUES (?)', (inbox_uid,))
        
        # Add participants
        db.execute('INSERT INTO inbox_participants (inbox_uid, user_id) VALUES (?, ?)', (inbox_uid, user1_id))
        db.execute('INSERT INTO inbox_participants (inbox_uid, user_id) VALUES (?, ?)', (inbox_uid, user2_id))
        
        return inbox_uid

def add_user_to_room(user_id: int, room_id: int):
    """Add user to room"""
    with get_db() as db:
        # Check if already in room
        cur = db.execute(
            'SELECT 1 FROM room_participants WHERE user_id = ? AND room_id = ?',
            (user_id, room_id)
        )
        if not cur.fetchone():
            db.execute(
                'INSERT INTO room_participants (user_id, room_id) VALUES (?, ?)',
                (user_id, room_id)
            )

def remove_user_from_room(user_id: int, room_id: int):
    """Remove user from room"""
    with get_db() as db:
        db.execute(
            'DELETE FROM room_participants WHERE user_id = ? AND room_id = ?',
            (user_id, room_id)
        )

def is_user_in_room(user_id: int, room_id: int) -> bool:
    """Check if user is in room"""
    with get_db() as db:
        cur = db.execute(
            'SELECT 1 FROM room_participants WHERE user_id = ? AND room_id = ?',
            (user_id, room_id)
        )
        return cur.fetchone() is not None

def get_global_messages_with_users(limit: int = 50) -> List[Dict[str, Any]]:
    """Get global messages with user information"""
    with get_db() as db:
        cur = db.execute(
            '''SELECT gm.*, u.useruid as username 
               FROM global_messages gm 
               JOIN users u ON gm.user_id = u.id 
               ORDER BY gm.created_at DESC LIMIT ?''',
            (limit,)
        )
        return [dict(row) for row in cur.fetchall()]

def get_room_messages_with_users(room_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get room messages with user information"""
    with get_db() as db:
        cur = db.execute(
            '''SELECT rm.*, u.useruid as username 
               FROM room_messages rm 
               JOIN users u ON rm.user_id = u.id 
               WHERE rm.room_id = ? 
               ORDER BY rm.created_at DESC LIMIT ?''',
            (room_id, limit)
        )
        return [dict(row) for row in cur.fetchall()]

def get_private_messages_with_users(inbox_uid: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get private messages with user information"""
    with get_db() as db:
        cur = db.execute(
            '''SELECT m.*, u.useruid as username 
               FROM messages m 
               JOIN users u ON m.user_id = u.id 
               WHERE m.inbox_uid = ? 
               ORDER BY m.created_at DESC LIMIT ?''',
            (inbox_uid, limit)
        )
        return [dict(row) for row in cur.fetchall()]

def get_adventure_messages_with_users(adventure_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get adventure messages with user information"""
    with get_db() as db:
        cur = db.execute(
            '''SELECT am.*, u.useruid as username 
               FROM adventure_messages am 
               JOIN users u ON am.user_id = u.id 
               WHERE am.adventure_id = ? 
               ORDER BY am.created_at DESC LIMIT ?''',
            (adventure_id, limit)
        )
        return [dict(row) for row in cur.fetchall()]

def get_user_rooms(user_id: int) -> List[Dict[str, Any]]:
    """Get rooms that user is in"""
    with get_db() as db:
        cur = db.execute(
            '''SELECT r.*, rp.joined_at 
               FROM rooms r 
               JOIN room_participants rp ON r.id = rp.room_id 
               WHERE rp.user_id = ?''',
            (user_id,)
        )
        return [dict(row) for row in cur.fetchall()]

def get_user_inboxes(user_id: int) -> List[Dict[str, Any]]:
    """Get inboxes/conversations for user"""
    with get_db() as db:
        cur = db.execute(
            '''SELECT DISTINCT u.useruid as username, u.id as user_id
               FROM inbox_participants ip1
               JOIN inbox_participants ip2 ON ip1.inbox_uid = ip2.inbox_uid
               JOIN users u ON ip2.user_id = u.id
               WHERE ip1.user_id = ? AND ip2.user_id != ?''',
            (user_id, user_id)
        )
        return [dict(row) for row in cur.fetchall()]

def get_undelivered_private_messages(user_id: int) -> List[Dict[str, Any]]:
    """Get private messages sent to user since their last seen time"""
    with get_db() as db:
        # Get user's last seen time
        cur = db.execute('SELECT last_seen FROM users WHERE id = ?', (user_id,))
        user_row = cur.fetchone()
        if not user_row:
            return []
        
        last_seen = user_row['last_seen']
        
        # Get messages in inboxes where user is participant, sent after last_seen
        cur = db.execute(
            '''SELECT m.*, sender.useruid as sender_username
               FROM messages m
               JOIN inbox_participants ip ON m.inbox_uid = ip.inbox_uid
               JOIN users sender ON m.user_id = sender.id
               WHERE ip.user_id = ? 
               AND m.user_id != ?
               AND m.created_at > ?
               ORDER BY m.created_at DESC''',
            (user_id, user_id, last_seen)
        )
        return [dict(row) for row in cur.fetchall()]

def update_user_last_seen(user_id: int):
    """Update user's last seen timestamp"""
    with get_db() as db:
        db.execute('UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))

# Adventure-related functions
def create_adventure(room_id: int, story_title: str, created_by: int) -> int:
    """Create a new adventure"""
    with get_db() as db:
        cur = db.execute(
            'INSERT INTO adventures (room_id, story_title, created_by) VALUES (?, ?, ?)',
            (room_id, story_title, created_by)
        )
        return cur.lastrowid or 0

def add_adventure_participant(adventure_id: int, user_id: int, role: str = 'player'):
    """Add participant to adventure"""
    with get_db() as db:
        db.execute(
            'INSERT INTO adventure_participants (adventure_id, user_id, role) VALUES (?, ?, ?)',
            (adventure_id, user_id, role)
        )

def save_adventure_message(adventure_id: int, user_id: int, message: str, message_type: str = 'text', file_id: Optional[int] = None):
    """Save adventure message"""
    with get_db() as db:
        db.execute(
            'INSERT INTO adventure_messages (adventure_id, user_id, message, message_type, file_id) VALUES (?, ?, ?, ?, ?)',
            (adventure_id, user_id, message, message_type, file_id)
        )

def get_adventure_by_id(adventure_id: int) -> Optional[Dict[str, Any]]:
    """Get adventure by ID"""
    with get_db() as db:
        cur = db.execute('SELECT * FROM adventures WHERE id = ?', (adventure_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def get_adventure_participants(adventure_id: int) -> List[Dict[str, Any]]:
    """Get adventure participants"""
    with get_db() as db:
        cur = db.execute(
            '''SELECT ap.*, u.useruid as username 
               FROM adventure_participants ap 
               JOIN users u ON ap.user_id = u.id 
               WHERE ap.adventure_id = ?''',
            (adventure_id,)
        )
        return [dict(row) for row in cur.fetchall()]
