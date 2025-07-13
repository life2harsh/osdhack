import asyncio
import time
import threading
import concurrent.futures
from queue import Queue
from aiohttp import web
from bidict import bidict
import socketio
from pathlib import Path
from adventure_handler import AdventureHandler
from topic_analyzer import TopicAnalyzer
from persistence.chatdb import (
    init_db, get_or_create_user, get_room_by_name, create_new_room, save_global_message,
    save_room_message, save_private_message, get_or_create_inbox,
    get_global_messages_with_users, get_room_messages_with_users,
    get_private_messages_with_users, get_adventure_messages_with_users, get_user_inboxes, save_file_attachment,
    add_user_to_room, remove_user_from_room, get_user_rooms, is_user_in_room,
    get_undelivered_private_messages, update_user_last_seen
)
from persistence.authdb import init_auth_db
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

# Background task tracking to prevent spam
background_tasks = {}  # user_id -> last_task_time
BACKGROUND_TASK_COOLDOWN = 0.5  # seconds between background tasks per user

# Track topic notifications to prevent spam
topic_notifications = {}  # (user_id, topic) -> last_notification_time
TOPIC_NOTIFICATION_COOLDOWN = 60.0  # seconds between topic notifications per user per topic

# Thread pool for LLM processing
llm_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="LLM")
topic_analysis_queue = asyncio.Queue(maxsize=100)  # Limit queue size to prevent memory issues

# Initialize databases
init_db()         # Chat database
init_auth_db()    # Authentication database

# Initialize adventure handler
adventure_handler = AdventureHandler(sio, connected_clients)

# Initialize topic analyzer with reduced context
topic_analyzer = TopicAnalyzer(max_history_per_user=5, consecutive_threshold=4)

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
    
    # Check if username is already connected and disconnect the old session
    try:
        if username in connected_clients.inverse:
            old_sid = connected_clients.inverse[username]
            print(f"Username {username} already connected as {old_sid}, disconnecting old session")
            # Clean up old session
            connected_clients.pop(old_sid, None)
            client_sessions.pop(old_sid, None)
            # Disconnect the old session
            await sio.disconnect(old_sid)
    except Exception as e:
        print(f"Error handling duplicate username: {e}")
    
    # Now safely add the new connection
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
    
    # Check for and deliver offline private messages
    try:
        # Get user's last seen timestamp and undelivered messages
        undelivered_messages = get_undelivered_private_messages(user_id)
        if undelivered_messages:
            await sio.emit("server_message", 
                           {"text from server": f"You have {len(undelivered_messages)} undelivered private messages!"},
                           to=sid)
            
            # Send each undelivered message
            for msg in undelivered_messages:
                sender_name = msg.get('sender_username', 'Unknown')
                message_type = msg.get('message_type', 'text')
                
                if message_type == 'file':
                    # Handle file messages
                    file_data = {
                        'filename': msg.get('filename', 'unknown_file'),
                        'blob': msg.get('blob', '')
                    }
                    envelope = {
                        'sender_name': sender_name,
                        'receiver_name': username,
                        'type': 'file',
                        'data': file_data,
                        'timestamp': msg.get('created_at', '')
                    }
                else:
                    # Handle text messages
                    envelope = {
                        'sender_name': sender_name,
                        'receiver_name': username,
                        'type': 'text',
                        'data': msg.get('message', ''),
                        'timestamp': msg.get('created_at', '')
                    }
                
                await sio.emit("private_message", envelope, to=sid)
        
        # Update user's last seen timestamp
        update_user_last_seen(user_id)
        
    except Exception as e:
        print(f"Error delivering offline messages: {e}")
    
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


