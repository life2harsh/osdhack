"""
Tank Wars Multiplayer Server
A WebSocket-based tank battle game server with multiple game modes,
tank classes, team systems, and real-time combat.
"""
import asyncio
import websockets
import json
import math
import random
import time
import uuid
import string
from typing import Dict, List, Set, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

class GameMode(Enum):
    DEATHMATCH = "deathmatch"
    TEAM = "team"
    CAPTURE_FLAG = "capture"

class TankClass(Enum):
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    ARTILLERY = "artillery"

@dataclass
class TankStats:
    speed: float
    health: int
    armor: float  
    fire_rate: float  
    damage: int
    size: int

TANK_CLASSES = {
    TankClass.LIGHT: TankStats(speed=120, health=75, armor=0.8, fire_rate=0.2, damage=20, size=12),
    TankClass.MEDIUM: TankStats(speed=80, health=100, armor=0.6, fire_rate=0.4, damage=30, size=15),
    TankClass.HEAVY: TankStats(speed=50, health=150, armor=0.4, fire_rate=0.6, damage=35, size=18),
    TankClass.ARTILLERY: TankStats(speed=30, health=80, armor=0.7, fire_rate=1.0, damage=60, size=16),
}

class Vector2:
    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalize(self):
        length = self.length()
        if length > 0:
            return Vector2(self.x / length, self.y / length)
        return Vector2(0, 0)

    def distance_to(self, other):
        return (self - other).length()

class Tank:
    def __init__(self, tank_id: str, name: str, tank_class: TankClass, team: Optional[str] = None):
        self.id = tank_id
        self.name = name
        self.tank_class = tank_class
        self.team = team
        self.stats = TANK_CLASSES[tank_class]

        self.position = Vector2(0, 0)
        self.angle = 0.0
        self.health = self.stats.health
        self.max_health = self.stats.health
        self.rotation_speed = 3.0
        self.last_fire_time = 0
        self.kills = 0
        self.deaths = 0
        self.alive = True
        self.respawn_time = 0

        self.speed_boost_end = 0
        self.damage_boost_end = 0

    def update(self, dt: float, input_state: dict, world_bounds: Tuple[int, int], obstacles: List['Obstacle']):
        if not self.alive:
            return

        if input_state.get('left', False):
            self.angle -= self.rotation_speed * dt
        if input_state.get('right', False):
            self.angle += self.rotation_speed * dt

        current_speed = self.stats.speed
        if time.time() < self.speed_boost_end:
            current_speed *= 1.5

        movement = Vector2(0, 0)
        if input_state.get('up', False):
            movement.x += math.cos(self.angle) * current_speed * dt
            movement.y += math.sin(self.angle) * current_speed * dt
        if input_state.get('down', False):
            movement.x -= math.cos(self.angle) * current_speed * dt * 0.5  
            movement.y -= math.sin(self.angle) * current_speed * dt * 0.5

        new_position = self.position + movement

        tank_radius = self.stats.size
        collision = False

        for obstacle in obstacles:
            if obstacle.collides_with_point(new_position.x, new_position.y, tank_radius):
                collision = True
                break

        if not collision:

            margin = tank_radius
            new_position.x = max(margin, min(world_bounds[0] - margin, new_position.x))
            new_position.y = max(margin, min(world_bounds[1] - margin, new_position.y))
            self.position = new_position

    def can_fire(self) -> bool:
        return self.alive and time.time() - self.last_fire_time >= self.stats.fire_rate

    def fire(self) -> Optional['Bullet']:
        if self.can_fire():
            self.last_fire_time = time.time()

            barrel_length = self.stats.size * 2
            bullet_x = self.position.x + math.cos(self.angle) * barrel_length
            bullet_y = self.position.y + math.sin(self.angle) * barrel_length

            damage = self.stats.damage
            if time.time() < self.damage_boost_end:
                damage = int(damage * 1.5)

            return Bullet(bullet_x, bullet_y, self.angle, self.id, damage)
        return None

    def take_damage(self, damage: int):

        actual_damage = int(damage * self.stats.armor)
        self.health -= actual_damage

        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.deaths += 1
            self.respawn_time = time.time() + 3.0

    def respawn(self, x: float, y: float):
        self.position = Vector2(x, y)
        self.health = self.max_health
        self.alive = True
        self.angle = random.uniform(0, 2 * math.pi)
        self.respawn_time = 0

        self.speed_boost_end = 0
        self.damage_boost_end = 0

    def apply_powerup(self, powerup_type: str, value: int):
        if powerup_type == 'health':
            self.health = min(self.max_health, self.health + value)
        elif powerup_type == 'speed':
            self.speed_boost_end = time.time() + 10.0  
        elif powerup_type == 'damage':
            self.damage_boost_end = time.time() + 10.0  

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'x': self.position.x,
            'y': self.position.y,
            'angle': self.angle,
            'health': self.health,
            'maxHealth': self.max_health,
            'kills': self.kills,
            'deaths': self.deaths,
            'alive': self.alive,
            'team': self.team,
            'tankClass': self.tank_class.value
        }

