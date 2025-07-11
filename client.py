import asyncio
import socketio
import os
import base64
from datetime import datetime, timezone

sio = socketio.AsyncClient()
username = None

def make_payload(receiver: str, content: str, msg_type: str):
    """Build our standard JSON envelope."""
    # Default to text if type is not recognized
    if msg_type.lower() not in ["text", "file"]:
        msg_type = "text"
    
    return {
        "sender_name": username,
        "receiver_name": receiver,
        "type": msg_type.lower(),
        "data": content,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
    }

def make_file_payload(receiver: str, filepath: str):
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"No such file: {filepath}")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        blob = base64.b64encode(f.read()).decode("ascii")
    return {
        "sender_name": username,
        "receiver_name": receiver,
        "type": "file",
        "data": {"filename": filename, "blob": blob},
        "timestamp": datetime.utcnow().isoformat() + "Z"
        }

async def _handle_incoming_file(data):
    info = data["data"]
    filename = info["filename"]
    blob     = info["blob"]
    content  = base64.b64decode(blob)
    save_path = filename
    i = 1
    while os.path.exists(save_path):
        name, ext = os.path.splitext(filename)
        save_path = f"{name}_{i}{ext}"
        i += 1
    with open(save_path, "wb") as f:
        f.write(content)
    print(f"\n[FILE RECEIVED] saved as '{save_path}'")

@sio.event
async def connect():
    print("\n[client] Connected to server")

@sio.event
async def request_username(data):
    global username
    print()
    username = await asyncio.to_thread(input, "Enter your username: ")
    await sio.emit("username", {"username": username})

@sio.event
async def server_message(data):
    print()
    print(f"[SERVER]: {data.get('text from server', '')}")

@sio.event
async def chat_message(data):
    print()
    if data.get("type") == "file":
        await _handle_incoming_file(data)
    else:
        print(f"[{data.get('sender_name','Unknown')}]: {data.get('data','')}")

@sio.event
async def chat_history(data):
    """Handle chat history received from server"""
    print()
    print("=== CHAT HISTORY ===")
    messages = data.get('messages', [])
    for msg in reversed(messages):  # Show oldest first
        username = msg.get('useruid','Unknown')
        if msg.get('message_type') == 'file' and msg.get('filename'):
            print(f"[{username}]: [FILE: {msg.get('filename')}]")
        else:
            print(f"[{username}]: {msg.get('message','')}")
    print("=== END HISTORY ===")

@sio.event
async def room_history(data):
    """Handle room history received from server"""
    room = data.get('room', '')
    print()
    print(f"=== ROOM {room} HISTORY ===")
    messages = data.get('messages', [])
    for msg in reversed(messages):  # Show oldest first
        username = msg.get('useruid','Unknown')
        if msg.get('message_type') == 'file' and msg.get('filename'):
            print(f"[ROOM {room} - {username}]: [FILE: {msg.get('filename')}]")
        else:
            print(f"[ROOM {room} - {username}]: {msg.get('message','')}")
    print("=== END HISTORY ===")

@sio.event
async def private_message(data):
    print()
    if data.get("type") == "file":
        await _handle_incoming_file(data)
    else:
        print(f"[ROOM {data.get('receiver_name','')} - {data.get('sender_name','Unknown')}]: {data.get('data','')}")

@sio.event
async def room_message(data):
    print()
    print(f"[ROOM {data.get('receiver_name','')} - {data.get('sender_name','Unknown')}]: {data.get('data','')}")

@sio.event
async def users_list(data):
    print()
    users = data.get('users', [])
    print(f"[USERS ONLINE]: {users}")

@sio.event
async def room_list(data):
    print()
    rooms = data.get('rooms', [])
    print(f"[ROOMS JOINED]: {', '.join(rooms)}")

@sio.event
async def adventure_invitation(data):
    print()
    room_id = data.get('room_id', '')
    message = data.get('message', '')
    print(f"[ADVENTURE INVITATION] {message}")

@sio.event
async def adventure_message(data):
    print()
    room_id     = data.get('room_id', '')
    sender_name = data.get('sender_name', '')
    sender_role = data.get('sender_role', '')
    message     = data.get('message', '')
    msg_type    = data.get('type', 'message')

    if msg_type in ('join', 'dm_disconnect', 'player_disconnect'):
        print(f"[ADVENTURE {room_id}] ⚠️  {message}")
    else:
        print(f"[ADVENTURE {room_id} - {sender_name} ({sender_role})]: {message}")

@sio.event
async def adventure_info(data):
    print()
    room_id       = data.get('room_id', '')
    story         = data.get('story', '')
    dm            = data.get('dm', '')
    players       = data.get('players', [])
    invited_users = data.get('invited_users', [])

    print(f"[ADVENTURE INFO - {room_id}]")
    print(f"  Story:  {story}")
    print(f"  DM:     {dm}")
    print(f"  Players: {', '.join(players) if players else 'None'}")
    print(f"  Invited: {', '.join(invited_users) if invited_users else 'None'}")

@sio.event
async def disconnect():
    print()
    print("[client] Disconnected from server")