# Global chat – now with background topic analysis and message copying
@sio.event
async def chat_message(sid, data):
    sender = connected_clients.get(sid, "Unknown")
    msg_type = data.get("type", "")
    content = data.get("data", "")
    ts = data.get("timestamp", "")
    receiver = data.get("receiver_name", "all")

    # Get user session info
    user_session = client_sessions.get(sid, {})
    user_id = user_session.get('user_id')
    if not user_id:
        user_id = get_or_create_user(sender, is_anonymous=user_session.get('is_anonymous', True))
        client_sessions[sid]['user_id'] = user_id

    # ALWAYS send message immediately to global chat first (no delays)
    envelope = wrap_message(sender, receiver, msg_type, content, ts)
    
    if msg_type == "text":
        # Save to global chat immediately
        save_global_message(user_id, content, "text")
        
        # Send to global chat immediately
        await sio.emit("chat_message", envelope)
        
        # Always do topic analysis in background (non-blocking) for every message
        sio.start_background_task(analyze_and_copy_to_topic_room, sid, user_id, sender, content, ts)
        
    else:
        # For files or other types, handle immediately
        try:
            if msg_type == "file":
                file_data = content
                filename = file_data.get("filename", "unknown")
                blob = file_data.get("blob", "")
                file_size = len(blob) if blob else 0
                file_id = save_file_attachment(filename, blob, file_size)
                save_global_message(user_id, f"[FILE: {filename}]", "file", file_id)
        except Exception as e:
            print(f"Error saving global message: {e}")
        
        await sio.emit("chat_message", envelope)

async def analyze_and_copy_to_topic_room(sid, user_id, sender, content, ts):
    """Background task to analyze message and copy to topic room if needed"""
    try:
        # Add to queue for thread processing - non-blocking
        try:
            analysis_task = {
                'sid': sid,
                'user_id': user_id,
                'sender': sender,
                'content': content,
                'timestamp': ts
            }
            topic_analysis_queue.put_nowait(analysis_task)
        except asyncio.QueueFull:
            print(f"[Topic Analysis] Queue full, skipping analysis for {sender}")
            
    except Exception as e:
        print(f"Error queuing topic analysis: {e}")

def run_llm_analysis(task_data):
    """Run LLM analysis in separate thread (synchronous)"""
    loop = None
    try:
        user_id = task_data['user_id']
        content = task_data['content']
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async analysis
        analysis_result = loop.run_until_complete(
            topic_analyzer.analyze_message(str(user_id), content)
        )
        
        return {
            'success': True,
            'result': analysis_result,
            'task_data': task_data
        }
        
    except Exception as e:
        print(f"Error in LLM thread analysis: {e}")
        return {
            'success': False,
            'error': str(e),
            'task_data': task_data
        }
    finally:
        if loop:
            loop.close()

async def process_topic_analysis_queue():
    """Process topic analysis queue in background"""
    while True:
        try:
            # Get task from queue (wait if empty)
            task_data = await topic_analysis_queue.get()
            
            # Submit to thread pool
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(llm_thread_pool, run_llm_analysis, task_data)
            
            # Process result when ready (non-blocking for queue)
            sio.start_background_task(handle_analysis_result, future, task_data)
            
        except Exception as e:
            print(f"Error processing topic analysis queue: {e}")
            await asyncio.sleep(0.1)

