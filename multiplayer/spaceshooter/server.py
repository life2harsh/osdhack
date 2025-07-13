import asyncio
import json
import time
import random
import math
from typing import Dict, List, Optional
import socketio
from aiohttp import web

CANVAS_WIDTH = 1900
CANVAS_HEIGHT = 1000
PLAYER_SPEED = 5
BULLET_SPEED = 10
ENEMY_SPEED = 2
GAME_TICK_RATE = 60  
ENEMY_SPAWN_RATE = 2  

class Player:
    def __init__(self, player_id: str, name: str, x: float = 50, y: float = 300):
        self.id = player_id
        self.name = name
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        self.health = 100
        self.max_health = 100
        self.alive = True
        self.score = 0
        self.last_shot: float = 0

        self.input = {
            'left': False,
            'right': False,
            'up': False,
            'down': False,
            'shoot': False
        }

    def update(self):
        """Update player position based on input"""
        if not self.alive:
            return

        if self.input['left'] and self.x > 0:
            self.x -= PLAYER_SPEED
        if self.input['right'] and self.x < CANVAS_WIDTH - self.width:
            self.x += PLAYER_SPEED
        if self.input['up'] and self.y > 0:
            self.y -= PLAYER_SPEED
        if self.input['down'] and self.y < CANVAS_HEIGHT - self.height:
            self.y += PLAYER_SPEED

    def take_damage(self, damage: int):
        """Apply damage to player"""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def respawn(self):
        """Respawn player"""
        self.health = self.max_health
        self.alive = True
        self.x = 50
        self.y = CANVAS_HEIGHT // 2

    def to_dict(self):
        """Convert player to dictionary for network transmission"""
        return {
            'id': self.id,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'health': self.health,
            'max_health': self.max_health,
            'alive': self.alive,
            'score': self.score
        }

class Enemy:
    def __init__(self, enemy_id: str, x: float = CANVAS_WIDTH, y: Optional[float] = None):
        self.id = enemy_id
        self.x = x
        self.y = y if y is not None else random.uniform(0, CANVAS_HEIGHT - 32)
        self.width = 32
        self.height = 32
        self.health = 50
        self.max_health = 50
        self.speed = ENEMY_SPEED
        self.alive = True

    def update(self):
        """Update enemy position"""
        if self.alive:
            self.x -= self.speed

    def take_damage(self, damage: int):
        """Apply damage to enemy"""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def to_dict(self):
        """Convert enemy to dictionary for network transmission"""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'health': self.health,
            'max_health': self.max_health,
            'alive': self.alive
        }

class Bullet:
    def __init__(self, bullet_id: str, x: float, y: float, player_id: str):
        self.id = bullet_id
        self.x = x
        self.y = y
        self.width = 8
        self.height = 4
        self.speed = BULLET_SPEED
        self.player_id = player_id
        self.alive = True

    def update(self):
        """Update bullet position"""
        if self.alive:
            self.x += self.speed

            if self.x > CANVAS_WIDTH:
                self.alive = False

    def to_dict(self):
        """Convert bullet to dictionary for network transmission"""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'player_id': self.player_id,
            'alive': self.alive
        }

