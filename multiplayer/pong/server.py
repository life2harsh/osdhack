import asyncio
import websockets
import json
import uuid
import logging
from typing import Dict, List, Optional, Any
import random
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Player:
    def __init__(self, websocket, player_id: str, name: str):
        self.websocket = websocket
        self.player_id = player_id
        self.name = name
        self.ready = False
        self.paddle_y: float= 205
        self.score = 0

class GameRoom:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: Dict[int, Optional[Player]] = {1: None, 2: None}
        self.spectators: List[Player] = []

        self.ball_x = 400
        self.ball_y = 250
        self.ball_speed_x = 0
        self.ball_speed_y = 0
        self.game_active = False
        self.game_paused = False
        self.last_update = time.time()

        self.winning_score = 10
        self.ball_speed = 4
        self.paddle_speed = 8

    def add_player(self, websocket, player_id: str, name: str) -> Optional[int]:
        """Add a player to the room. Returns player number (1 or 2) or None if room is full."""
        player = Player(websocket, player_id, name)

        if self.players[1] is None:
            self.players[1] = player
            logging.info(f"Player {name} joined room {self.room_id} as Player 1")
            return 1
        elif self.players[2] is None:
            self.players[2] = player
            logging.info(f"Player {name} joined room {self.room_id} as Player 2")

            self.start_game()
            return 2
        else:

            self.spectators.append(player)
            logging.info(f"Player {name} joined room {self.room_id} as spectator")
            return None

    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the room. Returns True if room becomes empty."""

        for slot, player in self.players.items():
            if player and player.player_id == player_id:
                logging.info(f"Player {player.name} (Player {slot}) left room {self.room_id}")
                self.players[slot] = None
                self.pause_game()
                break

        self.spectators = [s for s in self.spectators if s.player_id != player_id]

        return all(p is None for p in self.players.values()) and len(self.spectators) == 0

    def get_player_count(self) -> int:
        """Get number of active players (not spectators)."""
        return sum(1 for p in self.players.values() if p is not None)

    def is_full(self) -> bool:
        """Check if room has both player slots filled."""
        return all(p is not None for p in self.players.values())

    def start_game(self):
        """Start the game when both players are present."""
        if self.is_full():
            self.game_active = True
            self.game_paused = False
            self.reset_ball()
            self.reset_paddles()
            logging.info(f"Game started in room {self.room_id}")

    def pause_game(self):
        """Pause the game when a player leaves."""
        self.game_active = False
        self.game_paused = True
        self.ball_speed_x = 0
        self.ball_speed_y = 0

    def reset_game(self):
        """Reset the game state for a new game."""
        if self.players[1]:
            self.players[1].score = 0
        if self.players[2]:
            self.players[2].score = 0

        self.reset_paddles()
        self.reset_ball()

        if self.is_full():
            self.game_active = True
            self.game_paused = False

        logging.info(f"Game reset in room {self.room_id}")

    def reset_paddles(self):
        """Reset paddle positions."""
        if self.players[1]:
            self.players[1].paddle_y = 205
        if self.players[2]:
            self.players[2].paddle_y = 205

    def reset_ball(self):
        """Reset ball to center with random direction."""
        self.ball_x = 400
        self.ball_y = 250

        if self.game_active and self.is_full():

            direction = 1 if random.random() > 0.5 else -1
            self.ball_speed_x = self.ball_speed * direction
            self.ball_speed_y = random.uniform(-3, 3)
        else:
            self.ball_speed_x = 0
            self.ball_speed_y = 0

    def update_paddle(self, player_number: int, y: float):
        """Update player paddle position."""
        if player_number in self.players and self.players[player_number]:

            self.players[player_number].paddle_y = max(0, min(410, y)) 

    def update_game_state(self):
        """Update the game physics."""
        if not self.game_active or not self.is_full():
            return

        self.ball_x += self.ball_speed_x
        self.ball_y += self.ball_speed_y

        if self.ball_y <= 6 or self.ball_y >= 494:
            self.ball_speed_y = -self.ball_speed_y
            self.ball_y = max(6, min(494, self.ball_y))

        player1 = self.players[1]
        player2 = self.players[2]

        if not player1 or not player2:
            return

        if (self.ball_x <= 18 and 
            self.ball_y >= player1.paddle_y and 
            self.ball_y <= player1.paddle_y + 90 and
            self.ball_speed_x < 0):

            self.ball_speed_x = abs(self.ball_speed_x) * 1.02
            self.ball_x = 18

            hit_pos = (self.ball_y - player1.paddle_y) / 90
            self.ball_speed_y = (hit_pos - 0.5) * 8

        elif (self.ball_x >= 782 and 
              self.ball_y >= player2.paddle_y and 
              self.ball_y <= player2.paddle_y + 90 and
              self.ball_speed_x > 0):

            self.ball_speed_x = -abs(self.ball_speed_x) * 1.02
            self.ball_x = 782

            hit_pos = (self.ball_y - player2.paddle_y) / 90
            self.ball_speed_y = (hit_pos - 0.5) * 8

        if self.ball_x < 0:
            player2.score += 1
            logging.info(f"Point scored in room {self.room_id}: {player1.name} {player1.score} - {player2.score} {player2.name}")
            self.reset_ball()
        elif self.ball_x > 800:
            player1.score += 1
            logging.info(f"Point scored in room {self.room_id}: {player1.name} {player1.score} - {player2.score} {player2.name}")
            self.reset_ball()

        if player1.score >= self.winning_score or player2.score >= self.winning_score:
            self.game_active = False
            winner = player1.name if player1.score >= self.winning_score else player2.name
            logging.info(f"Game finished in room {self.room_id}: {winner} wins!")

    def get_game_state(self) -> dict:
        """Get current game state for broadcasting."""
        player1 = self.players[1]
        player2 = self.players[2]

        return {
            'ballX': self.ball_x,
            'ballY': self.ball_y,
            'ballSpeedX': self.ball_speed_x,
            'ballSpeedY': self.ball_speed_y,
            'player1Y': player1.paddle_y if player1 else 205,
            'player2Y': player2.paddle_y if player2 else 205,
            'player1Score': player1.score if player1 else 0,
            'player2Score': player2.score if player2 else 0,
            'player1Name': player1.name if player1 else 'Player 1',
            'player2Name': player2.name if player2 else 'Player 2',
            'gameActive': self.game_active
        }

    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all players and spectators in the room."""
        message_str = json.dumps(message)
        disconnected = []

        for slot, player in self.players.items():
            if player:
                try:
                    await player.websocket.send(message_str)
                except (websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError):
                    disconnected.append(player.player_id)
                except Exception as e:
                    logging.error(f"Error sending message to player {player.player_id}: {e}")
                    disconnected.append(player.player_id)

        for spectator in self.spectators:
            try:
                await spectator.websocket.send(message_str)
            except (websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError):
                disconnected.append(spectator.player_id)
            except Exception as e:
                logging.error(f"Error sending message to spectator {spectator.player_id}: {e}")
                disconnected.append(spectator.player_id)

        for player_id in disconnected:
            self.remove_player(player_id)