async def handle_analysis_result(future, task_data):
    """Handle the result of LLM analysis"""
    try:
        result = await future
        
        if not result['success']:
            print(f"LLM analysis failed: {result.get('error', 'Unknown error')}")
            return
            
        analysis_result = result['result']
        sid = task_data['sid']
        user_id = task_data['user_id']
        sender = task_data['sender']
        content = task_data['content']
        ts = task_data['timestamp']
        
        topic = analysis_result['topic']
        confidence = analysis_result['confidence']
        should_copy = analysis_result['should_move']
        consecutive_count = analysis_result['consecutive_count']
        
        print(f"[LLM Topic Analysis] {sender}: topic={topic}, confidence={confidence:.2f}, consecutive={consecutive_count}, should_copy={should_copy}")

        if should_copy:
            topic_room = f"topic:{topic}"
            
            # Check if topic room exists, else create
            room_id = get_room_by_name(topic_room)
            if not room_id:
                # Create topic room with a detailed description
                description = f"Auto-created room for discussing {topic}. Messages are copied here when users have {topic_analyzer.consecutive_threshold} consecutive messages about {topic}."
                room_id = create_new_room(topic_room, description, is_adventure=False)

            # Auto-join user to topic room if not already in it
            if not is_user_in_room(user_id, room_id):
                add_user_to_room(user_id, room_id)
                await sio.enter_room(sid, topic_room)
                print(f"Auto-joined {sender} to {topic_room}")

            # Copy message to topic room (don't move user, just copy the message)
            save_room_message(room_id, user_id, content, "text")

            # Build envelope for topic room with correct sender name
            envelope = wrap_message(sender, topic_room, "text", content, ts)
            
            # Send to everyone in the topic room EXCEPT the original sender (skip_sid)
            await sio.emit("room_message", envelope, room=topic_room, skip_sid=sid)

            # Only notify user once when they first start talking about a topic or after cooldown
            # Check if this is the first message that triggered the topic copy
            notification_key = (user_id, topic)
            current_time = time.time()
            last_notification = topic_notifications.get(notification_key, 0)
            
            if (consecutive_count == topic_analyzer.consecutive_threshold and 
                current_time - last_notification >= TOPIC_NOTIFICATION_COOLDOWN):
                topic_notifications[notification_key] = current_time
                await sio.emit("server_message", {
                    "text from server": f"🔗 Your messages about {topic} are being copied to {topic_room}"
                }, to=sid)
            
    except Exception as e:
        print(f"Error handling analysis result: {e}")

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

# Create a new room
@sio.event
async def create_room(sid, data):
    room_name = data.get("room_name")
    description = data.get("description", "")
    
    if not room_name:
        await sio.emit("server_message", {"text from server": "Room name required"}, to=sid)
        return
    
    username = connected_clients.get(sid)
    if not username:
        await sio.emit("server_message", {"text from server": "Not authenticated"}, to=sid)
        return
    
    try:
        # Check if room already exists
        if get_room_by_name(room_name):
            await sio.emit("server_message", {"text from server": f"Room '{room_name}' already exists"}, to=sid)
            return
        
        # Create the room
        room_id = create_new_room(room_name, description, is_adventure=False)
        
        # Get user ID
        user_session = client_sessions.get(sid, {})
        user_id = user_session.get('user_id')
        if not user_id:
            user_id = get_or_create_user(username, is_anonymous=user_session.get('is_anonymous', True))
            client_sessions[sid]['user_id'] = user_id
        
        # Add creator to the room
        add_user_to_room(user_id, room_id)
        await sio.enter_room(sid, room_name)
        
        print(f"User {username} created and joined room '{room_name}'")
        await sio.emit("server_message", {"text from server": f"Created and joined room '{room_name}'"}, to=sid)
        
    except Exception as e:
        print(f"Error creating room {room_name}: {e}")
        await sio.emit("server_message", {"text from server": f"Error creating room '{room_name}'"}, to=sid)

# Join/leave rooms with persistence
@sio.event
async def join_room(sid, data):
    room = data.get("room")
    if room:
        username = connected_clients.get(sid)
        if not username:
            await sio.emit("server_message", {"text from server": "Not authenticated"}, to=sid)
            return
        
        # Check if room exists first
        room_id = get_room_by_name(room)
        if not room_id:
            await sio.emit("server_message", {"text from server": f"Room '{room}' does not exist. Use /newroom {room} <description> to create it."}, to=sid)
            return
        
        # Get user and room IDs
        try:
            user_session = client_sessions.get(sid, {})
            user_id = user_session.get('user_id')
            if not user_id:
                user_id = get_or_create_user(username, is_anonymous=user_session.get('is_anonymous', True))
                client_sessions[sid]['user_id'] = user_id
            
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
            
            room_id = get_room_by_name(room)
            if not room_id:
                await sio.emit("server_message", {"text from server": f"Room '{room}' does not exist"}, to=sid)
                return
            
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
        # Send full room information including descriptions
        rooms_with_descriptions = [
            {
                "name": room['name'],
                "description": room['description'] or "No description"
            }
            for room in user_rooms
        ]
        await sio.emit("room_list", {"rooms": rooms_with_descriptions}, to=sid)
    except Exception as e:
        print(f"Error getting rooms for user: {e}")
        await sio.emit("room_list", {"rooms": []}, to=sid)

