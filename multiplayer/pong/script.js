const canvas = document.getElementById('pong');
    const ctx = canvas.getContext('2d');

    let gameState = {
      ballX: 400,
      ballY: 250,
      ballSpeedX: 7,
      ballSpeedY: 7,
      player1Y: 205,
      player2Y: 205,
      player1Score: 0,
      player2Score: 0,
      gameActive: false,
      player1Name: 'Player 1',
      player2Name: 'Player 2'
    };

    let playerNumber = 0;
    let playerName = '';
    let roomId = '';
    let playersInRoom = 0;

    let ws = null;
    let connected = false;
    let demoMode = false;

    let upPressed = false;
    let downPressed = false;
    const moveSpeed = 8;

    const modalOverlay = document.getElementById('modalOverlay');
    const modalMessage = document.getElementById('modalMessage');
    const playAgainBtn = document.getElementById('playAgainBtn');
    const quitBtn = document.getElementById('quitBtn');
    const connectionStatus = document.getElementById('connectionStatus');
    const instructions = document.getElementById('instructions');
    const nameModal = document.getElementById('nameModal');
    const nameInput = document.getElementById('nameInput');
    const joinGameBtn = document.getElementById('joinGameBtn');
    const player1NameEl = document.getElementById('player1Name');
    const player2NameEl = document.getElementById('player2Name');

    setTimeout(() => {
      nameModal.style.display = 'flex';
      nameInput.focus();
    }, 100);

    function connectWebSocket() {

      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }

      try {
        ws = new WebSocket('ws://localhost:8765');
        connectionStatus.textContent = 'Connecting...';
        connectionStatus.className = 'connection-status';
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        fallbackToDemo();
        return;
      }

      ws.onopen = function() {
        connected = true;
        demoMode = false;

        if (demoInterval) {
          clearInterval(demoInterval);
          demoInterval = null;
        }

        gameState = {
          ballX: 400,
          ballY: 250,
          ballSpeedX: 7,
          ballSpeedY: 7,
          player1Y: 205,
          player2Y: 205,
          player1Score: 0,
          player2Score: 0,
          gameActive: false,
          player1Name: playerName,
          player2Name: 'Waiting...'
        };

        ws.send(JSON.stringify({
          type: 'join',
          name: playerName
        }));
      };

      ws.onmessage = function(event) {
        try {
          const data = JSON.parse(event.data);
          handleServerMessage(data);
        } catch (error) {
          console.error('Error parsing server message:', error);
        }
      };

      ws.onclose = function() {
        connected = false;
        connectionStatus.textContent = 'Disconnected - Reconnecting...';
        connectionStatus.className = 'connection-status disconnected';

        setTimeout(() => {
          if (playerName && !demoMode) {
            connectWebSocket();
          }
        }, 3000);
      };

      ws.onerror = function(error) {
        console.error('WebSocket error:', error);
        connected = false;
        connectionStatus.textContent = 'Connection failed - Starting demo mode';
        connectionStatus.className = 'connection-status disconnected';

        setTimeout(() => {
          fallbackToDemo();
        }, 2000);
      };
    }

    function fallbackToDemo() {
      demoMode = true;
      connected = false;
      connectionStatus.textContent = 'Demo Mode - No server connection';
      connectionStatus.className = 'connection-status';

      playerNumber = 1;
      roomId = 'demo';
      playersInRoom = 1;
      gameState.gameActive = true;
      gameState.player1Name = playerName;
      gameState.player2Name = 'AI Player';
      updatePlayerNames();
      updateInstructions();

      startDemoMode();
    }

    function handleServerMessage(data) {
      switch(data.type) {
        case 'connected':
          playerNumber = data.player_number;
          roomId = data.room_id;
          playersInRoom = data.players_in_room;

          if (data.game_state) {
            gameState = { ...gameState, ...data.game_state };
          }

          if (playersInRoom === 2) {
            connectionStatus.textContent = `Connected - Room ${roomId} - Game Ready!`;
            connectionStatus.className = 'connection-status';
            updateInstructions();
          } else {
            connectionStatus.textContent = `Connected - Room ${roomId} - Waiting for opponent...`;
            connectionStatus.className = 'connection-status';
            instructions.innerHTML = `
              <strong>Instructions:</strong><br>
              Waiting for Player 2...<br>
              Share this room: ${roomId}<br>
              First to 10 wins!
            `;
          }
          updatePlayerNames();
          updateScore();
          break;

        case 'game_state':
          gameState = { ...gameState, ...data.data };
          updateScore();
          updatePlayerNames();

          if (!gameState.gameActive && (gameState.player1Score >= 10 || gameState.player2Score >= 10)) {
            setTimeout(() => {
              const winner = gameState.player1Score >= 10 ? gameState.player1Name : gameState.player2Name;
              showModal(`Game Over! ${winner} Wins!`);
            }, 100);
          }
          break;

        case 'player_disconnected':
          connectionStatus.textContent = `Player disconnected - Waiting for opponent...`;
          connectionStatus.className = 'connection-status disconnected';
          gameState.gameActive = false;
          if (data.remaining_player) {
            gameState.player2Name = 'Waiting...';
          }
          updatePlayerNames();
          break;

        case 'error':
          console.error('Server error:', data.message);
          connectionStatus.textContent = 'Server error - Switching to demo mode';
          connectionStatus.className = 'connection-status disconnected';
          setTimeout(() => {
            fallbackToDemo();
          }, 1000);
          break;
      }
    }

    let demoInterval = null;

    function startDemoMode() {

      if (demoInterval) {
        clearInterval(demoInterval);
      }

      demoInterval = setInterval(() => {
        if (gameState.gameActive && demoMode) {

          const paddleCenter = gameState.player2Y + 45;
          const ballY = gameState.ballY;
          const aiSpeed = 4; 

          if (ballY < paddleCenter - 10) {
            gameState.player2Y = Math.max(0, gameState.player2Y - aiSpeed);
          } else if (ballY > paddleCenter + 10) {
            gameState.player2Y = Math.min(410, gameState.player2Y + aiSpeed);
          }

          gameState.ballX += gameState.ballSpeedX;
          gameState.ballY += gameState.ballSpeedY;

          if (gameState.ballY <= 6 || gameState.ballY >= 494) {
            gameState.ballSpeedY = -gameState.ballSpeedY;
          }

          if (gameState.ballX <= 18 && gameState.ballY >= gameState.player1Y && gameState.ballY <= gameState.player1Y + 90) {
            gameState.ballSpeedX = Math.abs(gameState.ballSpeedX);
            gameState.ballSpeedY += (Math.random() - 0.5) * 2;
          }

          if (gameState.ballX >= 782 && gameState.ballY >= gameState.player2Y && gameState.ballY <= gameState.player2Y + 90) {
            gameState.ballSpeedX = -Math.abs(gameState.ballSpeedX);
            gameState.ballSpeedY += (Math.random() - 0.5) * 2;
          }

          if (gameState.ballX < 0) {
            gameState.player2Score++;
            resetBall();
          } else if (gameState.ballX > 800) {
            gameState.player1Score++;
            resetBall();
          }

          if (gameState.player1Score >= 10 || gameState.player2Score >= 10) {
            gameState.gameActive = false;
            const winner = gameState.player1Score >= 10 ? gameState.player1Name : gameState.player2Name;
            setTimeout(() => showModal(`Game Over! ${winner} Wins!`), 100);
          }

          updateScore();
        }
      }, 1000/60);
    }

    function resetBall() {
      gameState.ballX = 400;
      gameState.ballY = 250;
      gameState.ballSpeedX = (Math.random() > 0.5 ? 1 : -1) * 7;
      gameState.ballSpeedY = (Math.random() - 0.5) * 8;
    }

    function updatePlayerNames() {
      if (player1NameEl) player1NameEl.textContent = gameState.player1Name || 'Player 1';
      if (player2NameEl) player2NameEl.textContent = gameState.player2Name || 'Player 2';
    }

    function updateInstructions() {
      const controls = playerNumber === 1 ? 'W / S keys' : '↑ / ↓ keys';
      const mode = connected ? 'Multiplayer' : 'Demo Mode';
      instructions.innerHTML = `
        <strong>Instructions:</strong><br>
        ${mode} - You are Player ${playerNumber}<br>
        Controls: ${controls}<br>
        First to 10 wins!
      `;
    }

    function sendPaddleUpdate() {
      if (!connected || !ws || ws.readyState !== WebSocket.OPEN) return;

      const paddleY = playerNumber === 1 ? gameState.player1Y : gameState.player2Y;

      try {
        ws.send(JSON.stringify({
          type: 'paddle_move',
          y: paddleY
        }));
      } catch (error) {
        console.error('Error sending paddle update:', error);
      }
    }

    function showModal(message) {
      modalMessage.textContent = message;
      modalOverlay.style.display = 'flex';
    }

    function hideModal() {
      modalOverlay.style.display = 'none';
    }

    playAgainBtn.onclick = function() {
      if (connected && ws && ws.readyState === WebSocket.OPEN) {
        try {
          ws.send(JSON.stringify({
            type: 'reset_game'
          }));
        } catch (error) {
          console.error('Error sending reset game:', error);
        }
      } else if (demoMode) {

        gameState.player1Score = 0;
        gameState.player2Score = 0;
        gameState.player1Y = 205;
        gameState.player2Y = 205;
        gameState.gameActive = true;
        resetBall();
        updateScore();
      }
      hideModal();
    };

    quitBtn.onclick = function() {

      if (demoInterval) {
        clearInterval(demoInterval);
        demoInterval = null;
      }
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'disconnect' }));
        ws.close();
      }

      connected = false;
      demoMode = false;
      playerNumber = 0;
      playerName = '';
      roomId = '';
      playersInRoom = 0;

      nameModal.style.display = 'flex';
      nameInput.value = '';
      nameInput.focus();
      connectionStatus.textContent = 'Enter your name to play';
      connectionStatus.className = 'connection-status';
      hideModal();
    };

    function drawRect(x, y, w, h, color) {
      ctx.fillStyle = color;
      ctx.fillRect(x, y, w, h);
    }

    function drawCircle(x, y, r, color) {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.closePath();
      ctx.fill();
    }

    function drawText(text, x, y, color = '#fff', size = 30) {
      ctx.fillStyle = color;
      ctx.font = `${size}px Courier New, monospace`;
      ctx.textAlign = 'center';
      ctx.fillText(text, x, y);
    }

    function updateScore() {
      const scoreElement = document.getElementById("score");
      if (scoreElement) {
        scoreElement.innerHTML = `${gameState.player1Score} &nbsp; | &nbsp; ${gameState.player2Score}`;
      }
    }

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      drawRect(0, 0, canvas.width, canvas.height, '#000');

      for (let i = 0; i < canvas.height; i += 28) {
        drawRect(canvas.width / 2 - 2, i, 4, 18, '#fff');
      }

      drawRect(0, gameState.player1Y, 12, 90, '#fff');
      drawRect(canvas.width - 12, gameState.player2Y, 12, 90, '#fff');

      drawCircle(gameState.ballX, gameState.ballY, 6, '#fff');

      drawText(gameState.player1Score, canvas.width / 4, 55, '#fff', 48);
      drawText(gameState.player2Score, 3 * canvas.width / 4, 55, '#fff', 48);
    }

    function gameLoop() {
      draw();
      requestAnimationFrame(gameLoop);
    }

    document.addEventListener("keydown", function(e) {
      if (!gameState.gameActive) return;

      let moved = false;

      if (playerNumber === 1) {
        if (e.key === "w" || e.key === "W") {
          upPressed = true;
          gameState.player1Y = Math.max(0, gameState.player1Y - moveSpeed);
          moved = true;
        }
        if (e.key === "s" || e.key === "S") {
          downPressed = true;
          gameState.player1Y = Math.min(410, gameState.player1Y + moveSpeed);
          moved = true;
        }
      } else if (playerNumber === 2) {
        if (e.key === "ArrowUp") {
          e.preventDefault();
          upPressed = true;
          gameState.player2Y = Math.max(0, gameState.player2Y - moveSpeed);
          moved = true;
        }
        if (e.key === "ArrowDown") {
          e.preventDefault();
          downPressed = true;
          gameState.player2Y = Math.min(410, gameState.player2Y + moveSpeed);
          moved = true;
        }
      }

      if (moved && connected) {
        sendPaddleUpdate();
      }
    });

    document.addEventListener("keyup", function(e) {
      if (playerNumber === 1) {
        if (e.key === "w" || e.key === "W") upPressed = false;
        if (e.key === "s" || e.key === "S") downPressed = false;
      } else if (playerNumber === 2) {
        if (e.key === "ArrowUp") {
          e.preventDefault();
          upPressed = false;
        }
        if (e.key === "ArrowDown") {
          e.preventDefault();
          downPressed = false;
        }
      }
    });

    setInterval(() => {
      if (!gameState.gameActive) return;

      let moved = false;

      if (playerNumber === 1) {
        if (upPressed) {
          gameState.player1Y = Math.max(0, gameState.player1Y - moveSpeed);
          moved = true;
        }
        if (downPressed) {
          gameState.player1Y = Math.min(410, gameState.player1Y + moveSpeed);
          moved = true;
        }
      } else if (playerNumber === 2) {
        if (upPressed) {
          gameState.player2Y = Math.max(0, gameState.player2Y - moveSpeed);
          moved = true;
        }
        if (downPressed) {
          gameState.player2Y = Math.min(410, gameState.player2Y + moveSpeed);
          moved = true;
        }
      }

      if (moved && connected) {
        sendPaddleUpdate();
      }
    }, 1000 / 60);

    let touchStartY = null;
    let touchCurrentY = null;

    canvas.addEventListener('touchstart', function(e) {
      e.preventDefault();
      const touch = e.touches[0];
      touchStartY = touch.clientY;
      touchCurrentY = touch.clientY;
    });

    canvas.addEventListener('touchmove', function(e) {
      e.preventDefault();
      if (!gameState.gameActive || touchStartY === null) return;

      const touch = e.touches[0];
      const deltaY = touch.clientY - touchCurrentY;
      touchCurrentY = touch.clientY;

      let moved = false;
      const touchSensitivity = 3;

      if (playerNumber === 1) {
        gameState.player1Y = Math.max(0, Math.min(410, gameState.player1Y + deltaY * touchSensitivity));
        moved = true;
      } else if (playerNumber === 2) {
        gameState.player2Y = Math.max(0, Math.min(410, gameState.player2Y + deltaY * touchSensitivity));
        moved = true;
      }

      if (moved && connected) {
        sendPaddleUpdate();
      }
    });

    canvas.addEventListener('touchend', function(e) {
      e.preventDefault();
      touchStartY = null;
      touchCurrentY = null;
    });

    joinGameBtn.onclick = function() {
      const name = nameInput.value.trim();
      if (name === '') {
        alert('Please enter a name!');
        return;
      }

      if (demoInterval) {
        clearInterval(demoInterval);
        demoInterval = null;
      }
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }

      connected = false;
      demoMode = false;
      playerNumber = 0;
      roomId = '';
      playersInRoom = 0;

      playerName = name;
      gameState.player1Name = name;
      gameState.player2Name = 'Waiting...';
      nameModal.style.display = 'none';
      connectionStatus.textContent = 'Attempting to connect...';
      updatePlayerNames();
      connectWebSocket();
    };

    nameInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        joinGameBtn.click();
      }
    });

    gameLoop();