class GameRoom:
    def __init__(self, room_id: str):
        self.id = room_id
        self.players: Dict[str, Player] = {}
        self.enemies: Dict[str, Enemy] = {}
        self.bullets: Dict[str, Bullet] = {}
        self.score = 0
        self.last_enemy_spawn = time.time()
        self.next_enemy_id = 1
        self.next_bullet_id = 1
        self.running = False

    def add_player(self, player_id: str, name: str) -> Player:
        """Add a new player to the room"""
        spawn_x = 50 + (len(self.players) * 60)
        spawn_y = CANVAS_HEIGHT // 2
        player = Player(player_id, name, spawn_x, spawn_y)
        self.players[player_id] = player

        print(f"✅ Player {name} ({player_id}) joined room {self.id}")
        print(f"📊 Room {self.id} now has {len(self.players)} players")

        return player

    def remove_player(self, player_id: str):
        """Remove a player from the room"""
        if player_id in self.players:
            player = self.players[player_id]
            print(f"❌ Player {player.name} ({player_id}) left room {self.id}")
            del self.players[player_id]

    def update_player_input(self, player_id: str, input_data: dict):
        """Update player input state"""
        if player_id in self.players:
            self.players[player_id].input.update(input_data)

    def player_shoot(self, player_id: str):
        """Handle player shooting"""
        if player_id not in self.players:
            return

        player = self.players[player_id]
        if not player.alive:
            return

        current_time = time.time()
        if current_time - player.last_shot < 0.1:  
            return

        bullet_id = f"bullet_{self.next_bullet_id}"
        self.next_bullet_id += 1

        bullet_x = player.x + player.width
        bullet_y = player.y + player.height // 2

        bullet = Bullet(bullet_id, bullet_x, bullet_y, player_id)
        self.bullets[bullet_id] = bullet
        player.last_shot = current_time

        print(f"💥 Player {player.name} shot bullet {bullet_id}")

    def spawn_enemy(self):
        """Spawn a new enemy"""
        enemy_id = f"enemy_{self.next_enemy_id}"
        self.next_enemy_id += 1

        enemy = Enemy(enemy_id)
        self.enemies[enemy_id] = enemy
        self.last_enemy_spawn = time.time()

        print(f"👾 Spawned enemy {enemy_id} at ({enemy.x}, {enemy.y})")

    def check_collisions(self):
        """Check all collisions and apply damage"""

        for bullet in list(self.bullets.values()):
            if not bullet.alive:
                continue

            for enemy in list(self.enemies.values()):
                if not enemy.alive:
                    continue

                if self.check_collision(bullet, enemy):

                    bullet.alive = False
                    enemy.take_damage(25)

                    if not enemy.alive:

                        self.score += 25
                        if bullet.player_id in self.players:
                            self.players[bullet.player_id].score += 25
                        print(f"💥 Enemy {enemy.id} destroyed by {bullet.player_id}")

        for player in self.players.values():
            if not player.alive:
                continue

            for enemy in list(self.enemies.values()):
                if not enemy.alive:
                    continue

                if self.check_collision(player, enemy):

                    player.take_damage(25)
                    enemy.alive = False  
                    print(f"🔥 Player {player.name} hit by enemy {enemy.id}")

    def check_collision(self, obj1, obj2) -> bool:
        """Check if two objects are colliding"""
        return (obj1.x < obj2.x + obj2.width and
                obj1.x + obj1.width > obj2.x and
                obj1.y < obj2.y + obj2.height and
                obj1.y + obj1.height > obj2.y)

    def update(self):
        """Update game state (called every tick)"""

        for player in self.players.values():
            player.update()

        for bullet in list(self.bullets.values()):
            bullet.update()
            if not bullet.alive:
                del self.bullets[bullet.id]

        for enemy in list(self.enemies.values()):
            enemy.update()

            if enemy.x + enemy.width < 0:
                del self.enemies[enemy.id]
            elif not enemy.alive:
                del self.enemies[enemy.id]

        current_time = time.time()
        if current_time - self.last_enemy_spawn > ENEMY_SPAWN_RATE:
            self.spawn_enemy()

        self.check_collisions()

    def get_game_state(self) -> dict:
        """Get complete game state for network transmission"""
        return {
            'players': [player.to_dict() for player in self.players.values()],
            'enemies': [enemy.to_dict() for enemy in self.enemies.values()],
            'bullets': [bullet.to_dict() for bullet in self.bullets.values()],
            'score': self.score,
            'room_id': self.id
        }

sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

game_rooms: Dict[str, GameRoom] = {}

@sio.event
async def connect(sid, environ):
    print(f"🔌 Client {sid} connected")

@sio.event
async def disconnect(sid):
    print(f"🔌 Client {sid} disconnected")

    for room in game_rooms.values():
        if sid in room.players:
            room.remove_player(sid)

            await sio.emit('gameState', room.get_game_state(), room=room.id)
            break

@sio.event
async def joinGame(sid, data):
    player_name = data.get('playerName', 'Player')
    room_id = data.get('roomId', 'room1')

    if room_id not in game_rooms:
        game_rooms[room_id] = GameRoom(room_id)
        print(f"🏠 Created new room: {room_id}")

    room = game_rooms[room_id]

    player = room.add_player(sid, player_name)
    await sio.enter_room(sid, room_id)

    await sio.emit('joinedGame', {
        'success': True,
        'playerId': sid,
        'playerName': player_name,
        'roomId': room_id
    }, room=sid)

    await sio.emit('gameState', room.get_game_state(), room=room_id)

@sio.event
async def playerInput(sid, data):

    for room in game_rooms.values():
        if sid in room.players:
            room.update_player_input(sid, data)
            break

@sio.event
async def playerShoot(sid, data):

    for room in game_rooms.values():
        if sid in room.players:
            room.player_shoot(sid)
            break

async def game_loop():
    """Main game loop - runs at 60 FPS"""
    while True:
        try:

            for room_id, room in list(game_rooms.items()):
                if len(room.players) > 0:
                    room.update()

                    await sio.emit('gameState', room.get_game_state(), room=room_id)
                else:

                    print(f"🗑️ Removing empty room: {room_id}")
                    del game_rooms[room_id]

            await asyncio.sleep(1.0 / GAME_TICK_RATE)

        except Exception as e:
            print(f"❌ Error in game loop: {e}")

async def init_app():
    """Initialize the application"""

    asyncio.create_task(game_loop())
    return app

if __name__ == '__main__':

    print("🚀 Starting Space Shooter Multiplayer Server")
    print(f"📊 Game tick rate: {GAME_TICK_RATE} FPS")
    print(f"🎯 Canvas size: {CANVAS_WIDTH}x{CANVAS_HEIGHT}")
    print(f"👾 Enemy spawn rate: every {ENEMY_SPAWN_RATE} seconds")
    print(f"🌐 Server starting on http://localhost:3000")

    web.run_app(init_app(), host='localhost', port=3000)