# Get list of private message conversations
@sio.event
async def get_pm_list(sid):
    """Get list of users that current user has private messages with"""
    try:
        username = connected_clients.get(sid)
        if not username:
            await sio.emit("pm_list", {"conversations": []}, to=sid)
            return
        
        user_session = client_sessions.get(sid, {})
        user_id = user_session.get('user_id')
        if not user_id:
            user_id = get_or_create_user(username, is_anonymous=user_session.get('is_anonymous', True))
            client_sessions[sid]['user_id'] = user_id
        
        conversations = get_user_inboxes(user_id)
        await sio.emit("pm_list", {"conversations": conversations}, to=sid)
    except Exception as e:
        print(f"Error getting PM list for user: {e}")
        await sio.emit("pm_list", {"conversations": []}, to=sid)

# Get chat history
@sio.event
async def get_chat_history(sid, data=None):
    """Get chat history - global, room, or adventure based on parameters"""
    try:
        # If no data provided, get global history (backward compatibility)
        if not data:
            global_messages = get_global_messages_with_users(limit=50)
            await sio.emit("chat_history", {"messages": global_messages, "type": "global"}, to=sid)
            return
        
        history_type = data.get("type", "global")
        target = data.get("target", "")
        limit = data.get("limit", 50)
        
        if history_type == "room":
            # Get room history
            room_id = get_room_by_name(target)
            if not room_id:
                await sio.emit("server_message", {"text from server": f"Room '{target}' not found"}, to=sid)
                return
                
            # Check if user is in the room
            username = connected_clients.get(sid)
            if username:
                user_session = client_sessions.get(sid, {})
                user_id = user_session.get('user_id')
                if user_id and not is_user_in_room(user_id, room_id):
                    await sio.emit("server_message", {"text from server": f"You are not in room '{target}'"}, to=sid)
                    return
            
            room_messages = get_room_messages_with_users(room_id, limit=limit)
            await sio.emit("room_history", {"room": target, "messages": room_messages}, to=sid)
            
        elif history_type == "private" or history_type == "pm":
            # Get private message history
            username = connected_clients.get(sid)
            if not username:
                await sio.emit("server_message", {"text from server": "Not authenticated"}, to=sid)
                return
            
            user_session = client_sessions.get(sid, {})
            user_id = user_session.get('user_id')
            if not user_id:
                user_id = get_or_create_user(username, is_anonymous=user_session.get('is_anonymous', True))
                client_sessions[sid]['user_id'] = user_id
            
            # Get the other user ID
            other_user_id = get_or_create_user(target, is_anonymous=True)
            
            # Get or create inbox between users
            inbox_uid = get_or_create_inbox(user_id, other_user_id)
            
            # Get private messages
            private_messages = get_private_messages_with_users(inbox_uid, limit=limit)
            await sio.emit("private_history", {"username": target, "messages": private_messages}, to=sid)
            
        elif history_type == "adventure":
            # Get adventure history
            try:
                adventure_id = int(target)
                adventure_messages = get_adventure_messages_with_users(adventure_id, limit=limit)
                await sio.emit("adventure_history", {"adventure_id": adventure_id, "messages": adventure_messages}, to=sid)
            except (ValueError, TypeError):
                await sio.emit("server_message", {"text from server": f"Invalid adventure ID: '{target}'"}, to=sid)
                
        else:
            # Default to global history
            global_messages = get_global_messages_with_users(limit=limit)
            await sio.emit("chat_history", {"messages": global_messages, "type": "global"}, to=sid)
            
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
        
        room_id = get_room_by_name(room)
        if not room_id:
            await sio.emit("server_message",
                           {"text from server": f"Room '{room}' does not exist. Use /newroom {room} <description> to create it."},
                           to=sid)
            return
        
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