class GameServer:
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.player_to_room: Dict[str, str] = {}
        self.waiting_room: Optional[str] = None

    def find_or_create_room(self) -> str:
        """Find an available room or create a new one using proper matchmaking logic."""

        if self.waiting_room and self.waiting_room in self.rooms:
            room = self.rooms[self.waiting_room]
            if room.get_player_count() == 1:  
                logging.info(f"Joining player to waiting room {self.waiting_room}")
                return self.waiting_room
            elif room.get_player_count() == 0:

                del self.rooms[self.waiting_room]
                self.waiting_room = None

        for room_id, room in self.rooms.items():
            if room.get_player_count() == 1:
                logging.info(f"Found room {room_id} with 1 player waiting")
                return room_id

        room_id = str(uuid.uuid4())[:8]
        self.rooms[room_id] = GameRoom(room_id)
        self.waiting_room = room_id
        logging.info(f"Created new room {room_id}")
        return room_id

    def cleanup_empty_rooms(self):
        """Remove empty rooms."""
        empty_rooms = []
        for room_id, room in self.rooms.items():
            if room.get_player_count() == 0 and len(room.spectators) == 0:
                empty_rooms.append(room_id)

        for room_id in empty_rooms:
            if room_id == self.waiting_room:
                self.waiting_room = None
            del self.rooms[room_id]
            logging.info(f"Cleaned up empty room {room_id}")

    async def handle_client(self, websocket: Any, path: Optional[str] = None):
        player_id = str(uuid.uuid4())
        room_id = None
        player_number = None

        try:

            try:
                initial_message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                data = json.loads(initial_message)
            except asyncio.TimeoutError:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Connection timeout'
                }))
                return
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    'type': 'error', 
                    'message': 'Invalid message format'
                }))
                return

            player_name = "Anonymous"
            if data.get('type') == 'join' and data.get('name'):
                player_name = data['name'].strip()[:20]

            room_id = self.find_or_create_room()
            room = self.rooms[room_id]

            player_number = room.add_player(websocket, player_id, player_name)
            self.player_to_room[player_id] = room_id

            if room.get_player_count() == 2:

                if self.waiting_room == room_id:
                    self.waiting_room = None

            await websocket.send(json.dumps({
                'type': 'connected',
                'player_number': player_number,
                'room_id': room_id,
                'players_in_room': room.get_player_count(),
                'player_name': player_name,
                'is_spectator': player_number is None
            }))

            await room.broadcast_to_all({
                'type': 'game_state',
                'data': room.get_game_state()
            })

            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(player_id, data)
                except json.JSONDecodeError:
                    logging.warning(f"Invalid JSON from player {player_id}")
                except Exception as e:
                    logging.error(f"Error handling message from {player_id}: {e}")

        except (websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError):
            logging.info(f"Player {player_id} disconnected")
        except Exception as e:
            logging.error(f"Error in handle_client: {e}")
        finally:

            if player_id in self.player_to_room:
                room_id = self.player_to_room[player_id]
                if room_id in self.rooms:
                    room = self.rooms[room_id]
                    room_empty = room.remove_player(player_id)

                    if room_empty:
                        if self.waiting_room == room_id:
                            self.waiting_room = None

                    elif room.get_player_count() == 1:
                        self.waiting_room = room_id

                del self.player_to_room[player_id]

            self.cleanup_empty_rooms()

    async def handle_message(self, player_id: str, data: dict):
        """Handle incoming messages from players."""
        if player_id not in self.player_to_room:
            return

        room_id = self.player_to_room[player_id]
        if room_id not in self.rooms:
            return

        room = self.rooms[room_id]

        if data['type'] == 'paddle_move':

            player_number = None
            for slot, player in room.players.items():
                if player and player.player_id == player_id:
                    player_number = slot
                    break

            if player_number:
                room.update_paddle(player_number, data['y'])

        elif data['type'] == 'reset_game':
            room.reset_game()
            logging.info(f"Game reset requested in room {room_id}")

    async def game_loop(self):
        """Main game loop - updates all active games."""
        while True:
            try:
                current_time = time.time()

                for room in list(self.rooms.values()):
                    if room.game_active:
                        room.update_game_state()

                    await room.broadcast_to_all({
                        'type': 'game_state',
                        'data': room.get_game_state()
                    })

                await asyncio.sleep(1/60)  
            except Exception as e:
                logging.error(f"Error in game loop: {e}")
                await asyncio.sleep(1/60)

    async def start_server(self):
        """Start the game server."""

        asyncio.create_task(self.game_loop())

        try:
            server = await websockets.serve(
                self.handle_client,
                "localhost",
                8765,
                ping_interval=20,
                ping_timeout=10
            )

            print("=" * 60)
            print("🏓 MULTIPLAYER PONG SERVER STARTED 🏓")
            print("=" * 60)
            print("Server: ws://localhost:8765")
            print("Matchmaking: Smart room assignment")
            print("• 2 players per game room")
            print("• Automatic matchmaking")
            print("• Spectator support")
            print("• First to 10 points wins!")
            print("Press Ctrl+C to stop")
            print("=" * 60)

            await server.wait_closed()

        except OSError as e:
            if e.errno == 98:
                print("❌ Port 8765 already in use!")
                print("Stop other servers and try again.")
            else:
                print(f"❌ Network error: {e}")
        except Exception as e:
            print(f"❌ Server error: {e}")

if __name__ == "__main__":
    try:
        server = GameServer()
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("🛑 Server stopped")
        print("Thanks for playing Multiplayer Pong!")
        print("=" * 60)
    except Exception as e:
        print(f"❌ Server error: {e}")