class Bullet:
    def __init__(self, x: float, y: float, angle: float, owner_id: str, damage: int = 25):
        self.id = str(uuid.uuid4())
        self.position = Vector2(x, y)
        self.velocity = Vector2(
            math.cos(angle) * 400,
            math.sin(angle) * 400
        )
        self.owner_id = owner_id
        self.damage = damage
        self.lifetime = 3.0
        self.creation_time = time.time()

    def update(self, dt: float) -> bool:
        self.position = self.position + self.velocity * dt
        return time.time() - self.creation_time < self.lifetime

    def to_dict(self):
        return {
            'id': self.id,
            'x': self.position.x,
            'y': self.position.y,
            'owner_id': self.owner_id
        }

class Obstacle:
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def collides_with_point(self, x: float, y: float, radius: float = 0) -> bool:
        return (x - radius < self.x + self.width and 
                x + radius > self.x and 
                y - radius < self.y + self.height and 
                y + radius > self.y)

    def collides_with_bullet(self, bullet_pos: Vector2, radius: float = 3) -> bool:
        return self.collides_with_point(bullet_pos.x, bullet_pos.y, radius)

    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height
        }

class PowerUp:
    def __init__(self, x: float, y: float, powerup_type: str):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.type = powerup_type
        self.value = self._get_value(powerup_type)
        self.creation_time = time.time()
        self.lifetime = 30.0

    def _get_value(self, powerup_type: str) -> int:
        values = {
            'health': 50,
            'speed': 0,  
            'damage': 0  
        }
        return values.get(powerup_type, 0)

    def is_expired(self) -> bool:
        return time.time() - self.creation_time > self.lifetime

    def collides_with_tank(self, tank: Tank) -> bool:
        distance = Vector2(self.x, self.y).distance_to(tank.position)
        return distance < 25

    def to_dict(self):
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'type': self.type,
            'value': self.value
        }

class Flag:
    def __init__(self, x: float, y: float, team: str):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.team = team
        self.captured = False
        self.carrier_id: Optional[str] = None

    def to_dict(self):
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'team': self.team,
            'captured': self.captured,
            'carrier_id': self.carrier_id
        }