# Client disconnects
@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    try:
        username = connected_clients.pop(sid, "Unknown")
        client_sessions.pop(sid, None)
        print(f"Client {sid} ({username}) disconnected")
        
        # Adventure handler cleanup
        await adventure_handler.cleanup_on_disconnect(sid)
    except Exception as e:
        print(f"Error during disconnect cleanup for {sid}: {e}")

async def send_messages():
    while True:
        msg = await asyncio.to_thread(input)
        if msg.lower() in {"exit", "quit"}:
            print("Server Exiting...")
            # Clean shutdown
            llm_thread_pool.shutdown(wait=True)
            # Disconnect all clients
            for sid in list(connected_clients.keys()):
                await sio.disconnect(sid)
            break
        await sio.emit("server_message", {"text from server": msg})


async def on_startup(app):
    # Initialize topic analyzer
    await topic_analyzer.initialize()
    # Start the topic analysis queue processor
    sio.start_background_task(process_topic_analysis_queue)
    # This schedules send_messages() in the background
    sio.start_background_task(send_messages)

app.on_startup.append(on_startup)

# Topic-related events
@sio.event
async def get_topic_stats(sid):
    """Get topic statistics for the current user"""
    try:
        user_session = client_sessions.get(sid, {})
        user_id = user_session.get('user_id')
        if not user_id:
            await sio.emit("server_message", {"text from server": "Not authenticated"}, to=sid)
            return
        
        stats = topic_analyzer.get_user_topic_stats(str(user_id))
        if stats:
            await sio.emit("topic_stats", stats, to=sid)
        else:
            await sio.emit("server_message", {"text from server": "No topic statistics available yet"}, to=sid)
    except Exception as e:
        print(f"Error getting topic stats: {e}")
        await sio.emit("server_message", {"text from server": "Error retrieving topic statistics"}, to=sid)

@sio.event
async def join_topic_room(sid, data):
    """Manually join a topic room"""
    topic = data.get("topic")
    if not topic:
        await sio.emit("server_message", {"text from server": "Topic name required"}, to=sid)
        return
    
    username = connected_clients.get(sid)
    if not username:
        await sio.emit("server_message", {"text from server": "Not authenticated"}, to=sid)
        return
    
    try:
        topic_room = f"topic:{topic}"
        
        # Check if topic room exists, else create
        room_id = get_room_by_name(topic_room)
        if not room_id:
            description = f"Topic room for discussing {topic}. Created manually by {username}."
            room_id = create_new_room(topic_room, description, is_adventure=False)
        
        # Get user ID
        user_session = client_sessions.get(sid, {})
        user_id = user_session.get('user_id')
        if not user_id:
            user_id = get_or_create_user(username, is_anonymous=user_session.get('is_anonymous', True))
            client_sessions[sid]['user_id'] = user_id
        
        # Add user to topic room
        add_user_to_room(user_id, room_id)
        await sio.enter_room(sid, topic_room)
        
        await sio.emit("server_message", {"text from server": f"Manually joined {topic_room}"}, to=sid)
        
        # Send room history
        room_messages = get_room_messages_with_users(room_id, limit=20)
        if room_messages:
            await sio.emit("room_history", {"room": topic_room, "messages": room_messages}, to=sid)
            
    except Exception as e:
        print(f"Error joining topic room {topic}: {e}")
        await sio.emit("server_message", {"text from server": f"Error joining topic room '{topic}'"}, to=sid)

@sio.event
async def clear_topic_history(sid):
    """Clear user's topic history (admin function)"""
    try:
        user_session = client_sessions.get(sid, {})
        user_id = user_session.get('user_id')
        if not user_id:
            await sio.emit("server_message", {"text from server": "Not authenticated"}, to=sid)
            return
        
        topic_analyzer.clear_user_history(str(user_id))
        await sio.emit("server_message", {"text from server": "Topic history cleared"}, to=sid)
    except Exception as e:
        print(f"Error clearing topic history: {e}")
        await sio.emit("server_message", {"text from server": "Error clearing topic history"}, to=sid)

#Run the web server
if __name__ == "__main__":
    web.run_app(app, host='127.0.0.1', port=8080)