async def send_messages():
    print("Commands:")
    print("  <message>                                 – send text message to global chat")
    print("  text <message>                            – send text message to global chat")
    print("  file <filepath>                           – send file to global chat")
    print("  /users                                    – list users")
    print("  /rooms                                    – list rooms joined")
    print("  /history                                  – get global chat history")
    print("  /pm <user> <type> <message>               – private message")
    print("  /join <room>                              – join a room")
    print("  /leave <room>                             – leave a room")
    print("  /room <room> <type> <message>             – room chat")
    print("  /startadventure <story> <u1,u2,...>       – Start D&D adventure")
    print("  /joinadventure <room_id> <role>           – Join adventure with role")
    print("  /adventure <room_id> <type> <message>     –  Send message to adventure room")
    print("  /adventureinfo <room_id>                  – Get adventure room info")
    print("  /exit or /quit                            – exit client\n")

    while True:
        try:
            raw = await asyncio.to_thread(input, f"You ({sio.sid})> ")
            if not raw:
                continue

            cmd, *rest = raw.split(" ", 1)
            lower = raw.lower()

            if lower in ("/exit", "/quit"):
                print("Client Exiting...")
                await sio.disconnect()
                break

            if cmd == "/users":
                await sio.emit("get_users")
                continue

            if cmd == "/rooms":
                await sio.emit("check_rooms")
                continue

            if cmd == "/history":
                await sio.emit("get_chat_history")
                continue

            if cmd == "/pm":
                # /pm <user> <type> <message>
                parts = raw.split(" ", 3)
                if len(parts) < 4:
                    print("Usage: /pm <username> <type> <message>")
                    continue
                _, user, msg_type, msg = parts
                if msg_type == "file":
                    try:
                        payload = make_file_payload(user, msg)
                    except FileNotFoundError as e:
                        print(e)
                        continue
                else:
                    payload = make_payload(user, msg, msg_type)

                await sio.emit("private_message", payload)               
                continue

            if cmd == "/join":
                room = rest[0]
                await sio.emit("join_room", {"room": room})
                print(f"Joined room: {room}")
                continue

            if cmd == "/leave":
                room = rest[0]
                await sio.emit("leave_room", {"room": room})
                print(f"Left room: {room}")
                continue

            if cmd == "/room":
                # /room <room> <type> <message>
                parts = raw.split(" ", 3)
                if len(parts) < 4:
                    print("Usage: /room <room> <type> <message>")
                    continue
                _, room, msg_type, msg = parts
                if msg_type == "file":
                    try:
                        payload = make_file_payload(room, msg)
                    except FileNotFoundError as e:
                        print(e)
                        continue
                else:
                    payload = make_payload(room, msg, msg_type)

                await sio.emit("room_message", payload)               
                continue

            if cmd == "/startadventure":
                parts = raw.split(" ", 2)
                if len(parts) < 3:
                    print("Usage: /startadventure <story> <u1,u2,...>")
                    continue
                _, story, us = parts
                users = [u.strip() for u in us.split(",")]
                await sio.emit("start_adventure", {"story": story, "users": users})
                continue

            if cmd == "/joinadventure":
                parts = raw.split(" ", 2)
                if len(parts) < 3:
                    print("Usage: /joinadventure <room_id> <role>")
                    continue
                _, room_id, role = parts
                await sio.emit("join_adventure", {"room_id": room_id, "role": role})
                continue

            if cmd == "/adventureinfo":
                parts = raw.split(" ", 1)
                if len(parts) < 2:
                    print("Usage: /adventureinfo <room_id>")
                    continue
                _, room_id = parts
                await sio.emit("get_adventure_info", {"room_id": room_id})
                continue

            if cmd == "/adventure":
                # /adventure <room_id> <type> <message>
                parts = raw.split(" ", 3)
                if len(parts) < 4:
                    print("Usage: /adventure <room_id> <type> <message>")
                    continue
                _, room_id, msg_type, msg = parts
                if msg_type == "file":
                    try:
                        payload = make_file_payload(room_id, msg)
                    except FileNotFoundError as e:
                        print(e)
                        continue
                else:
                    payload = make_payload(room_id, msg, msg_type)

                await sio.emit("adventure_message", payload)               
                continue   

            # --- global chat: <type> <message> OR just <message> ---
            parts = raw.split(" ", 1)
            if len(parts) == 1:
                # Single word - treat as text message
                msg_type = "text"
                body = parts[0]
            elif len(parts) == 2:
                # Check if first part looks like a message type
                potential_type = parts[0].lower()
                if potential_type in ["text", "file"]:
                    msg_type, body = parts
                else:
                    # Treat the whole thing as a text message
                    msg_type = "text"
                    body = raw
            else:
                print("Usage: <type> <message> for global chat, or just <message> for text")
                continue
                
            # choose text vs file
            if msg_type == "file":
                try:
                    payload = make_file_payload("all", body)
                except FileNotFoundError as e:
                    print(e)
                    continue
            else:
                payload = make_payload("all", body, msg_type)

            await sio.emit("chat_message", payload)

        except KeyboardInterrupt:
            print("\nClient Exiting...")
            await sio.disconnect()
            break
        except Exception as e:
            print(f"Error: {e}")

async def main():
    try:
        await sio.connect("http://localhost:8080")
        await asyncio.gather(
            sio.wait(),        # incoming
            send_messages(),   # user input
        )
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