class GameRoom:
    def __init__(self, room_id: str, game_mode: GameMode, max_players: int = 8):
        self.room_id = room_id
        self.game_mode = game_mode
        self.max_players = max_players
        self.tanks: Dict[str, Tank] = {}
        self.bullets: List[Bullet] = []
        self.obstacles: List[Obstacle] = []
        self.powerups: List[PowerUp] = []
        self.flags: List[Flag] = []
        self.teams: Dict[str, List[str]] = {'red': [], 'blue': [], 'green': [], 'yellow': []}
        self.world_width = 1000
        self.world_height = 700
        self.last_update = time.time()
        self.last_powerup_spawn = time.time()
        self.powerup_spawn_interval = 8.0

        self.generate_obstacles()
        if game_mode == GameMode.CAPTURE_FLAG:
            self.generate_flags()

    def generate_obstacles(self):
        """Generate random obstacles"""
        obstacle_count = random.randint(8, 15)

        for _ in range(obstacle_count):
            width = random.randint(30, 80)
            height = random.randint(30, 80)
            x = random.randint(50, self.world_width - width - 50)
            y = random.randint(50, self.world_height - height - 50)

            self.obstacles.append(Obstacle(x, y, width, height))

    def generate_flags(self):
        """Generate flags for capture the flag mode"""
        teams = ['red', 'blue']
        if len(self.tanks) > 4:
            teams.extend(['green', 'yellow'])

        for i, team in enumerate(teams):
            if i == 0:  
                x, y = 100, self.world_height // 2
            elif i == 1:  
                x, y = self.world_width - 100, self.world_height // 2
            elif i == 2:  
                x, y = self.world_width // 2, 100
            else:  
                x, y = self.world_width // 2, self.world_height - 100

            self.flags.append(Flag(x, y, team))

    def find_spawn_position(self, team: Optional[str] = None) -> Tuple[float, float]:
        """Find spawn position, considering team if applicable"""
        max_attempts = 50

        if team and self.game_mode in [GameMode.TEAM, GameMode.CAPTURE_FLAG]:
            spawn_areas = {
                'red': (50, 150, 50, self.world_height - 50),
                'blue': (self.world_width - 150, self.world_width - 50, 50, self.world_height - 50),
                'green': (50, self.world_width - 50, 50, 150),
                'yellow': (50, self.world_width - 50, self.world_height - 150, self.world_height - 50)
            }

            if team in spawn_areas:
                x_min, x_max, y_min, y_max = spawn_areas[team]
            else:
                x_min, x_max, y_min, y_max = 50, self.world_width - 50, 50, self.world_height - 50
        else:
            x_min, x_max, y_min, y_max = 50, self.world_width - 50, 50, self.world_height - 50

        for _ in range(max_attempts):
            x = random.randint(int(x_min), int(x_max))
            y = random.randint(int(y_min), int(y_max))

            clear = True
            for obstacle in self.obstacles:
                if obstacle.collides_with_point(x, y, 40):
                    clear = False
                    break

            if clear:
                for tank in self.tanks.values():
                    if tank.alive and tank.position.distance_to(Vector2(x, y)) < 100:
                        clear = False
                        break

            if clear:
                return x, y

        return random.randint(100, self.world_width - 100), random.randint(100, self.world_height - 100)

    def assign_team(self, tank_id: str) -> Optional[str]:
        """Assign team for team-based modes"""
        if self.game_mode == GameMode.DEATHMATCH:
            return None

        team_sizes = {team: len(players) for team, players in self.teams.items()}
        smallest_team = min(team_sizes.keys(), key=lambda k: team_sizes[k])

        self.teams[smallest_team].append(tank_id)
        return smallest_team

    def add_tank(self, tank_id: str, name: str, tank_class: TankClass) -> Tank:
        """Add new tank to the game"""
        team = self.assign_team(tank_id)
        tank = Tank(tank_id, name, tank_class, team)

        x, y = self.find_spawn_position(team)
        tank.position = Vector2(x, y)

        self.tanks[tank_id] = tank
        return tank

    def remove_tank(self, tank_id: str):
        """Remove tank from game"""
        if tank_id in self.tanks:
            tank = self.tanks[tank_id]

            if tank.team and tank_id in self.teams.get(tank.team, []):
                self.teams[tank.team].remove(tank_id)
            del self.tanks[tank_id]

    def update(self, dt: float):
        """Update game state"""

        for tank in self.tanks.values():
            if tank.alive:
                pass  
            elif tank.respawn_time > 0 and time.time() >= tank.respawn_time:
                x, y = self.find_spawn_position(tank.team)
                tank.respawn(x, y)

        bullets_to_remove = []
        for bullet in self.bullets:
            if not bullet.update(dt):
                bullets_to_remove.append(bullet)
                continue

            for obstacle in self.obstacles:
                if obstacle.collides_with_bullet(bullet.position):
                    bullets_to_remove.append(bullet)
                    break

            if bullet not in bullets_to_remove:
                for tank in self.tanks.values():
                    if (tank.alive and tank.id != bullet.owner_id and 
                        tank.position.distance_to(bullet.position) < tank.stats.size):

                        if (self.game_mode in [GameMode.TEAM, GameMode.CAPTURE_FLAG] and 
                            tank.team and bullet.owner_id in self.tanks and
                            self.tanks[bullet.owner_id].team == tank.team):
                            continue  

                        tank.take_damage(bullet.damage)
                        bullets_to_remove.append(bullet)

                        if not tank.alive and bullet.owner_id in self.tanks:
                            self.tanks[bullet.owner_id].kills += 1
                        break

            if (bullet.position.x < 0 or bullet.position.x > self.world_width or
                bullet.position.y < 0 or bullet.position.y > self.world_height):
                bullets_to_remove.append(bullet)

        for bullet in bullets_to_remove:
            if bullet in self.bullets:
                self.bullets.remove(bullet)

        powerups_to_remove = []
        for powerup in self.powerups:
            if powerup.is_expired():
                powerups_to_remove.append(powerup)
                continue

            for tank in self.tanks.values():
                if tank.alive and powerup.collides_with_tank(tank):
                    tank.apply_powerup(powerup.type, powerup.value)
                    powerups_to_remove.append(powerup)
                    break

        for powerup in powerups_to_remove:
            if powerup in self.powerups:
                self.powerups.remove(powerup)

        if (time.time() - self.last_powerup_spawn > self.powerup_spawn_interval and 
            len(self.powerups) < 4):
            x, y = self.find_spawn_position()
            powerup_type = random.choice(['health', 'speed', 'damage'])
            self.powerups.append(PowerUp(x, y, powerup_type))
            self.last_powerup_spawn = time.time()

        if self.game_mode == GameMode.CAPTURE_FLAG:
            self.update_capture_the_flag()

    def update_capture_the_flag(self):
        """Update capture the flag game logic"""
        for flag in self.flags:
            if not flag.captured:

                for tank in self.tanks.values():
                    if (tank.alive and tank.team != flag.team and 
                        Vector2(flag.x, flag.y).distance_to(tank.position) < 30):
                        flag.captured = True
                        flag.carrier_id = tank.id
                        break
            else:

                if flag.carrier_id in self.tanks:
                    carrier = self.tanks[flag.carrier_id]
                    if carrier.alive:
                        flag.x = carrier.position.x
                        flag.y = carrier.position.y
                    else:

                        flag.captured = False
                        flag.carrier_id = None

    def fire_bullet(self, tank_id: str) -> Optional[Bullet]:
        """Tank fires a bullet"""
        if tank_id in self.tanks:
            tank = self.tanks[tank_id]
            bullet = tank.fire()
            if bullet:
                self.bullets.append(bullet)
                return bullet
        return None

    def get_leaderboard(self) -> List[Dict]:
        """Get leaderboard sorted by kills"""
        tanks_list = list(self.tanks.values())
        tanks_list.sort(key=lambda t: t.kills, reverse=True)
        return [{
            'name': tank.name, 
            'kills': tank.kills, 
            'deaths': tank.deaths,
            'team': tank.team
        } for tank in tanks_list[:10]]

    def get_team_info(self) -> Dict:
        """Get team information"""
        return {
            'mode': self.game_mode.value,
            'teams': self.teams,
            'team_scores': self.get_team_scores()
        }

    def get_team_scores(self) -> Dict[str, int]:
        """Calculate team scores"""
        scores = {}
        for team_name, tank_ids in self.teams.items():
            scores[team_name] = sum(
                self.tanks[tank_id].kills for tank_id in tank_ids 
                if tank_id in self.tanks
            )
        return scores

    def to_dict(self):
        """Convert game state to dictionary"""
        return {
            'tanks': {tank_id: tank.to_dict() for tank_id, tank in self.tanks.items()},
            'bullets': [bullet.to_dict() for bullet in self.bullets],
            'obstacles': [obstacle.to_dict() for obstacle in self.obstacles],
            'powerups': [powerup.to_dict() for powerup in self.powerups],
            'flags': [flag.to_dict() for flag in self.flags],
            'teams': self.teams
        }

