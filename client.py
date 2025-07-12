import asyncio
import socketio
import os
import base64
from datetime import datetime

sio = socketio.AsyncClient()
username = None

def make_payload(receiver: str, content: str, msg_type: str):
    """Build our standard JSON envelope."""
    if msg_type != "text".lower() and  msg_type != "file".lower():
        print("Invalid type")
        return {}
    else:
        return {
            "sender_name": username,
            "receiver_name": receiver,
            "type": msg_type,
            "data": content,
            "timestamp": datetime.utcnow().isoformat() + "Z"
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

def print_fields(obj, prefix=''):
    """
    Recursively prints all keys (and list indices) in a JSON-like object,
    along with their values. Nested keys are shown as dot-separated paths.
    """
    if isinstance(obj, dict):
        for key, val in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            # If the value is a primitive, print it; otherwise recurse
            if isinstance(val, (dict, list)):
                print_fields(val, path)
            else:
                print(f"{path}: {val}")
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            path = f"{prefix}[{idx}]"
            if isinstance(item, (dict, list)):
                print_fields(item, path)
            else:
                print(f"{path}: {item}")
    else:
        # Shouldn't hit this for the top‐level call, but handles primitives
        print(f"{prefix}: {obj}")

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
    action_result= data.get("action_result",'')
    ai_narration= data.get( "ai_narration",'')
    timestamp: data.get("timestamp", "")
    msg_type= data.get("type","")

    if msg_type in ('join','dm_disconnect', 'player_disconnect'):
        print(f"[ADVENTURE {room_id}]  {message}\n" )

    elif msg_type=='action':
        print(f"[ADVENTURE {room_id}]  {message}\n sender: {sender_name}\n role:{sender_role}\n" )
        print_fields(ai_narration)
        
    else:
        print(f"[ADVENTURE {room_id} - {sender_name} ({sender_role})]: {message}")

@sio.event
async def turn_summary(data):
    print("Turn Summary received:")
    
    room_id = data.get("room_id")
    current_turn = data.get("current_turn")
    turn_order = data.get("turn_order")
    players = data.get("players")
    story_state = data.get("story_state", {})
    npcs = data.get("npcs")
    enemies = data.get("enemies")

    print(f"Room ID: {room_id}")
    print(f"Current Turn: {current_turn}")
    print(f"Turn Order: {turn_order}")
    
    print("\nPlayers:")
    for sid, player in players.items():
        print(f" - SID: {sid}, Name: {player.get('name')}, Status: {player.get('status')}")
    
    print("\nStory State:")
    print(f"  Scene: {story_state.get('current_scene')}")
    print(f"  Environment: {story_state.get('environment')}")
    print(f"  Time: {story_state.get('time')}")
    print(f"  Weather: {story_state.get('weather')}")
    print(f"  Encounter Active: {story_state.get('encounter_active')}")

@sio.event
def turn_notification(data):
    player_name = data.get("player_name")
    message = data.get("message")
    print(f"[TURN] {message} (Player: {player_name})")

@sio.event
def player_stats(data):
    print("[PLAYER STATS RECEIVED]")
    for stat, value in data.items():
        print(f"{stat}: {value}")

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
    print("  <type> <message>                          – global chat")
    print("  /users                                    – list users")
    print("  /rooms                                    – list rooms joined")
    print("  /pm <user> <type> <message>               – private message")
    print("  /join <room>                              – join a room")
    print("  /leave <room>                             – leave a room")
    print("  /room <room> <type> <message>             – room chat")
    print("  /startadventure       – Start D&D adventure")
    print("  /joinadventure <room_id> <role>           – Join adventure with role")
    print("  /adventure <room_id> <type> <message>     –  Send message to adventure room")
    print(" /adventureStats <room_id>                          - get player stats")
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
                        payload = make_file_payload(user, msg)
                    except FileNotFoundError as e:
                        print(e)
                        continue
                else:
                    payload = make_payload(user, msg, msg_type)

                await sio.emit("room_message", payload)               
                continue

            if cmd == "/startadventure":
                theme = input("Enter theme (optional): ").strip()
                tonality = input("Enter tonality (optional): ").strip()
                story = input("Enter story (optional): ").strip()
                user_str = input("Enter comma-separated usernames (required): ").strip()

                users = [u.strip() for u in user_str.split(",") if u.strip()]

                if not users:
                    print("Error: No users provided.")
                    continue

                await sio.emit("start_adventure", {
                    "theme": theme,
                    "tonality": tonality,
                    "story": story,
                    "users": users
                })
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
                parts = raw.split(" ", 2)
                if len(parts) < 3:
                    print("Usage: /adventure <room_id> <message>")
                    continue
                _, room_id, msg = parts
                payload = {
                        "room_id":room_id,
                        "message":msg
                        }

                await sio.emit("adventure_message", payload)               
                continue   
            
            if cmd== "/adventureStats":
                parts = raw.split(" ", 2)
                if len(parts) < 2:
                    print("Usage: /adventure <room_id>")
                room_id= parts
                await sio.emit("get_stats", room_id)
                continue

            # --- global chat: <type> <message> ---
            parts = raw.split(" ", 1)
            if len(parts) < 2:
                print("Usage: <type> <message> for global chat")
                continue
            msg_type, body = parts
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

