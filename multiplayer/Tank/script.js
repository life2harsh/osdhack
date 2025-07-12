const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');

        let gameState = {
            tanks: {},
            bullets: [],
            obstacles: [],
            powerups: [],
            teams: {},
            flags: []
        };

        let myTankId = null;
        let playerName = '';
        let selectedTankClass = 'light';
        let selectedGameMode = 'deathmatch';
        let currentRoom = null;
        let ws = null;
        let connected = false;

        const tankClasses = {
            light: {
                name: 'LIGHT TANK',
                speed: 120,
                health: 75,
                armor: 0.8,
                fireRate: 0.2,
                damage: 20,
                color: '#00ff00',
                size: 12
            },
            medium: {
                name: 'MEDIUM TANK',
                speed: 80,
                health: 100,
                armor: 0.6,
                fireRate: 0.4,
                damage: 30,
                color: '#ffff00',
                size: 15
            },
            heavy: {
                name: 'HEAVY TANK',
                speed: 50,
                health: 150,
                armor: 0.4,
                fireRate: 0.6,
                damage: 35,
                color: '#ff8800',
                size: 18
            },
            artillery: {
                name: 'ARTILLERY',
                speed: 30,
                health: 80,
                armor: 0.7,
                fireRate: 1.0,
                damage: 60,
                color: '#ff0000',
                size: 16
            }
        };

        let keys = {
            up: false,
            down: false,
            left: false,
            right: false,
            space: false,
            escape: false
        };

        const mainMenu = document.getElementById('mainMenu');
        const gameContainer = document.getElementById('gameContainer');
        const nameInput = document.getElementById('nameInput');
        const roomInput = document.getElementById('roomInput');
        const joinBtn = document.getElementById('joinBtn');
        const refreshRoomsBtn = document.getElementById('refreshRoomsBtn');
        const connectionStatus = document.getElementById('connectionStatus');
        const respawnModal = document.getElementById('respawnModal');
        const respawnTimer = document.getElementById('respawnTimer');
        const healthEl = document.getElementById('health');
        const ammoEl = document.getElementById('ammo');
        const killsEl = document.getElementById('kills');
        const deathsEl = document.getElementById('deaths');
        const tankClassEl = document.getElementById('tankClass');
        const leaderboardList = document.getElementById('leaderboardList');
        const teamInfo = document.getElementById('teamInfo');
        const gameMode = document.getElementById('gameMode');
        const teamStatus = document.getElementById('teamStatus');
        const roomList = document.getElementById('roomList');

        nameInput.focus();

        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                selectedGameMode = btn.dataset.mode;

                if (selectedGameMode === 'team' || selectedGameMode === 'capture') {

                    roomList.style.display = 'block';
                    refreshRooms();
                } else {
                    roomList.style.display = 'none';
                }
            });
        });

        document.querySelectorAll('.tank-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.tank-option').forEach(o => o.classList.remove('selected'));
                option.classList.add('selected');
                selectedTankClass = option.dataset.tank;
                tankClassEl.textContent = tankClasses[selectedTankClass].name;
            });
        });

        function connectToServer() {
            try {
                ws = new WebSocket('ws://localhost:8765');

                ws.onopen = () => {
                    connected = true;
                    connectionStatus.textContent = 'CONNECTED';
                    connectionStatus.className = 'connection-status connected';

                    const roomCode = roomInput.value.trim() || null;
                    ws.send(JSON.stringify({
                        type: 'join',
                        name: playerName,
                        tankClass: selectedTankClass,
                        gameMode: selectedGameMode,
                        roomCode: roomCode
                    }));
                };

                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        handleServerMessage(data);
                    } catch (error) {
                        console.error('Error parsing server message:', error);
                    }
                };

                ws.onclose = () => {
                    connected = false;
                    connectionStatus.textContent = 'DISCONNECTED';
                    connectionStatus.className = 'connection-status disconnected';

                    setTimeout(() => {
                        if (playerName && !mainMenu.style.display) {
                            connectToServer();
                        }
                    }, 3000);
                };

                ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    connected = false;
                    connectionStatus.textContent = 'CONNECTION FAILED';
                    connectionStatus.className = 'connection-status disconnected';
                };

            } catch (error) {
                console.error('Failed to create WebSocket connection:', error);
                connectionStatus.textContent = 'CONNECTION FAILED';
                connectionStatus.className = 'connection-status disconnected';
            }
        }

        function refreshRooms() {
            if (connected && ws) {
                ws.send(JSON.stringify({
                    type: 'get_rooms',
                    gameMode: selectedGameMode
                }));
            }
        }

        function handleServerMessage(data) {
            switch (data.type) {
                case 'game_state':
                    gameState = data.state;
                    updateHUD();
                    updateLeaderboard(data.leaderboard);
                    updateTeamInfo(data.teamInfo);
                    break;

                case 'tank_assigned':
                    myTankId = data.tank_id;
                    currentRoom = data.room_id;
                    mainMenu.style.display = 'none';
                    gameContainer.style.display = 'block';
                    break;

                case 'tank_destroyed':
                    if (data.tank_id === myTankId) {
                        showRespawnModal();
                    }
                    break;

                case 'tank_respawned':
                    if (data.tank_id === myTankId) {
                        hideRespawnModal();
                    }
                    break;

                case 'room_list':
                    updateRoomList(data.rooms);
                    break;

                case 'powerup_collected':
                    if (data.tank_id === myTankId) {
                        showPowerupEffect(data.powerup_type, data.value);
                    }
                    break;

                case 'error':
                    console.error('Server error:', data.message);
                    alert('ERROR: ' + data.message);
                    break;
            }
        }

        function updateRoomList(rooms) {
            if (!rooms || rooms.length === 0) {
                roomList.innerHTML = '<div class="room-item">NO ROOMS AVAILABLE</div>';
                return;
            }

            roomList.innerHTML = rooms.map(room => `
                <div class="room-item" onclick="joinRoom('${room.id}')">
                    ${room.name} (${room.players}/${room.maxPlayers}) - ${room.mode.toUpperCase()}
                </div>
            `).join('');
        }

        function joinRoom(roomId) {
            roomInput.value = roomId;
        }

        function sendInput() {
            if (!connected || !ws || ws.readyState !== WebSocket.OPEN) return;

            const inputState = {
                up: keys.up,
                down: keys.down,
                left: keys.left,
                right: keys.right,
                fire: keys.space
            };

            ws.send(JSON.stringify({
                type: 'input',
                input: inputState
            }));
        }

        function updateHUD() {
            if (myTankId && gameState.tanks[myTankId]) {
                const myTank = gameState.tanks[myTankId];
                healthEl.textContent = Math.max(0, myTank.health);
                killsEl.textContent = myTank.kills || 0;
                deathsEl.textContent = myTank.deaths || 0;
                tankClassEl.textContent = tankClasses[myTank.tankClass]?.name || 'UNKNOWN';
            }
        }

        function updateLeaderboard(leaderboard) {
            if (!leaderboard) return;

            let html = '';
            leaderboard.slice(0, 8).forEach((player, index) => {
                const prefix = index === 0 ? '█' : index === 1 ? '▲' : index === 2 ? '♦' : '•';
                const teamColor = player.team ? `team-${player.team}` : '';
                html += `<div class="${teamColor}">${prefix} ${player.name}: ${player.kills}</div>`;
            });
            leaderboardList.innerHTML = html || 'NO PLAYERS';
        }

        function updateTeamInfo(teamInfo) {
            if (!teamInfo) return;

            gameMode.textContent = teamInfo.mode.toUpperCase() + ' MODE';

            if (teamInfo.mode === 'team' || teamInfo.mode === 'capture') {
                const myTank = gameState.tanks[myTankId];
                const myTeam = myTank ? myTank.team : null;
                teamStatus.innerHTML = myTeam ? 
                    `TEAM: <span class="team-${myTeam}">${myTeam.toUpperCase()}</span>` : 
                    'NO TEAM ASSIGNED';
            } else {
                teamStatus.textContent = 'FREE FOR ALL';
            }
        }

        function showPowerupEffect(type, value) {

            const effect = document.createElement('div');
            effect.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: #00ff00;
                font-size: 12px;
                font-family: 'Press Start 2P', monospace;
                z-index: 3000;
                pointer-events: none;
                animation: powerupFade 2s ease-out forwards;
            `;

            if (type === 'health') {
                effect.textContent = `+${value} HEALTH`;
                effect.style.color = '#00ff00';
            } else if (type === 'speed') {
                effect.textContent = 'SPEED BOOST!';
                effect.style.color = '#ffff00';
            } else if (type === 'damage') {
                effect.textContent = 'DAMAGE BOOST!';
                effect.style.color = '#ff8800';
            }

            document.body.appendChild(effect);
            setTimeout(() => effect.remove(), 2000);
        }

        function showRespawnModal() {
            respawnModal.style.display = 'block';
            let countdown = 3;

            const timer = setInterval(() => {
                respawnTimer.textContent = `RESPAWNING IN ${countdown}...`;
                countdown--;

                if (countdown < 0) {
                    clearInterval(timer);
                    hideRespawnModal();
                }
            }, 1000);
        }

        function hideRespawnModal() {
            respawnModal.style.display = 'none';
        }

        function returnToMenu() {
            if (ws && connected) {
                ws.send(JSON.stringify({ type: 'leave_game' }));
                ws.close();
            }

            mainMenu.style.display = 'flex';
            gameContainer.style.display = 'none';
            connected = false;
            myTankId = null;
            currentRoom = null;
            gameState = { tanks: {}, bullets: [], obstacles: [], powerups: [], teams: {}, flags: [] };
        }

        function drawTank(tank) {
            ctx.save();
            ctx.translate(tank.x, tank.y);
            ctx.rotate(tank.angle);

            const tankClass = tankClasses[tank.tankClass] || tankClasses.light;
            const size = tankClass.size;

            ctx.fillStyle = tank.id === myTankId ? '#00ff00' : (tank.team ? getTeamColor(tank.team) : '#ff4444');
            ctx.fillRect(-size, -size * 0.6, size * 2, size * 1.2);

            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1;
            ctx.strokeRect(-size, -size * 0.6, size * 2, size * 1.2);

            ctx.fillStyle = '#888888';
            ctx.fillRect(size * 0.8, -2, size * 1.5, 4);
            ctx.strokeRect(size * 0.8, -2, size * 1.5, 4);

            ctx.fillStyle = '#444444';
            ctx.fillRect(-size, -size * 0.8, size * 2, 4);
            ctx.fillRect(-size, size * 0.4, size * 2, 4);

            ctx.restore();

            const healthPercent = Math.max(0, tank.health) / tank.maxHealth;
            const barWidth = 30;
            const barHeight = 6;
            const barX = tank.x - barWidth / 2;
            const barY = tank.y - 30;

            ctx.fillStyle = '#330000';
            ctx.fillRect(barX, barY, barWidth, barHeight);

            ctx.fillStyle = healthPercent > 0.6 ? '#00ff00' : healthPercent > 0.3 ? '#ffff00' : '#ff0000';
            ctx.fillRect(barX, barY, barWidth * healthPercent, barHeight);

            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1;
            ctx.strokeRect(barX, barY, barWidth, barHeight);

            ctx.fillStyle = tank.team ? getTeamColor(tank.team) : '#00ff00';
            ctx.font = '8px "Press Start 2P"';
            ctx.textAlign = 'center';
            ctx.fillText(tank.name, tank.x, tank.y - 40);
        }

        function drawBullet(bullet) {
            ctx.fillStyle = '#ffff00';
            ctx.fillRect(bullet.x - 2, bullet.y - 2, 4, 4);

            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1;
            ctx.strokeRect(bullet.x - 2, bullet.y - 2, 4, 4);
        }

        function drawObstacle(obstacle) {

            ctx.fillStyle = '#666666';
            ctx.fillRect(obstacle.x, obstacle.y, obstacle.width, obstacle.height);

            ctx.strokeStyle = '#888888';
            ctx.lineWidth = 1;

            const brickWidth = 20;
            const brickHeight = 10;

            for (let y = 0; y < obstacle.height; y += brickHeight) {
                for (let x = 0; x < obstacle.width; x += brickWidth) {
                    const offsetX = (Math.floor(y / brickHeight) % 2) * (brickWidth / 2);
                    ctx.strokeRect(obstacle.x + x + offsetX, obstacle.y + y, brickWidth, brickHeight);
                }
            }

            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2;
            ctx.strokeRect(obstacle.x, obstacle.y, obstacle.width, obstacle.height);
        }

        function drawPowerup(powerup) {
            ctx.save();
            ctx.translate(powerup.x, powerup.y);

            const flash = Math.sin(Date.now() * 0.01) > 0;

            if (powerup.type === 'health') {
                ctx.fillStyle = flash ? '#00ff00' : '#008800';
                ctx.fillRect(-8, -8, 16, 16);
                ctx.fillStyle = '#ffffff';
                ctx.font = '12px "Press Start 2P"';
                ctx.textAlign = 'center';
                ctx.fillText('+', 0, 4);
            } else if (powerup.type === 'speed') {
                ctx.fillStyle = flash ? '#ffff00' : '#888800';
                ctx.fillRect(-8, -8, 16, 16);
                ctx.fillStyle = '#ffffff';
                ctx.font = '8px "Press Start 2P"';
                ctx.textAlign = 'center';
                ctx.fillText('S', 0, 2);
            } else if (powerup.type === 'damage') {
                ctx.fillStyle = flash ? '#ff8800' : '#884400';
                ctx.fillRect(-8, -8, 16, 16);
                ctx.fillStyle = '#ffffff';
                ctx.font = '8px "Press Start 2P"';
                ctx.textAlign = 'center';
                ctx.fillText('!', 0, 2);
            }

            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2;
            ctx.strokeRect(-8, -8, 16, 16);

            ctx.restore();
        }

        function drawFlag(flag) {
            ctx.save();
            ctx.translate(flag.x, flag.y);

            ctx.fillStyle = '#888888';
            ctx.fillRect(-2, -30, 4, 60);

            const teamColor = getTeamColor(flag.team);
            ctx.fillStyle = flag.captured ? '#666666' : teamColor;

            const wave = Math.sin(Date.now() * 0.005) * 3;
            ctx.beginPath();
            ctx.moveTo(2, -25);
            ctx.lineTo(20 + wave, -20);
            ctx.lineTo(15 + wave, -10);
            ctx.lineTo(20 + wave, 0);
            ctx.lineTo(2, -5);
            ctx.closePath();
            ctx.fill();

            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1;
            ctx.stroke();

            ctx.restore();
        }

        function getTeamColor(team) {
            const colors = {
                red: '#ff4444',
                blue: '#4444ff',
                green: '#44ff44',
                yellow: '#ffff44'
            };
            return colors[team] || '#ffffff';
        }

        function render() {

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            ctx.fillStyle = '#001100';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.strokeStyle = 'rgba(0, 255, 0, 0.1)';
            ctx.lineWidth = 1;
            const gridSize = 25;

            for (let x = 0; x < canvas.width; x += gridSize) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }
            for (let y = 0; y < canvas.height; y += gridSize) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }

            gameState.obstacles.forEach(drawObstacle);
            gameState.powerups.forEach(drawPowerup);
            gameState.flags?.forEach(drawFlag);
            gameState.bullets.forEach(drawBullet);
            Object.values(gameState.tanks).forEach(drawTank);

            requestAnimationFrame(render);
        }

        document.addEventListener('keydown', (e) => {
if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
   return;
}

if (mainMenu.style.display !== 'none') {
   return;
}

            switch (e.code) {
                case 'ArrowUp':
                case 'KeyW':
                    keys.up = true;
                    e.preventDefault();
                    break;
                case 'ArrowDown':
                case 'KeyS':
                    keys.down = true;
                    e.preventDefault();
                    break;
                case 'ArrowLeft':
                case 'KeyA':
                    keys.left = true;
                    e.preventDefault();
                    break;
                case 'ArrowRight':
                case 'KeyD':
                    keys.right = true;
                    e.preventDefault();
                    break;
                case 'Space':
                    keys.space = true;
                    e.preventDefault();
                    break;
                case 'Escape':
                    if (gameContainer.style.display !== 'none') {
                        returnToMenu();
                    }
                    e.preventDefault();
                    break;
            }
        });

        document.addEventListener('keyup', (e) => {
if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
   return;
}

if (mainMenu.style.display !== 'none') {
   return;
}
            switch (e.code) {
                case 'ArrowUp':
                case 'KeyW':
                    keys.up = false;
                    break;
                case 'ArrowDown':
                case 'KeyS':
                    keys.down = false;
                    break;
                case 'ArrowLeft':
                case 'KeyA':
                    keys.left = false;
                    break;
                case 'ArrowRight':
                case 'KeyD':
                    keys.right = false;
                    break;
                case 'Space':
                    keys.space = false;
                    break;
            }
        });

        joinBtn.addEventListener('click', () => {
            const name = nameInput.value.trim();
            if (name) {
                playerName = name.toUpperCase();
                connectionStatus.textContent = 'CONNECTING...';
                connectionStatus.className = 'connection-status connecting';
                connectToServer();
            } else {
                alert('ENTER COMMANDER NAME!');
            }
        });

        refreshRoomsBtn.addEventListener('click', () => {
            if (connected) {
                refreshRooms();
            } else {

                connectToServer();
                setTimeout(() => {
                    if (connected) {
                        refreshRooms();
                    }
                }, 1000);
            }
        });

        nameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                joinBtn.click();
            }
        });

        roomInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                joinBtn.click();
            }
        });

        setInterval(() => {
            if (connected && myTankId && gameContainer.style.display !== 'none') {
                sendInput();
            }
        }, 1000 / 60); 

        render();

        const style = document.createElement('style');
        style.textContent = `
            @keyframes powerupFade {
                0% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                50% { opacity: 1; transform: translate(-50%, -60%) scale(1.2); }
                100% { opacity: 0; transform: translate(-50%, -80%) scale(0.8); }
            }
        `;
        document.head.appendChild(style);

        let touchStartX, touchStartY;
        let touchControls = { move: false, fire: false };

        canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const rect = canvas.getBoundingClientRect();
            touchStartX = touch.clientX - rect.left;
            touchStartY = touch.clientY - rect.top;

            const currentTime = new Date().getTime();
            if (currentTime - (touchControls.lastTap || 0) < 300) {
                keys.space = true;
                setTimeout(() => keys.space = false, 100);
            }
            touchControls.lastTap = currentTime;
        });

        canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            if (!touchStartX || !touchStartY) return;

            const touch = e.touches[0];
            const rect = canvas.getBoundingClientRect();
            const touchX = touch.clientX - rect.left;
            const touchY = touch.clientY - rect.top;

            const deltaX = touchX - touchStartX;
            const deltaY = touchY - touchStartY;

            keys.up = keys.down = keys.left = keys.right = false;

            if (Math.abs(deltaX) > Math.abs(deltaY)) {
                if (Math.abs(deltaX) > 20) {
                    keys.right = deltaX > 0;
                    keys.left = deltaX < 0;
                }
            } else {
                if (Math.abs(deltaY) > 20) {
                    keys.down = deltaY > 0;
                    keys.up = deltaY < 0;
                }
            }
        });

        canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            keys.up = keys.down = keys.left = keys.right = false;
            touchStartX = touchStartY = null;
        });