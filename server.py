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
    get_private_messages_with_users, save_file_attachment
)

#Create Socket.IO server and attach to aiohttp with CORS settings
sio = socketio.AsyncServer(
    async_mode="aiohttp",
    cors_allowed_origins="*"  # Allow all origins
)
app = web.Application()
sio.attach(app)

# Store connected clients
connected_clients = bidict({})

# Initialize database
init_db()

# Initialize adventure handler
adventure_handler = AdventureHandler(sio, connected_clients)

STATIC_DIR = Path(__file__).with_name("static")

# Serve a basic index page (Lil bit working)
async def index(request):
    return web.FileResponse(STATIC_DIR / "index.html")

async def audio(request):
    return web.FileResponse(STATIC_DIR / "audio.html")

app.router.add_get('/', index)
app.router.add_get("/audio", audio )
app.router.add_get("/video", video )
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
    print("Client connected:", sid)
    await sio.emit("request_username", {}, to=sid)

@sio.event
async def username(sid, data):
    username = data.get("username")
    connected_clients[sid] = username
    
    # Create or get user in database
    user_id = get_or_create_user(username)
    
    print(f"Client {sid} identified as {username}")
    
    # Send chat history to new user
    try:
        global_messages = get_global_messages_with_users(limit=20)
        if global_messages:
            await sio.emit("chat_history", {"messages": global_messages}, to=sid)
    except Exception as e:
        print(f"Error sending chat history: {e}")
    
    # welcome via server_message (unchanged)
    await sio.emit("server_message", 
                   {"text from server": f"Welcome, {username}!"},
                   to=sid)

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

# Join/leave rooms (unchanged)
@sio.event
async def join_room(sid, data):
    room = data.get("room")
    if room:
        await sio.enter_room(sid, room)
        
        # Send room history to newly joined user
        try:
            room_id = get_or_create_room(room)
            room_messages = get_room_messages_with_users(room_id, limit=20)
            if room_messages:
                await sio.emit("room_history", {"room": room, "messages": room_messages}, to=sid)
        except Exception as e:
            print(f"Error sending room history: {e}")

@sio.event
async def leave_room(sid, data):
    room = data.get("room")
    if room:
        await sio.leave_room(sid, room)

# Return rooms joined (unchanged)
@sio.event
async def check_rooms(sid):
    rooms = sio.rooms(sid)
    await sio.emit("room_list", {"rooms": list(rooms)}, to=sid)

# Get chat history
@sio.event
async def get_chat_history(sid):
    try:
        global_messages = get_global_messages_with_users(limit=50)
        await sio.emit("chat_history", {"messages": global_messages}, to=sid)
    except Exception as e:
        print(f"Error sending chat history: {e}")
        await sio.emit("server_message", {"text from server": "Error retrieving chat history"}, to=sid)

# Room broadcast
@sio.event
async def room_message(sid, data):
    sender = connected_clients.get(sid, "Unknown")
    room = data.get("receiver_name")
    if not room:
        await sio.emit("server_message",
                       {"text from server": "Room not specified!"},
                       to=sid)
        return

    # Verify membership
    if room not in sio.rooms(sid):
        await sio.emit("server_message",
                       {"text from server": f"You are not in room '{room}'. Use /join {room} first."},
                       to=sid)
        return

    msg_type = data.get("type", "")
    content = data.get("data", "")
    ts = data.get("timestamp", "")
    envelope = wrap_message(sender, room, msg_type, content, ts)
    
    # Save to database
    try:
        user_id = get_or_create_user(sender)
        room_id = get_or_create_room(room)
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

# Client disconnects
@sio.event
async def disconnect(sid):
    print("Client disconnected:", sid)
    connected_clients.pop(sid, None)

    if sid in connected_clients:
        await adventure_handler.cleanup_on_disconnect(sid)
        del connected_clients[sid]

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
