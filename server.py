import asyncio
from aiohttp import web
from bidict import bidict
import socketio
from pathlib import Path
from adventure_handler import AdventureHandler
from persistence.chatdb import (
    init_db, get_or_create_user, get_or_create_room, save_global_message,
    save_room_message, save_private_message, get_or_create_inbox,
    get_global_messages_with_users, get_room_messages_with_users,
    get_private_messages_with_users, save_file_attachment,
    add_user_to_room, remove_user_from_room, get_user_rooms, is_user_in_room
)
from auth import (
    setup_auth, get_current_user, login_handler, register_handler, 
    anonymous_login_handler, logout_handler, status_handler
)

#Create Socket.IO server and attach to aiohttp with CORS settings
sio = socketio.AsyncServer(
    async_mode="aiohttp",
    cors_allowed_origins="*"  # Allow all origins
)
app = web.Application()
sio.attach(app)

# Setup authentication
setup_auth(app)

# Store connected clients and their associated user sessions
connected_clients = bidict({})
client_sessions = {}  # sid -> session data

# Initialize database
init_db()

# Initialize adventure handler
adventure_handler = AdventureHandler(sio, connected_clients)

STATIC_DIR = Path(__file__).with_name("static")

# Serve a basic index page - now check authentication
async def index(request):
    user = await get_current_user(request)
    if not user['is_authenticated']:
        return web.HTTPFound('/login')
    return web.FileResponse(STATIC_DIR / "index.html")

async def audio(request):
    user = await get_current_user(request)
    if not user['is_authenticated']:
        return web.HTTPFound('/login')
    return web.FileResponse(STATIC_DIR / "audio.html")

# Add authentication routes
app.router.add_route('*', '/login', login_handler)
app.router.add_route('*', '/register', register_handler)
app.router.add_post('/anonymous-login', anonymous_login_handler)
app.router.add_post('/logout', logout_handler)
app.router.add_get('/auth/status', status_handler)

app.router.add_get('/', index)
app.router.add_get("/audio", audio)
app.router.add_static("/static/", path=STATIC_DIR, name="static")

@sio.event()
async def signal(sid, data):
    print(f"Signal from {sid}: {data.get('type')}")
    await sio.emit('signal', data, skip_sid=sid)

def wrap_message(sender: str, receiver: str, msg_type: str, content: str, timestamp: str):
    """Helper to build the unified envelope."""
    return {
        "sender_name": sender,
        "receiver_name": receiver,
        "type": msg_type,
        "data": content,
        "timestamp": timestamp
    }

@sio.event
async def connect(sid, environ):
    """Handle client connection - request authentication"""
    print("Client connected:", sid)
    # Send authentication request to client
    await sio.emit("auth_required", {}, to=sid)

@sio.event 
async def authenticate(sid, data):
    """Handle authentication from client with session token or credentials"""
    print(f"Authentication attempt from {sid}")
    
    auth_type = data.get('type', 'session')
    
    if auth_type == 'session':
        # Try to authenticate using session ID from client
        session_id = data.get('session_id')
        if session_id:
            # This would require implementing session token validation
            # For now, we'll use a simpler approach
            pass
    
    # For now, request username as fallback (backward compatibility)
    await sio.emit("request_username", {}, to=sid)

@sio.event
async def set_username(sid, data):
    """Handle username setting (for anonymous users or after login)"""
    username = data.get("username")
    is_anonymous = data.get("is_anonymous", True)
    
    if not username:
        await sio.emit("auth_error", {"error": "Username required"}, to=sid)
        return
    
    connected_clients[sid] = username
    client_sessions[sid] = {
        'username': username,
        'is_anonymous': is_anonymous,
        'is_authenticated': True
    }
    
    # Create or get user in database
    user_id = get_or_create_user(username, is_anonymous=is_anonymous)
    client_sessions[sid]['user_id'] = user_id
    
    print(f"Client {sid} identified as {username} (anonymous: {is_anonymous})")
    
    # Restore user's rooms
    try:
        user_rooms = get_user_rooms(user_id)
        for room_data in user_rooms:
            room_name = room_data['name']
            await sio.enter_room(sid, room_name)
            print(f"Restored {username} to room: {room_name}")
        
        # Send list of restored rooms to client
        if user_rooms:
            room_names = [room['name'] for room in user_rooms]
            await sio.emit("rooms_restored", {"rooms": room_names}, to=sid)
    except Exception as e:
        print(f"Error restoring rooms for {username}: {e}")
    
    # Send chat history to new user
    try:
        global_messages = get_global_messages_with_users(limit=20)
        if global_messages:
            await sio.emit("chat_history", {"messages": global_messages}, to=sid)
    except Exception as e:
        print(f"Error sending chat history: {e}")
    
    # Send welcome message
    await sio.emit("server_message", 
                   {"text from server": f"Welcome, {username}!"},
                   to=sid)
    
    # Send authentication status
    await sio.emit("auth_status", {
        "authenticated": True,
        "username": username,
        "is_anonymous": is_anonymous
    }, to=sid)

