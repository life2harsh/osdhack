-- SQLite schema for chat, BBS, and adventure system

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    useruid TEXT UNIQUE NOT NULL,
    firstname TEXT,
    lastname TEXT,
    avatar TEXT,
    email TEXT UNIQUE,
    password_hash TEXT,
    is_anonymous BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inboxuid TEXT UNIQUE NOT NULL,
    last_message TEXT,
    last_sent_user_id INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS inbox_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inbox_uid TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inbox_uid TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id),
    message TEXT NOT NULL,
    file_id INTEGER REFERENCES file_attachments(id),
    message_type TEXT DEFAULT 'text',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    is_adventure BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS room_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER REFERENCES rooms(id),
    user_id INTEGER REFERENCES users(id),
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS room_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER REFERENCES rooms(id),
    user_id INTEGER REFERENCES users(id),
    message TEXT NOT NULL,
    file_id INTEGER REFERENCES file_attachments(id),
    message_type TEXT DEFAULT 'text',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS adventures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER REFERENCES rooms(id),
    story_title TEXT NOT NULL,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS adventure_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adventure_id INTEGER REFERENCES adventures(id),
    user_id INTEGER REFERENCES users(id),
    role TEXT,
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS adventure_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adventure_id INTEGER REFERENCES adventures(id),
    user_id INTEGER REFERENCES users(id),
    message TEXT NOT NULL,
    file_id INTEGER REFERENCES file_attachments(id),
    message_type TEXT DEFAULT 'text',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS file_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    blob TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS global_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    message TEXT NOT NULL,
    file_id INTEGER REFERENCES file_attachments(id),
    message_type TEXT DEFAULT 'text',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

PRAGMA foreign_keys = ON;

CREATE INDEX IF NOT EXISTS idx_inbox_uid ON inbox_participants(inbox_uid);
CREATE INDEX IF NOT EXISTS idx_room_participants ON room_participants(room_id);
CREATE INDEX IF NOT EXISTS idx_adventure_participants ON adventure_participants(adventure_id);
CREATE INDEX IF NOT EXISTS idx_messages_inbox_uid ON messages(inbox_uid);