class MatchmakingSystem:
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.waiting_players: Dict[GameMode, List[Dict]] = {
            GameMode.DEATHMATCH: [],
            GameMode.TEAM: [],
            GameMode.CAPTURE_FLAG: []
        }

    def find_or_create_room(self, game_mode: GameMode, room_code: Optional[str] = None) -> str:
        """Find existing room or create new one"""
        if room_code:

            if room_code in self.rooms:
                room = self.rooms[room_code]
                if len(room.tanks) < room.max_players:
                    return room_code
            else:

                self.rooms[room_code] = GameRoom(room_code, game_mode)
                return room_code

        for room_id, room in self.rooms.items():
            if (room.game_mode == game_mode and 
                len(room.tanks) < room.max_players):
                return room_id

        room_id = self.generate_room_id()
        self.rooms[room_id] = GameRoom(room_id, game_mode)
        return room_id

    def generate_room_id(self) -> str:
        """Generate random room ID"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def get_room_list(self, game_mode: GameMode) -> List[Dict]:
        """Get list of available rooms for a game mode"""
        rooms = []
        for room in self.rooms.values():
            if room.game_mode == game_mode and len(room.tanks) < room.max_players:
                rooms.append({
                    'id': room.room_id,
                    'name': f"Room {room.room_id}",
                    'players': len(room.tanks),
                    'maxPlayers': room.max_players,
                    'mode': room.game_mode.value
                })
        return rooms

    def cleanup_empty_rooms(self):
        """Remove empty rooms"""
        empty_rooms = [room_id for room_id, room in self.rooms.items() 
                      if len(room.tanks) == 0]
        for room_id in empty_rooms:
            del self.rooms[room_id]

class GameServer:
    def __init__(self):
        self.clients: Dict = {}
        self.matchmaking = MatchmakingSystem()
        self.running = False

    async def register_client(self, websocket):
        """Handle new client connection"""
        print(f"New client connected from {websocket.remote_address}")

    async def unregister_client(self, websocket):
        """Handle client disconnection"""
        if websocket in self.clients:
            client_info = self.clients[websocket]
            tank_id = client_info.get('tank_id')
            room_id = client_info.get('room_id')

            if room_id and room_id in self.matchmaking.rooms:
                self.matchmaking.rooms[room_id].remove_tank(tank_id)

            del self.clients[websocket]
            print(f"Client {tank_id} disconnected")

    async def handle_message(self, websocket, message):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            message_type = data.get('type')

            if message_type == 'join':
                await self.handle_join(websocket, data)
            elif message_type == 'input':
                await self.handle_input(websocket, data)
            elif message_type == 'get_rooms':
                await self.handle_get_rooms(websocket, data)
            elif message_type == 'leave_game':
                await self.handle_leave_game(websocket)

        except json.JSONDecodeError:
            print(f"Invalid JSON from {websocket.remote_address}")
        except Exception as e:
            print(f"Error handling message: {e}")

    async def handle_join(self, websocket, data):
        """Handle player join request"""
        name = data.get('name', 'Anonymous')
        tank_class_str = data.get('tankClass', 'light')
        game_mode_str = data.get('gameMode', 'deathmatch')
        room_code = data.get('roomCode')

        try:
            tank_class = TankClass(tank_class_str)
            game_mode = GameMode(game_mode_str)
        except ValueError:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Invalid tank class or game mode'
            }))
            return

        room_id = self.matchmaking.find_or_create_room(game_mode, room_code)
        room = self.matchmaking.rooms[room_id]

        tank_id = str(uuid.uuid4())
        tank = room.add_tank(tank_id, name, tank_class)

        self.clients[websocket] = {
            'tank_id': tank_id,
            'room_id': room_id,
            'name': name
        }

        await websocket.send(json.dumps({
            'type': 'tank_assigned',
            'tank_id': tank_id,
            'room_id': room_id
        }))

        print(f"Player {name} joined room {room_id} as {tank_class.value}")

    async def handle_input(self, websocket, data):
        """Handle player input"""
        if websocket not in self.clients:
            return

        client_info = self.clients[websocket]
        tank_id = client_info['tank_id']
        room_id = client_info['room_id']

        if room_id not in self.matchmaking.rooms:
            return

        room = self.matchmaking.rooms[room_id]
        input_state = data.get('input', {})

        if tank_id in room.tanks:
            tank = room.tanks[tank_id]
            tank.update(1/60, input_state, (room.world_width, room.world_height), room.obstacles)

            if input_state.get('fire', False):
                bullet = room.fire_bullet(tank_id)
                if bullet:

                    if not tank.alive:
                        await websocket.send(json.dumps({
                            'type': 'tank_destroyed',
                            'tank_id': tank_id
                        }))

                for powerup in room.powerups[:]:  
                    if powerup.collides_with_tank(tank):
                        await websocket.send(json.dumps({
                            'type': 'powerup_collected',
                            'tank_id': tank_id,
                            'powerup_type': powerup.type,
                            'value': powerup.value
                        }))

    async def handle_get_rooms(self, websocket, data):
        """Handle room list request"""
        game_mode_str = data.get('gameMode', 'deathmatch')
        try:
            game_mode = GameMode(game_mode_str)
            rooms = self.matchmaking.get_room_list(game_mode)
            await websocket.send(json.dumps({
                'type': 'room_list',
                'rooms': rooms
            }))
        except ValueError:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Invalid game mode'
            }))

    async def handle_leave_game(self, websocket):
        """Handle player leaving game"""
        if websocket in self.clients:
            await self.unregister_client(websocket)

    async def broadcast_room_state(self, room_id: str):
        """Send game state to all clients in a room"""
        if room_id not in self.matchmaking.rooms:
            return

        room = self.matchmaking.rooms[room_id]
        game_state = room.to_dict()
        leaderboard = room.get_leaderboard()
        team_info = room.get_team_info()

        message = json.dumps({
            'type': 'game_state',
            'state': game_state,
            'leaderboard': leaderboard,
            'teamInfo': team_info
        })

        room_clients = [ws for ws, info in self.clients.items() 
                       if info.get('room_id') == room_id]

        disconnected_clients = []
        for websocket in room_clients:
            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(websocket)
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected_clients.append(websocket)

        for websocket in disconnected_clients:
            await self.unregister_client(websocket)

    async def game_loop(self):
        """Main game loop"""
        last_time = time.time()

        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            for room_id, room in list(self.matchmaking.rooms.items()):
                room.update(dt)
                await self.broadcast_room_state(room_id)

            self.matchmaking.cleanup_empty_rooms()

            await asyncio.sleep(max(0, 1/60 - dt))

    async def client_handler(self, websocket, path=None):
        """Handle individual client connection"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Client handler error: {e}")
        finally:
            await self.unregister_client(websocket)

    async def start_server(self, host='localhost', port=8765):
        """Start the WebSocket server"""
        self.running = True

        print("="*60)
        print("🚗 TANK WARS MULTIPLAYER SERVER 🚗")
        print("="*60)
        print(f"🌐 Server starting on {host}:{port}")
        print()
        print("📋 FEATURES ENABLED:")
        print("  ✅ Multiple tank classes (Light, Medium, Heavy, Artillery)")
        print("  ✅ Team-based combat modes")
        print("  ✅ Capture the flag gameplay")
        print("  ✅ Room system with matchmaking") 
        print("  ✅ Working powerups (Health, Speed, Damage)")
        print("  ✅ Realistic physics and collision detection")
        print("  ✅ Real-time multiplayer combat")
        print()
        print("🎮 GAME MODES:")
        print("  • DEATHMATCH - Free for all combat")
        print("  • TEAM BATTLE - Red vs Blue team warfare")
        print("  • CAPTURE FLAG - Objective-based team combat")
        print()
        print("🛡️ TANK CLASSES:")
        print("  • LIGHT TANK - Fast and agile")
        print("  • MEDIUM TANK - Balanced combat unit")
        print("  • HEAVY TANK - Armored powerhouse")
        print("  • ARTILLERY - Long-range devastation")
        print()
        print("⚡ POWERUPS:")
        print("  • Health Pack - Restore tank health")
        print("  • Speed Boost - Temporary speed increase")
        print("  • Damage Boost - Enhanced firepower")
        print()
        print("="*60)

        try:
            async with websockets.serve(
                self.client_handler, 
                host, 
                port,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            ) as server:
                print(f"🟢 Server is ONLINE at ws://{host}:{port}")
                print("🎯 Waiting for commanders to deploy tanks...")
                print("📊 Use Ctrl+C to stop the server")
                print("="*60)

                await self.game_loop()

        except OSError as e:
            if e.errno == 98:  
                print(f"❌ ERROR: Port {port} is already in use!")
                print(f"💡 Try a different port: python {__file__} --port {port + 1}")
            else:
                print(f"❌ Network error: {e}")
        except Exception as e:
            print(f"❌ Server error: {e}")
            raise
        finally:
            self.running = False
            print("\n" + "="*60)
            print("🛑 TANK WARS SERVER SHUTDOWN")
            print("="*60)

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Tank Wars Multiplayer Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tank_server.py                    
  python tank_server.py --port 9000       
  python tank_server.py --host 0.0.0.0    
        """
    )
    parser.add_argument(
        '--host', 
        default='localhost', 
        help='Server host address (default: localhost, use 0.0.0.0 for public access)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=8765, 
        help='Server port number (default: 8765)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    if not (1024 <= args.port <= 65535):
        print("❌ Error: Port must be between 1024 and 65535")
        return 1

    server = GameServer()

    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        print("🐛 Debug mode enabled")

    try:

        asyncio.run(server.start_server(args.host, args.port))
        return 0

    except KeyboardInterrupt:
        print("\n" + "="*50)
        print("🛑 Server stopped by user (Ctrl+C)")
        print("Thanks for running Tank Wars Server!")
        print("="*50)
        return 0

    except ImportError as e:
        print("❌ Missing required dependency!")
        print("💡 Install websockets: pip install websockets")
        return 1

    except Exception as e:
        print(f"❌ Fatal server error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)