# Remove the old username event handler since auth is handled in connect

# Global chat – broadcast to everyone except sender
@sio.event
async def chat_message(sid, data):
    sender = connected_clients.get(sid, "Unknown")
    # client sent: receiver_name="all", type & data & timestamp
    receiver = data.get("receiver_name", "all")
    msg_type = data.get("type", "")
    content = data.get("data", "")
    ts = data.get("timestamp", "")
    envelope = wrap_message(sender, receiver, msg_type, content, ts)
    print("Received:", envelope)
    
    # Save to database
    try:
        user_id = get_or_create_user(sender)
        if msg_type == "text":
            save_global_message(user_id, content, "text")
        elif msg_type == "file":
            # content is a dict with filename and blob
            file_data = content
            filename = file_data.get("filename", "unknown")
            blob = file_data.get("blob", "")
            file_size = len(blob) if blob else 0
            
            file_id = save_file_attachment(filename, blob, file_size)
            save_global_message(user_id, f"[FILE: {filename}]", "file", file_id)
    except Exception as e:
        print(f"Error saving global message: {e}")
    
    # Send to everyone including the sender
    await sio.emit("chat_message", envelope)

# Private message to one user
@sio.event
async def private_message(sid, data):
    sender = connected_clients.get(sid, "Unknown")
    target = data.get("receiver_name")
    if not target:
        return
    # look up their SID
    try:
        target_sid = connected_clients.inverse[target]
    except KeyError:
        return
    msg_type = data.get("type", "")
    content = data.get("data", "")
    ts = data.get("timestamp", "")
    envelope = wrap_message(sender, target, msg_type, content, ts)
    
    # Save to database
    try:
        sender_id = get_or_create_user(sender)
        target_id = get_or_create_user(target)
        inbox_uid = get_or_create_inbox(sender_id, target_id)
        if msg_type == "text":
            save_private_message(inbox_uid, sender_id, content, "text")
        elif msg_type == "file":
            file_data = content
            filename = file_data.get("filename", "unknown")
            blob = file_data.get("blob", "")
            file_size = len(blob) if blob else 0
            
            file_id = save_file_attachment(filename, blob, file_size)
            save_private_message(inbox_uid, sender_id, f"[FILE: {filename}]", "file", file_id)
    except Exception as e:
        print(f"Error saving private message: {e}")
    
    await sio.emit("private_message", envelope, to=target_sid)

# List users (unchanged)
@sio.event
async def get_users(sid):
    user_list = list(connected_clients.values())
    await sio.emit("users_list", {"users": user_list}, to=sid)

# Join/leave rooms with persistence
@sio.event
async def join_room(sid, data):
    room = data.get("room")
    if room:
        username = connected_clients.get(sid)
        if not username:
            await sio.emit("server_message", {"text from server": "Not authenticated"}, to=sid)
            return
        
        # Get user and room IDs
        try:
            user_session = client_sessions.get(sid, {})
            user_id = user_session.get('user_id')
            if not user_id:
                user_id = get_or_create_user(username, is_anonymous=user_session.get('is_anonymous', True))
                client_sessions[sid]['user_id'] = user_id
            
            room_id = get_or_create_room(room)
            
            # Add user to room in database
            add_user_to_room(user_id, room_id)
            
            # Add user to Socket.IO room
            await sio.enter_room(sid, room)
            
            print(f"User {username} joined room {room}")
            
            # Send room history to newly joined user
            room_messages = get_room_messages_with_users(room_id, limit=20)
            if room_messages:
                await sio.emit("room_history", {"room": room, "messages": room_messages}, to=sid)
                
            await sio.emit("server_message", {"text from server": f"Joined room '{room}'"}, to=sid)
            
        except Exception as e:
            print(f"Error joining room {room}: {e}")
            await sio.emit("server_message", {"text from server": f"Error joining room '{room}'"}, to=sid)

@sio.event
async def leave_room(sid, data):
    room = data.get("room")
    if room:
        username = connected_clients.get(sid)
        if not username:
            await sio.emit("server_message", {"text from server": "Not authenticated"}, to=sid)
            return
        
        try:
            user_session = client_sessions.get(sid, {})
            user_id = user_session.get('user_id')
            if not user_id:
                user_id = get_or_create_user(username, is_anonymous=user_session.get('is_anonymous', True))
                client_sessions[sid]['user_id'] = user_id
            
            room_id = get_or_create_room(room)
            
            # Remove user from room in database
            remove_user_from_room(user_id, room_id)
            
            # Remove user from Socket.IO room
            await sio.leave_room(sid, room)
            
            print(f"User {username} left room {room}")
            await sio.emit("server_message", {"text from server": f"Left room '{room}'"}, to=sid)
            
        except Exception as e:
            print(f"Error leaving room {room}: {e}")
            await sio.emit("server_message", {"text from server": f"Error leaving room '{room}'"}, to=sid)

# Return rooms joined from database
@sio.event
async def check_rooms(sid):
    try:
        username = connected_clients.get(sid)
        if not username:
            await sio.emit("room_list", {"rooms": []}, to=sid)
            return
        
        user_session = client_sessions.get(sid, {})
        user_id = user_session.get('user_id')
        if not user_id:
            user_id = get_or_create_user(username, is_anonymous=user_session.get('is_anonymous', True))
            client_sessions[sid]['user_id'] = user_id
        
        user_rooms = get_user_rooms(user_id)
        room_names = [room['name'] for room in user_rooms]
        await sio.emit("room_list", {"rooms": room_names}, to=sid)
    except Exception as e:
        print(f"Error getting rooms for user: {e}")
        await sio.emit("room_list", {"rooms": []}, to=sid)

# Get chat history
@sio.event
async def get_chat_history(sid):
    try:
        global_messages = get_global_messages_with_users(limit=50)
        await sio.emit("chat_history", {"messages": global_messages}, to=sid)
    except Exception as e:
        print(f"Error sending chat history: {e}")
        await sio.emit("server_message", {"text from server": "Error retrieving chat history"}, to=sid)

# Room broadcast with membership verification
@sio.event
async def room_message(sid, data):
    sender = connected_clients.get(sid, "Unknown")
    room = data.get("receiver_name")
    if not room:
        await sio.emit("server_message",
                       {"text from server": "Room not specified!"},
                       to=sid)
        return

    # Verify membership in database
    try:
        user_session = client_sessions.get(sid, {})
        user_id = user_session.get('user_id')
        if not user_id:
            user_id = get_or_create_user(sender, is_anonymous=user_session.get('is_anonymous', True))
            client_sessions[sid]['user_id'] = user_id
        
        room_id = get_or_create_room(room)
        
        if not is_user_in_room(user_id, room_id):
            await sio.emit("server_message",
                           {"text from server": f"You are not in room '{room}'. Use /join {room} first."},
                           to=sid)
            return
            
    except Exception as e:
        print(f"Error checking room membership: {e}")
        await sio.emit("server_message",
                       {"text from server": f"Error accessing room '{room}'"},
                       to=sid)
        return

    msg_type = data.get("type", "")
    content = data.get("data", "")
    ts = data.get("timestamp", "")
    envelope = wrap_message(sender, room, msg_type, content, ts)
    
    # Save to database
    try:
        if msg_type == "text":
            save_room_message(room_id, user_id, content, "text")
        elif msg_type == "file":
            file_data = content
            filename = file_data.get("filename", "unknown")
            blob = file_data.get("blob", "")
            file_size = len(blob) if blob else 0
            
            file_id = save_file_attachment(filename, blob, file_size)
            save_room_message(room_id, user_id, f"[FILE: {filename}]", "file", file_id)
    except Exception as e:
        print(f"Error saving room message: {e}")
    
    # Send to everyone in the room including the sender
    await sio.emit("room_message", envelope, room=room)

# D&D Adventure Events
@sio.event
async def start_adventure(sid, data):
    await adventure_handler.start_adventure(sid, data)

@sio.event
async def join_adventure(sid, data):
    await adventure_handler.join_adventure(sid, data)

@sio.event
async def adventure_message(sid, data):
    await adventure_handler.send_adventure_message(sid, data)

@sio.event
async def get_adventure_info(sid, data):
    await adventure_handler.get_adventure_info(sid, data)

@sio.event
async def get_adventure_info(sid, data):
    await adventure_handler.get_adventure_info(sid, data)

@sio.event
async def get_stats(sid, data):
    await adventure_handler.handle_stats(sid, data)

# Client disconnects
@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    username = connected_clients.pop(sid, "Unknown")
    client_sessions.pop(sid, None)
    print(f"Client {sid} ({username}) disconnected")
    
    # Adventure handler cleanup
    await adventure_handler.cleanup_on_disconnect(sid)

async def send_messages():
    while True:
        msg = await asyncio.to_thread(input)
        if msg.lower() in {"exit", "quit"}:
            print("Server Exiting...")
            # Disconnect all clients
            for sid in list(connected_clients.keys()):
                await sio.disconnect(sid)
            break
        await sio.emit("server_message", {"text from server": msg})


async def on_startup(app):
    # This schedules send_messages() in the background
    sio.start_background_task(send_messages)

app.on_startup.append(on_startup)

#Run the web server
if __name__ == "__main__":
    web.run_app(app, host='127.0.0.1', port=8080)

