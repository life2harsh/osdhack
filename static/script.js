let socket = null;
let username = '';
let isConnected = false;
let currentUser = null;
let peerConnection = null;
let localStream = null;
let isVoiceEnabled = false;
let isMuted = false;
let pendingFile = null;
let pendingReceiver = null;
let pendingEmitEvent = null;
let currentPMConversations = [];
let currentPMUser = null;
let currentPMMessages = [];

function makePayload(receiver, content, msgType='text') {
   msgType = msgType.toLowerCase();
   if (msgType !== 'text' && msgType !== 'file') {
       console.error('Invalid message type', msgType);
       return null;
   }
   return {
       sender_name: username,
       receiver_name: receiver,
       type: msgType,
       data: content,
       timestamp: new Date().toISOString()
   };
}

function sendPendingFile() {
   if (!pendingFile || !pendingReceiver || !pendingEmitEvent) return;
   const reader = new FileReader();
   reader.onload = () => {
       const base64 = reader.result.split(',')[1];
       const payload = makePayload(
           pendingReceiver,
           { filename: pendingFile.name, blob: base64 },
           'file'
       );
       socket.emit(pendingEmitEvent, payload);
       pendingFile = pendingReceiver = pendingEmitEvent = null;
       document.getElementById('hiddenFileInput').value = '';
   };
   reader.readAsDataURL(pendingFile);
}

function scrollToBottom() {
   const messagesDiv = document.getElementById('messages');
   if (!messagesDiv) return;

   const scrollToBottomImmediate = () => {
       messagesDiv.scrollTop = messagesDiv.scrollHeight;
   };

   scrollToBottomImmediate();

   requestAnimationFrame(() => {
       scrollToBottomImmediate();

       requestAnimationFrame(() => {
           scrollToBottomImmediate();
       });
   });

   setTimeout(scrollToBottomImmediate, 0);
   setTimeout(scrollToBottomImmediate, 10);
   setTimeout(scrollToBottomImmediate, 50);
}

function addMsg(html, cls='') {
   const messagesDiv = document.getElementById('messages');
   if (!messagesDiv) return;

   const div = document.createElement('div');
   div.className = `msg message-output ${cls}`;

   const timestamp = new Date().toLocaleTimeString();
   div.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${html}`;

   messagesDiv.appendChild(div);

   scrollToBottom();
}

function startUsersAutoRefresh() {
   if (window.usersRefreshInterval) {
       clearInterval(window.usersRefreshInterval);
   }

   window.usersRefreshInterval = setInterval(() => {
       if (socket && isConnected) {
           socket.emit('get_users');
       }
   }, 30000); 
}

function stopUsersAutoRefresh() {
   if (window.usersRefreshInterval) {
       clearInterval(window.usersRefreshInterval);
       window.usersRefreshInterval = null;
   }
}

function updateUsersOnlineDisplay(users) {

   const countSpan = document.getElementById('usersOnlineCount');
   if (countSpan) {
       countSpan.textContent = users.length;
   }

   const userListContainer = document.getElementById('userListContainer');
   if (userListContainer) {
       userListContainer.innerHTML = '';

       if (users.length === 0) {
           const emptyDiv = document.createElement('div');
           emptyDiv.className = 'user-list-empty';
           emptyDiv.textContent = 'No users online';
           userListContainer.appendChild(emptyDiv);
       } else {
           users.forEach((user, index) => {
               const userDiv = document.createElement('div');
               userDiv.className = 'user-item';
               userDiv.onclick = () => startPrivateMessage(user);

               let status = 'Online';
               let statusClass = 'user-status';

               if (user === username) {
                   status = 'You';
                   statusClass += ' user-status-self';
               }

               userDiv.innerHTML = `
                   <span class="user-name">${user}</span>
                   <span class="${statusClass}">${status}</span>
               `;

               userListContainer.appendChild(userDiv);
           });
       }
   }

   const sidebarUserList = document.getElementById('users');
   if (sidebarUserList) {
       sidebarUserList.innerHTML = users.map(u => `<li>${u}</li>`).join('');
   }
}

function startPrivateMessage(targetUser) {
   if (targetUser === username) {
       return; 
   }

   if (document.getElementById('bbsMainMenu').style.display === 'block' || 
       document.getElementById('pmConversationsMenu').style.display === 'block') {
       openPMChat(targetUser);
   } else {

       const message = prompt(`Send private message to ${targetUser}:`);
       if (message && message.trim()) {
           hideBBSMainMenu();
           executeQuickCommand(`/pm ${targetUser} ${message.trim()}`);
       }
   }
}

function showBBSMainMenu() {

   document.getElementById('bootScreen').style.display = 'none';

   const mainInterface = document.getElementById('mainInterface');
   mainInterface.style.visibility = 'hidden';
   mainInterface.style.opacity = '0';
   mainInterface.style.pointerEvents = 'none';

   document.getElementById('bbsMainMenu').style.display = 'block';

   updateBBSStatus();
   updateBBSTime();

   if (socket) {
       socket.emit('get_users');
       socket.emit('check_rooms');
   }

   startUsersAutoRefresh();

   if (window.bbsTimeInterval) {
       clearInterval(window.bbsTimeInterval);
   }
   window.bbsTimeInterval = setInterval(updateBBSTime, 1000);
}

function hideBBSMainMenu() {

   document.getElementById('bbsMainMenu').style.display = 'none';
   document.getElementById('bootScreen').style.display = 'none';

   const mainInterface = document.getElementById('mainInterface');
   mainInterface.style.visibility = 'visible';
   mainInterface.style.opacity = '1';
   mainInterface.style.pointerEvents = 'auto';

   mainInterface.offsetHeight; 

   stopUsersAutoRefresh();

   initializeTerminal();

   setTimeout(() => scrollToBottom(), 10);
   setTimeout(() => scrollToBottom(), 50);
   setTimeout(() => scrollToBottom(), 100);
}

function updateBBSStatus() {
   const userSpan = document.getElementById('bbsCurrentUser');
   if (userSpan) {
       userSpan.textContent = username || 'GUEST';
   }
}

function updateBBSTime() {
   const timeSpan = document.getElementById('bbsSystemTime');
   if (timeSpan) {
       const now = new Date();
       timeSpan.textContent = now.toTimeString().split(' ')[0];
   }
}

function selectBBSOption(option) {
   document.getElementById('bbsCommandInput').value = option;
   executeBBSChoice();
}

function handleBBSInput(event) {
   if (event.key === 'Enter') {
       executeBBSChoice();
   }
}

function executeBBSChoice() {
   const input = document.getElementById('bbsCommandInput');
   const choice = input.value.trim().toUpperCase();
   input.value = '';

   switch (choice) {
       case '1':
           hideBBSMainMenu();
           logMessage('[SYSTEM] Adventure Games selected. Use /startadventure or /joinadventure commands.', 'adventure-msg');
           break;
       case '2':
       case '3':
       case '4':
           hideBBSMainMenu();
           logMessage('[SYSTEM] Feature not yet implemented.', 'system-msg');
           break;
       case '5':
       case '6':
           hideBBSMainMenu();
           logMessage('[SYSTEM] Voice chat available. Use voice controls in terminal.', 'system-msg');
           break;
       case 'DM':
           showPMConversations();
           break;
       case 'U':
       case 'W':
           hideBBSMainMenu();
           executeQuickCommand('/users');
           break;
       case 'S':
           hideBBSMainMenu();
           showSystemInfo();
           break;
       case 'R1':
           hideBBSMainMenu();
           executeQuickCommand('/join general');
           break;
       case 'R2':
           hideBBSMainMenu();
           executeQuickCommand('/join support');
           break;
       case 'R3':
           hideBBSMainMenu();
           executeQuickCommand('/join files');
           break;
       case 'R4':
           hideBBSMainMenu();
           executeQuickCommand('/join lounge');
           break;
       case 'J':
           hideBBSMainMenu();
           const roomToJoin = prompt('Enter room name to join:');
           if (roomToJoin) {
               executeQuickCommand(`/join ${roomToJoin}`);
           }
           break;
       case 'L':
           hideBBSMainMenu();
           const roomToLeave = prompt('Enter room name to leave:');
           if (roomToLeave) {
               executeQuickCommand(`/leave ${roomToLeave}`);
           }
           break;
       case 'M':
           hideBBSMainMenu();
           const message = prompt('Enter your message:');
           if (message) {
               document.getElementById('commandInput').value = message;
               executeCommand();
           }
           break;
       case 'P':
           hideBBSMainMenu();
           const dmUser = prompt('Enter username for private message:');
           if (dmUser) {
               const dmMessage = prompt('Enter your message:');
               if (dmMessage) {
                   executeQuickCommand(`/pm ${dmUser} ${dmMessage}`);
               }
           }
           break;
       case 'F':
           hideBBSMainMenu();
           showFileModal();
           break;
       case 'H':
           hideBBSMainMenu();
           executeQuickCommand('/history');
           break;
       case 'T':
           showThemeSelector();
           break;
       case 'Q':
           logout();
           break;
       default:
           if (choice) {
               hideBBSMainMenu();
               document.getElementById('commandInput').value = choice.toLowerCase();
               executeCommand();
           }
           break;
   }
}

function showSystemInfo() {
   const info = `
[SYSTEM INFORMATION]
RobCo Industries (TM) Termlink v2.1.7
BBS Network Access Protocol
Voice Chat Module: ${isVoiceEnabled ? 'ACTIVE' : 'INACTIVE'}
File Transmission: READY
Current Theme: ${document.documentElement.getAttribute('data-theme') || 'amber'}
Connection Status: ${isConnected ? 'ONLINE' : 'OFFLINE'}
User: ${username || 'GUEST'}
Uptime: ${window.startTime ? Math.floor((Date.now() - window.startTime) / 1000) + 's' : 'Unknown'}
   `;
   logMessage(info, 'adventure-msg');
}

function executeQuickCommand(command) {

   const mainInterface = document.getElementById('mainInterface');
   if (mainInterface.style.visibility === 'hidden') {
       hideBBSMainMenu();

       setTimeout(() => {
           document.getElementById('commandInput').value = command;
           executeCommand();
       }, 50);
   } else {
       document.getElementById('commandInput').value = command;
       executeCommand();
   }
}

function executeCommand() {
   const commandInput = document.getElementById('commandInput');
   const command = commandInput.value.trim();

   if (!command || !isConnected || !socket) return;

   const parts = command.split(' ');
   const cmd = parts[0].toLowerCase();

   if (cmd.startsWith('/')) {
       logMessage(`> ${command}`, 'system-msg');
   }

   processCommand(command);
   commandInput.value = '';

   scrollToBottom();
}

function processCommand(command) {
   if (!socket) return;

   const parts = command.split(' ');
   const cmd = parts[0].toLowerCase();

   if (cmd === '/users') {
       socket.emit('get_users');
   } else if (cmd === '/rooms') {
       socket.emit('check_rooms');
   } else if (cmd === '/pm_list') {
       socket.emit('get_pm_list');
   } else if (cmd === '/history') {
       if (parts.length === 1) {
           socket.emit('get_chat_history');
       } else if (parts.length === 2) {
           const target = parts[1];
           if (/^\d+$/.test(target)) {

               socket.emit('get_chat_history', {type: 'adventure', target: target});
           } else {

               logMessage(`Specify history type for '${target}':`, 'system-msg');
               logMessage('/history_room <name> - for room history', 'system-msg');
               logMessage('/history_pm <username> - for private message history', 'system-msg');
           }
       } else {
           logMessage('Usage: /history [target] or use /history_room or /history_pm for clarity', 'system-msg');
       }
   } else if (cmd === '/history_room') {
       if (parts.length === 2) {
           socket.emit('get_chat_history', {type: 'room', target: parts[1]});
       } else {
           logMessage('Usage: /history_room <room_name>', 'system-msg');
       }
   } else if (cmd === '/history_pm') {
       if (parts.length === 2) {
           socket.emit('get_chat_history', {type: 'private', target: parts[1]});
       } else {
           logMessage('Usage: /history_pm <username>', 'system-msg');
       }
   } else if (cmd === '/pm') {
       if (parts.length >= 3) {
           const user = parts[1];
           if (parts[2] === 'file') {

               pendingReceiver = user;
               pendingEmitEvent = 'private_message';
               document.getElementById('hiddenFileInput').click();
           } else {
               const msg = parts.slice(2).join(' ');
               socket.emit('private_message', makePayload(user, msg));
           }
       } else {
           logMessage('USAGE: /pm <username> <message> OR /pm <username> file', 'server-msg');
       }
   } else if (cmd === '/join') {
       if (parts.length >= 2) {
           socket.emit('join_room', { room: parts[1] });
           logMessage(`JOINING ROOM: ${parts[1]}`, 'system-msg');
       } else {
           logMessage('USAGE: /join <room>', 'server-msg');
       }
   } else if (cmd === '/leave') {
       if (parts.length >= 2) {
           socket.emit('leave_room', { room: parts[1] });
           logMessage(`LEAVING ROOM: ${parts[1]}`, 'system-msg');
       } else {
           logMessage('USAGE: /leave <room>', 'server-msg');
       }
   } else if (cmd === '/newroom') {
       if (parts.length >= 2) {
           const roomName = parts[1];
           const description = parts.slice(2).join(' ') || '';
           socket.emit('create_room', { room_name: roomName, description: description });
       } else {
           logMessage('Usage: /newroom <room_name> [description]', 'system-msg');
       }
   } else if (cmd === '/room') {
       if (parts.length >= 3) {
           const room = parts[1];
           if (parts[2] === 'file') {

               pendingReceiver = room;
               pendingEmitEvent = 'room_message';
               document.getElementById('hiddenFileInput').click();
           } else {
               const msg = parts.slice(2).join(' ');
               socket.emit('room_message', makePayload(room, msg));
           }
       } else {
           logMessage('USAGE: /room <room> <message> OR /room <room> file', 'server-msg');
       }
   } else if (cmd === '/startadventure') {
       if (parts.length >= 3) {
           const story = parts[1];
           const users = parts[2].split(',').map(u => u.trim());
           socket.emit('start_adventure', { story: story, users: users });
       } else {
           logMessage('USAGE: /startadventure <story> <user1,user2,...>', 'server-msg');
       }
   } else if (cmd === '/joinadventure') {
       if (parts.length >= 3) {
           socket.emit('join_adventure', { room_id: parts[1], role: parts[2] });
       } else {
           logMessage('USAGE: /joinadventure <room_id> <role>', 'server-msg');
       }
   } else if (cmd === '/adventure') {
       if (parts.length >= 3) {
           const room = parts[1];
           if (parts[2] === 'file') {

               pendingReceiver = room;
               pendingEmitEvent = 'adventure_message';
               document.getElementById('hiddenFileInput').click();
           } else {
               const msg = parts.slice(2).join(' ');
               socket.emit('adventure_message', makePayload(room, msg));
           }
       } else {
           logMessage('USAGE: /adventure <room_id> <message> OR /adventure <room_id> file', 'server-msg');
       }
   } else if (cmd === '/adventureinfo') {
       if (parts.length >= 2) {
           socket.emit('get_adventure_info', { room_id: parts[1] });
       } else {
           logMessage('USAGE: /adventureinfo <room_id>', 'server-msg');
       }
   } else if (cmd === '/theme') {
       showThemeSelector();
   } else if (cmd === 'file') {

       pendingReceiver = 'all';
       pendingEmitEvent = 'chat_message';
       document.getElementById('hiddenFileInput').click();
   } else {

       socket.emit('chat_message', makePayload('all', command, 'text'));
   }
}

function showHelp() {
   const helpText = `
[BBS NETWORK PROTOCOLS]
/pm <user> <message> - SEND PRIVATE MESSAGE
/pm <user> file - SEND PRIVATE FILE
/join <room> - JOIN ROOM
/leave <room> - LEAVE ROOM
/newroom <room> [description] - CREATE NEW ROOM
/room <room> <message> - SEND ROOM MESSAGE
/room <room> file - SEND ROOM FILE
/startadventure <story> <user1,user2,...> - START ADVENTURE
/joinadventure <room_id> <role> - JOIN ADVENTURE
/adventure <room_id> <message> - SEND ADVENTURE MESSAGE
/adventure <room_id> file - SEND ADVENTURE FILE
/adventureinfo <room_id> - GET ADVENTURE INFO
/users - LIST ACTIVE USERS
/rooms - LIST JOINED ROOMS
/pm_list - LIST PRIVATE MESSAGE CONVERSATIONS
/history - GET GLOBAL CHAT HISTORY
/history_room <room> - GET ROOM HISTORY
/history_pm <user> - GET PRIVATE MESSAGE HISTORY
/theme - CHANGE VISUAL THEME
file - SEND FILE TO GLOBAL CHAT

[DIRECT MESSAGES SYSTEM]
DM - ACCESS DISCORD-LIKE DIRECT MESSAGES INTERFACE
- Click on users to start conversations
- Real-time message interface
- File sharing in DMs
- Message history

[VOICE COMMANDS]
ENABLE VOICE - ACTIVATE VOICE CHAT
MUTE MIC - MUTE/UNMUTE MICROPHONE

[FILE TRANSMISSION]
Use 📎 FILE button for file uploads or commands above

[KEYBOARD SHORTCUTS]
Ctrl+L - Clear screen
Ctrl+U - Show users
Ctrl+R - Show rooms
Ctrl+H - Show help
Ctrl+F - File upload
Ctrl+Shift+T - Theme selector
Ctrl+M - BBS Menu
ESC - Navigate back through interfaces
   `;
   logMessage(helpText, 'adventure-msg');
}

function clearTerminal() {
   document.getElementById('messages').innerHTML = '<div class="loading-bar"></div>';
}

function handleCommandInput(event) {
   if (event.key === 'Enter') {
       executeCommand();
   }
}

function showFileModal() {
   document.getElementById('fileModal').style.display = 'flex';
}

function logout() {

   if (socket) {
       socket.disconnect();
   }
   if (localStream) {
       localStream.getTracks().forEach(track => track.stop());
   }
   if (peerConnection) {
       peerConnection.close();
   }
   currentUser = null;
   username = '';
   isConnected = false;
   isVoiceEnabled = false;
   isMuted = false;
   updateConnectionStatus(false);
   updateVoiceStatus();
   clearTerminal();

   const mainInterface = document.getElementById('mainInterface');
   mainInterface.style.visibility = 'hidden';
   mainInterface.style.opacity = '0';
   mainInterface.style.pointerEvents = 'none';

   document.getElementById('bbsMainMenu').style.display = 'none';
   showBootScreen();
}

function initializeTerminal() {
   logMessage('RobCo Industries (TM) Termlink Protocol', 'server-msg');
   logMessage('BBS Network v2.1.7', 'system-msg');
   logMessage('VOICE CHAT MODULE LOADED', 'system-msg');
   logMessage('FILE TRANSMISSION SYSTEM READY', 'system-msg');
   logMessage('THEME SYSTEM ACTIVE', 'system-msg');
   logMessage('>', 'system-msg');
   logMessage('TYPE /help FOR COMMAND LIST', 'system-msg');
}

function logMessage(message, className = 'system-msg') {
   const messagesDiv = document.getElementById('messages');
   if (!messagesDiv) return;

   const messageElement = document.createElement('div');
   messageElement.className = `message-output ${className}`;

   const timestamp = new Date().toLocaleTimeString();

   if (message.includes('\n')) {
       const lines = message.split('\n');
       let formattedMessage = '';
       lines.forEach(line => {
           if (line.trim()) {
               formattedMessage += `<div><span class="timestamp">[${timestamp}]</span> ${line}</div>`;
           }
       });
       messageElement.innerHTML = formattedMessage;
   } else {
       messageElement.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${message}`;
   }

   messagesDiv.appendChild(messageElement);

   scrollToBottom();
}

function updateConnectionStatus(connected, user = '') {
   const led = document.getElementById('statusLed');
   const status = document.getElementById('connectionStatus');
   const statusBar = document.getElementById('statusBar');

   if (connected) {
       led.classList.add('connected');
       status.textContent = 'ONLINE';
       statusBar.innerHTML = `SYSTEM STATUS: ONLINE | USER: ${user} | TIME: <span id="systemTime"></span><span class="blinking-cursor">_</span>`;
   } else {
       led.classList.remove('connected');
       status.textContent = 'OFFLINE';
       statusBar.innerHTML = `SYSTEM STATUS: OFFLINE | TIME: <span id="systemTime"></span><span class="blinking-cursor">_</span>`;
   }
   updateSystemTime();
}

function updateSystemTime() {
   const now = new Date();
   const timeString = now.toTimeString().split(' ')[0];
   const timeSpan = document.getElementById('systemTime');
   if (timeSpan) {
       timeSpan.textContent = timeString;
   }
}

function updateVoiceStatus() {
   const indicator = document.getElementById('voiceIndicator');
   const status = document.getElementById('voiceStatus');
   const toggleBtn = document.getElementById('voiceToggle');
   const muteBtn = document.getElementById('muteMic');

   if (isVoiceEnabled) {
       indicator.classList.add('active');
       status.textContent = isMuted ? 'VOICE MUTED' : 'VOICE ACTIVE';
       toggleBtn.textContent = 'DISABLE VOICE';
       toggleBtn.classList.add('active');
       muteBtn.style.display = 'inline-block';
       muteBtn.textContent = isMuted ? 'UNMUTE MIC' : 'MUTE MIC';
   } else {
       indicator.classList.remove('active');
       status.textContent = 'VOICE DISABLED';
       toggleBtn.textContent = 'ENABLE VOICE';
       toggleBtn.classList.remove('active');
       muteBtn.style.display = 'none';
   }
}

document.addEventListener('DOMContentLoaded', () => {
   setupCursor();
   setupFileModal();
   setupThemeSystem();
   updateSystemTime();
   setInterval(updateSystemTime, 1000);
   addTransitions();
   createHiddenFileInput();

   showBootScreen();
});

function createHiddenFileInput() {
   const fileInput = document.createElement('input');
   fileInput.type = 'file';
   fileInput.id = 'hiddenFileInput';
   fileInput.style.display = 'none';
   document.body.appendChild(fileInput);

   fileInput.addEventListener('change', () => {
       if (fileInput.files.length) {
           pendingFile = fileInput.files[0];
           sendPendingFile();
       }
   });
}

function showBootScreen() {
   const bootScreen = document.getElementById('bootScreen');
   const bootContent = document.getElementById('bootContent');

   bootContent.innerHTML = '';

   bootScreen.style.display = 'block';

   const bootMessages = [
       'RobCo Industries (TM) Unified Operating System',
       'COPYRIGHT 2075-2077 ROBCO INDUSTRIES',
       '-Server 11-',
       '',
       'Initializing Robco Industries(TM) MF Boot Agent v2.3.0',
       'RBIOS-4.02.08.00 52EE5.E7.E8',
       'Copyright 2075-2077 Robco Ind.',
       'Uppermem: 64 KB',
       'Root (5A8)',
       'Maintenance Mode',
       '',
       'RobCo Industries(TM) Termlink Protocol',
       'Initializing Robco Industries(TM) MF Boot Agent v2.3.0',
       'RETROS BIOS',
       'RBIOS-4.02.08.00 52EE5.E7.E8',
       'Copyright 2075-2077 Robco Ind.',
       'Uppermem: 64 KB',
       'Root (5A8)',
       'Maintenance Mode',
       '',
       '> SET TERMINAL/INQUIRE',
       '',
       '> SET TERMINAL/DETACH',
       '',
       '> RUN DEBUG/ACCOUNTS.F',
       '> Checking authentication status...',
       ''
   ];

   let currentLine = 0;

   function typeNextLine() {
       if (currentLine < bootMessages.length) {
           const line = document.createElement('div');
           line.className = 'boot-line';
           line.textContent = bootMessages[currentLine];
           line.style.animationDelay = '0s';
           bootContent.appendChild(line);

           bootScreen.scrollTop = bootScreen.scrollHeight;

           currentLine++;

           const delay = bootMessages[currentLine - 1] === '' ? 100 : 
                        bootMessages[currentLine - 1].startsWith('>') ? 300 :
                        Math.random() * 200 + 50;

           setTimeout(typeNextLine, delay);
       } else {

           setTimeout(checkAuthAndShowLogin, 1000);
       }
   }

   setTimeout(typeNextLine, 500);
}

async function checkAuthAndShowLogin() {
   const bootContent = document.getElementById('bootContent');

   try {
       const response = await fetch('/auth/status');
       const user = await response.json();

       if (user.is_authenticated) {

           currentUser = user;
           username = user.username;

           const authLine = document.createElement('div');
           authLine.className = 'boot-line';
           authLine.textContent = `> Authentication verified: ${user.username}`;
           bootContent.appendChild(authLine);

           setTimeout(continueBootSequence, 500);
       } else {

           showTerminalLogin();
       }
   }
    catch (error) {
       console.error('Error checking auth status:', error);

       showTerminalLogin();
   }}

function showTerminalLogin() {
   const bootContent = document.getElementById('bootContent');
   const bootScreen = document.getElementById('bootScreen');

   const loginLine = document.createElement('div');
   loginLine.className = 'boot-line';
   loginLine.textContent = 'RobCo Industries (TM) Termlink';
   bootContent.appendChild(loginLine);

   const emptyLine = document.createElement('div');
   emptyLine.className = 'boot-line';
   emptyLine.textContent = '';
   bootContent.appendChild(emptyLine);

   const usernamePrompt = document.createElement('div');
   usernamePrompt.className = 'login-prompt';
   usernamePrompt.innerHTML = 'login: <input type="text" class="boot-input" id="bootUsername" placeholder="Enter username">';
   bootContent.appendChild(usernamePrompt);

   const usernameInput = document.getElementById('bootUsername');
   usernameInput.focus();

   usernameInput.addEventListener('keypress', (e) => {
       if (e.key === 'Enter') {
           const enteredUsername = usernameInput.value.trim();
           if (enteredUsername) {
               usernameInput.disabled = true;
               showPasswordPrompt(enteredUsername);
           }
       }
   });

   const newUserLine = document.createElement('div');
   newUserLine.className = 'boot-line';
   newUserLine.innerHTML = 'Type "new" to create new account or "guest" for guest access';
   bootContent.appendChild(newUserLine);

   bootScreen.scrollTop = bootScreen.scrollHeight;
}

function showPasswordPrompt(enteredUsername) {
   const bootContent = document.getElementById('bootContent');
   const bootScreen = document.getElementById('bootScreen');

   if (enteredUsername.toLowerCase() === 'new') {
       showTerminalRegistration();
       return;
   }

   if (enteredUsername.toLowerCase() === 'guest') {
       showGuestLogin();
       return;
   }
   const passwordPrompt = document.createElement('div');
   passwordPrompt.className = 'login-prompt';
   passwordPrompt.innerHTML = 'Password: <input type="password" class="boot-input" id="bootPassword" placeholder="Enter password">';
   bootContent.appendChild(passwordPrompt);

   const passwordInput = document.getElementById('bootPassword');
   passwordInput.focus();

   passwordInput.addEventListener('keypress', async (e) => {
       if (e.key === 'Enter') {
           const password = passwordInput.value;
           passwordInput.disabled = true;

           try {
               const formData = new FormData();
               formData.append('username', enteredUsername);
               formData.append('password', password);

               const response = await fetch('/login', {
                   method: 'POST',
                   body: formData
               });
               const result = await response.json();

               if (result.success) {
                   const successLine = document.createElement('div');
                   successLine.className = 'boot-line';
                   successLine.textContent = `> Authentication successful: ${result.username}`;
                   bootContent.appendChild(successLine);

                   handleLoginSuccess(result.username, false);
               } else {
                   const errorLine = document.createElement('div');
                   errorLine.className = 'boot-line';
                   errorLine.textContent = `> Authentication failed: ${result.error}`;
                   bootContent.appendChild(errorLine);

                   setTimeout(showTerminalLogin, 2000);
               }
           } catch (error) {
               const errorLine = document.createElement('div');
               errorLine.className = 'boot-line';
               errorLine.textContent = '> Connection error - please try again';
               bootContent.appendChild(errorLine);

               setTimeout(showTerminalLogin, 2000);
           }
       }
   });

   bootScreen.scrollTop = bootScreen.scrollHeight;
}

function showTerminalRegistration() {
   const bootContent = document.getElementById('bootContent');
   const bootScreen = document.getElementById('bootScreen');

   const regLine = document.createElement('div');
   regLine.className = 'boot-line';
   regLine.textContent = '> Creating new account...';
   bootContent.appendChild(regLine);

   const usernamePrompt = document.createElement('div');
   usernamePrompt.className = 'login-prompt';
   const usernameId = 'regUsername_' + Date.now(); 
   usernamePrompt.innerHTML = `New username: <input type="text" class="boot-input" id="${usernameId}" placeholder="Choose username">`;
   bootContent.appendChild(usernamePrompt);

   setTimeout(() => {
       const usernameInput = document.getElementById(usernameId);
       if (usernameInput) {
           usernameInput.focus();

           usernameInput.onkeypress = (e) => {
               if (e.key === 'Enter') {
                   const username = usernameInput.value.trim();
                   if (username) {
                       usernameInput.disabled = true;
                       showEmailPrompt(username);
                   }
               }
           };
       }
   }, 100);

   bootScreen.scrollTop = bootScreen.scrollHeight;
}

function showEmailPrompt(username) {
   const bootContent = document.getElementById('bootContent');
   const bootScreen = document.getElementById('bootScreen');

   const emailPrompt = document.createElement('div');
   emailPrompt.className = 'login-prompt';
   const emailId = 'regEmail_' + Date.now(); 
   emailPrompt.innerHTML = `Email: <input type="email" class="boot-input" id="${emailId}" placeholder="Enter email">`;
   bootContent.appendChild(emailPrompt);

   setTimeout(() => {
       const emailInput = document.getElementById(emailId);
       if (emailInput) {
           emailInput.focus();

           emailInput.onkeypress = (e) => {
               if (e.key === 'Enter') {
                   const email = emailInput.value.trim();
                   if (email) {
                       emailInput.disabled = true;
                       showRegPasswordPrompt(username, email);
                   }
               }
           };
       }
   }, 100);

   bootScreen.scrollTop = bootScreen.scrollHeight;
}

function showRegPasswordPrompt(username, email) {
   const bootContent = document.getElementById('bootContent');
   const bootScreen = document.getElementById('bootScreen');

   const passwordPrompt = document.createElement('div');
   passwordPrompt.className = 'login-prompt';
   const passwordId = 'regPassword_' + Date.now(); 
   passwordPrompt.innerHTML = `Password: <input type="password" class="boot-input" id="${passwordId}" placeholder="Choose password">`;
   bootContent.appendChild(passwordPrompt);

   setTimeout(() => {
       const passwordInput = document.getElementById(passwordId);
       if (passwordInput) {
           passwordInput.focus();

           passwordInput.onkeypress = (e) => {
               if (e.key === 'Enter') {
                   const password = passwordInput.value;
                   if (password) {
                       passwordInput.disabled = true;
                       showConfirmPasswordPrompt(username, email, password);
                   }
               }
           };
       }
   }, 100);

   bootScreen.scrollTop = bootScreen.scrollHeight;
}

function showConfirmPasswordPrompt(username, email, password) {
   const bootContent = document.getElementById('bootContent');
   const bootScreen = document.getElementById('bootScreen');

   const confirmPrompt = document.createElement('div');
   confirmPrompt.className = 'login-prompt';
   const confirmId = 'regConfirmPassword_' + Date.now(); 
   confirmPrompt.innerHTML = `Confirm Password: <input type="password" class="boot-input" id="${confirmId}" placeholder="Confirm password">`;
   bootContent.appendChild(confirmPrompt);

   setTimeout(() => {
       const confirmInput = document.getElementById(confirmId);
       if (confirmInput) {
           confirmInput.focus();

           confirmInput.onkeypress = async (e) => {
               if (e.key === 'Enter') {
                   const confirmPassword = confirmInput.value;
                   confirmInput.disabled = true;

                   if (password !== confirmPassword) {
                       const errorLine = document.createElement('div');
                       errorLine.className = 'boot-line';
                       errorLine.textContent = '> Password confirmation failed - please try again';
                       bootContent.appendChild(errorLine);

                       setTimeout(() => {
                           showTerminalLogin();
                       }, 1500);
                       return;
                   }

                   try {
                       const formData = new FormData();
                       formData.append('username', username);
                       formData.append('email', email);
                       formData.append('password', password);
                       formData.append('confirm_password', confirmPassword);

                       const response = await fetch('/register', {
                           method: 'POST',
                           body: formData
                       });
                       const result = await response.json();

                       if (result.success) {
                           const successLine = document.createElement('div');
                           successLine.className = 'boot-line';
                           successLine.textContent = `> Registration successful: ${result.username}`;
                           bootContent.appendChild(successLine);

                           handleLoginSuccess(result.username, false);
                       } else {
                           const errorLine = document.createElement('div');
                           errorLine.className = 'boot-line';
                           errorLine.textContent = `> Registration failed: ${result.error}`;
                           bootContent.appendChild(errorLine);

                           setTimeout(() => {
                               showTerminalLogin();
                           }, 1500);
                       }
                   } catch (error) {
                       const errorLine = document.createElement('div');
                       errorLine.className = 'boot-line';
                       errorLine.textContent = '> Connection error - please try again';
                       bootContent.appendChild(errorLine);

                       setTimeout(() => {
                           showTerminalLogin();
                       }, 1500);
                   }
               }
           };
       }
   }, 100);

   bootScreen.scrollTop = bootScreen.scrollHeight;
}

function showGuestLogin() {
   const bootContent = document.getElementById('bootContent');
   const bootScreen = document.getElementById('bootScreen');

   const guestPrompt = document.createElement('div');
   guestPrompt.className = 'login-prompt';
   guestPrompt.innerHTML = 'Guest username: <input type="text" class="boot-input" id="guestUsername" placeholder="Enter guest name">';
   bootContent.appendChild(guestPrompt);

   const guestInput = document.getElementById('guestUsername');
   guestInput.focus();

   guestInput.addEventListener('keypress', async (e) => {
       if (e.key === 'Enter') {
           const guestName = guestInput.value.trim();
           if (guestName) {
               guestInput.disabled = true;

               try {
                   const response = await fetch('/anonymous-login', {
                       method: 'POST',
                       headers: {'Content-Type': 'application/json'},
                       body: JSON.stringify({username: guestName.toUpperCase()})
                   });
                   const result = await response.json();

                   if (result.success) {
                       const successLine = document.createElement('div');
                       successLine.className = 'boot-line';
                       successLine.textContent = `> Guest access granted: ${result.username}`;
                       bootContent.appendChild(successLine);

                       handleLoginSuccess(result.username, true);
                   } else {
                       const errorLine = document.createElement('div');
                       errorLine.className = 'boot-line';
                       errorLine.textContent = `> Guest access denied: ${result.error}`;
                       bootContent.appendChild(errorLine);

                       setTimeout(showTerminalLogin, 2000);
                   }
               } catch (error) {
                   const errorLine = document.createElement('div');
                   errorLine.className = 'boot-line';
                   errorLine.textContent = '> Connection error - please try again';
                   bootContent.appendChild(errorLine);

                   setTimeout(showTerminalLogin, 2000);
               }
           }
       }
   });

   bootScreen.scrollTop = bootScreen.scrollHeight;
}

function continueBootSequence() {
   const bootContent = document.getElementById('bootContent');
   const bootScreen = document.getElementById('bootScreen');

   const finalBootMessages = [
       '',
       'Welcome to ROBCO Industries (TM) Termlink',
       '',
       '> Parsing network protocols...',
       '> Establishing secure connection...',
       '> Loading user interface modules...',
       '> Initializing voice communication systems...',
       '> Loading file transfer protocols...',
       '> Loading BBS network access...',
       '',
       'ROBCO TERMLINK READY',
       'Connecting to BBS Network...',
       '',
       'Connection established.',
       'Welcome to the Network.'
   ];

   let currentLine = 0;

   function typeNextLine() {
       if (currentLine < finalBootMessages.length) {
           const line = document.createElement('div');
           line.className = 'boot-line';
           line.textContent = finalBootMessages[currentLine];
           line.style.animationDelay = '0s';
           bootContent.appendChild(line);

           bootScreen.scrollTop = bootScreen.scrollHeight;

           currentLine++;

           const delay = finalBootMessages[currentLine - 1] === '' ? 100 : 
                        finalBootMessages[currentLine - 1].startsWith('>') ? 300 :
                        Math.random() * 200 + 50;

           setTimeout(typeNextLine, delay);
       } else {

           setTimeout(() => {
               bootScreen.style.display = 'none';
               showBBSMainMenu();
               connectToServer();
           }, 1000);
       }
   }

   setTimeout(typeNextLine, 200);
}

function handleLoginSuccess(usernameFromServer, isAnonymous) {
   currentUser = { username: usernameFromServer, is_anonymous: isAnonymous };
   username = usernameFromServer; 
   window.username = usernameFromServer; 

   console.log('Login success - username set to:', username); 

   setTimeout(continueBootSequence, 500);
}

function connectToServer() {
   logMessage('ESTABLISHING CONNECTION...', 'system-msg');

   socket = io('http://localhost:8080');

   socket.on('connect', () => {
       isConnected = true;
       updateConnectionStatus(true, username);
       logMessage('CONNECTION ESTABLISHED TO BBS NETWORK', 'server-msg');

       socket.emit('set_username', {
           username: username,
           is_anonymous: currentUser.is_anonymous
       });

       socket.emit('get_users');
       socket.emit('check_rooms');

       if (document.getElementById('bbsMainMenu').style.display === 'block') {
           startUsersAutoRefresh();
       }
   });

   socket.on('server_message', (data) => {
       logMessage(`[SYSTEM]: ${data['text from server'] || data.text || data.data}`, 'server-msg');
   });

   socket.on('auth_status', (data) => {
       if (data.authenticated) {
           logMessage(`[SYSTEM]: AUTHENTICATED AS ${data.username}`, 'server-msg');
       }
   });

   socket.on('rooms_restored', (data) => {
       if (data.rooms && data.rooms.length > 0) {
           logMessage(`[SYSTEM]: RESTORED TO ROOMS: ${data.rooms.join(', ')}`, 'server-msg');
       }
   });

   socket.on('chat_message', (data) => {
       if (data.type === 'file') {
           const { filename, blob } = data.data;
           const arr = atob(blob).split('').map(c => c.charCodeAt(0));
           const url = URL.createObjectURL(new Blob([new Uint8Array(arr)]));
           addMsg(`<b>${data.sender_name}:</b> [FILE] <a href="${url}" download="${filename}" style="color: var(--text-secondary); text-decoration: underline;">${filename}</a>`, 'chat');
       } else {
           addMsg(`<b>${data.sender_name}:</b> ${data.data}`, 'chat');
       }

       scrollToBottom();
   });

   socket.on('private_message', (data) => {
       if (data.type === 'file') {
           const { filename, blob } = data.data;
           const arr = atob(blob).split('').map(c => c.charCodeAt(0));
           const url = URL.createObjectURL(new Blob([new Uint8Array(arr)]));
           addMsg(`<b>Private from ${data.sender_name}:</b> [FILE] <a href="${url}" download="${filename}" style="color: #ff6666; text-decoration: underline;">${filename}</a>`, 'private');
       } else {
           addMsg(`<b>Private from ${data.sender_name}:</b> ${data.data}`, 'private');
       }
       showNotification(`Private message from ${data.sender_name}`, data.data);

       scrollToBottom();
   });

   socket.on('room_message', (data) => {
       if (data.type === 'file') {
           const { filename, blob } = data.data;
           const arr = atob(blob).split('').map(c => c.charCodeAt(0));
           const url = URL.createObjectURL(new Blob([new Uint8Array(arr)]));
           addMsg(`<b>[${data.receiver_name}] ${data.sender_name}:</b> [FILE] <a href="${url}" download="${filename}" style="color: #6666ff; text-decoration: underline;">${filename}</a>`, 'room');
       } else {
           addMsg(`<b>[${data.receiver_name}] ${data.sender_name}:</b> ${data.data}`, 'room');
       }

       scrollToBottom();
   });

   socket.on('users_list', (data) => {
       if (data && data.users) {
           logMessage(`ACTIVE USERS: ${data.users.join(', ')}`, 'system-msg');
           updateUsersOnlineDisplay(data.users);
       } else {
           logMessage('ACTIVE USERS: None', 'system-msg');
           updateUsersOnlineDisplay([]);
       }
   });

   socket.on('room_list', (data) => {
       if (data && data.rooms) {

           let roomNames = [];
           if (data.rooms.length > 0 && typeof data.rooms[0] === 'object') {
               roomNames = data.rooms.map(r => r.name || r);
           } else {
               roomNames = data.rooms;
           }
           logMessage(`JOINED ROOMS: ${roomNames.join(', ') || 'NONE'}`, 'system-msg');

           const sidebarRoomList = document.getElementById('rooms');
           if (sidebarRoomList) {
               if (data.rooms.length === 0) {
                   sidebarRoomList.innerHTML = '<li><em>No rooms joined</em></li>';
               } else {
                   sidebarRoomList.innerHTML = data.rooms.map(r => {
                       if (typeof r === 'object') {
                           const name = r.name || 'Unknown';
                           const desc = r.description || 'No description';
                           return `<li><strong>${name}</strong><br><small>${desc}</small></li>`;
                       } else {
                           return `<li>${r}</li>`;
                       }
                   }).join('');
               }
           }
       } else {
           logMessage('JOINED ROOMS: NONE', 'system-msg');
       }
   });

   socket.on('chat_history', (data) => {
       addMsg('<b>=== CHAT HISTORY ===</b>', 'system');
       const messages = data.messages || [];
       messages.reverse().forEach(msg => {
           const username = msg.useruid || 'Unknown';
           if (msg.message_type === 'file' && msg.filename && msg.blob) {
               const arr = atob(msg.blob).split('').map(c => c.charCodeAt(0));
               const url = URL.createObjectURL(new Blob([new Uint8Array(arr)]));
               addMsg(`<b>${username}:</b> [FILE] <a href="${url}" download="${msg.filename}" style="color: var(--text-secondary); text-decoration: underline;">${msg.filename}</a>`, 'chat');
           } else {
               addMsg(`<b>${username}:</b> ${msg.message || ''}`, 'chat');
           }
       });
       addMsg('<b>=== END HISTORY ===</b>', 'system');
   });

   socket.on('room_history', (data) => {
       const room = data.room || '';
       addMsg(`<b>=== ROOM ${room} HISTORY ===</b>`, 'system');
       const messages = data.messages || [];
       messages.reverse().forEach(msg => {
           const username = msg.useruid || 'Unknown';
           if (msg.message_type === 'file' && msg.filename && msg.blob) {
               const arr = atob(msg.blob).split('').map(c => c.charCodeAt(0));
               const url = URL.createObjectURL(new Blob([new Uint8Array(arr)]));
               addMsg(`<b>[${room}] ${username}:</b> [FILE] <a href="${url}" download="${msg.filename}" style="color: #6666ff; text-decoration: underline;">${msg.filename}</a>`, 'room');
           } else {
               addMsg(`<b>[${room}] ${username}:</b> ${msg.message || ''}`, 'room');
           }
       });
       addMsg('<b>=== END HISTORY ===</b>', 'system');
   });

   socket.on('pm_list', (data) => {
       const conversations = data.conversations || [];
       if (conversations.length === 0) {
           addMsg('<b>=== PRIVATE MESSAGE CONVERSATIONS ===</b>', 'system');
           addMsg('No private message conversations found', 'system');
           addMsg('<b>=== END PM LIST ===</b>', 'system');
       } else {
           addMsg('<b>=== PRIVATE MESSAGE CONVERSATIONS ===</b>', 'system');
           conversations.forEach(conv => {
               const username = conv.useruid || 'Unknown';
               const messageCount = conv.message_count || 0;
               const lastMessage = conv.last_message_time || 'Never';
               addMsg(`${username} - ${messageCount} messages (last: ${lastMessage})`, 'system');
           });
           addMsg('<b>=== END PM LIST ===</b>', 'system');
       }
   });

   socket.on('private_history', (data) => {
       const username = data.username || 'Unknown';
       addMsg(`<b>=== PRIVATE MESSAGES WITH ${username} ===</b>`, 'system');
       data.messages.reverse().forEach(msg => {
           const sender = msg.useruid || 'Unknown';
           if (msg.message_type === 'file' && msg.filename) {
               addMsg(`<b>[PM ${sender}]:</b> [FILE: ${msg.filename}]`, 'private');
           } else {
               addMsg(`<b>[PM ${sender}]:</b> ${msg.message}`, 'private');
           }
       });
       addMsg('<b>=== END HISTORY ===</b>', 'system');
   });

   socket.on('adventure_invitation', (data) => {
       logMessage(`[ADVENTURE INVITATION] ${data.message}`, 'adventure-invite');
   });

   socket.on('adventure_message', (data) => {
       const type = data.type;
       const prefix = `[ADVENTURE ${data.room_id} – ${data.sender_name || ''} (${data.sender_role || ''})] `;

       if (type === 'join' || type === 'dm_disconnect' || type === 'player_disconnect') {
           logMessage(`${prefix}⚠️ ${data.message}`, 'adventure-msg');
       } else if (type === 'file') {
           const { filename, blob } = data.data;
           const arr = atob(blob).split('').map(c => c.charCodeAt(0));
           const url = URL.createObjectURL(new Blob([new Uint8Array(arr)]));
           logMessage(`${prefix}[FILE] <a href="${url}" download="${filename}" style="color: #66ff66; text-decoration: underline;">${filename}</a>`, 'adventure-msg');
       } else {
           logMessage(`${prefix}${data.data}`, 'adventure-msg');
       }
   });

   socket.on('adventure_info', (data) => {
       let info = `[ADVENTURE: ${data.room_id}]\n`;
       info += `STORY: ${data.story}\n`;
       info += `DUNGEON MASTER: ${data.dm}\n`;
       info += `PLAYERS: ${data.players.join(', ') || 'NONE'}\n`;
       info += `INVITED: ${data.invited_users.join(', ') || 'NONE'}`;
       logMessage(info, 'adventure-msg');
   });

   socket.on('disconnect', () => {
       isConnected = false;
       updateConnectionStatus(false);
       logMessage('CONNECTION TERMINATED', 'server-msg');
   });

   socket.on('connect_error', (error) => {
       logMessage(`CONNECTION ERROR: ${error.message}`, 'server-msg');
   });

   socket.on('signal', handleVoiceSignal);

   socket.on('reconnect', () => {
       logMessage('[SYSTEM] Connection restored', 'server-msg');
       updateConnectionStatus(true, username);

       if (socket) {
           socket.emit('set_username', {
               username: username,
               is_anonymous: currentUser.is_anonymous
           });
       }
   });

   socket.on('reconnect_attempt', (attemptNumber) => {
       logMessage(`[SYSTEM] Reconnection attempt ${attemptNumber}`, 'system-msg');
   });

   socket.on('reconnect_failed', () => {
       logMessage('[SYSTEM] Reconnection failed - please refresh page', 'server-msg');
   });
}

function showPMConversations() {

   document.getElementById('bootScreen').style.display = 'none';
   document.getElementById('mainInterface').style.display = 'none';
   document.getElementById('bbsMainMenu').style.display = 'none';
   document.getElementById('pmChatInterface').style.display = 'none';

   document.getElementById('pmConversationsMenu').style.display = 'block';

   loadPMConversations();

   stopUsersAutoRefresh();
}

function loadPMConversations() {
   if (!socket) return;

   const conversationsList = document.getElementById('pmConversationsList');
   conversationsList.innerHTML = '<div class="pm-loading">Loading conversations...</div>';

   socket.emit('get_pm_list');
}

function openPMChat(targetUser) {
   currentPMUser = targetUser;

   document.getElementById('pmConversationsMenu').style.display = 'none';
   document.getElementById('pmChatInterface').style.display = 'block';

   document.getElementById('pmChatTitle').textContent = `Direct Message - ${targetUser}`;

   updatePMUserStatus(targetUser);

   loadPMHistory(targetUser);

   setTimeout(() => {
       document.getElementById('pmMessageInput').focus();
   }, 100);
}

function loadPMHistory(targetUser) {
   if (!socket) return;

   const messagesContainer = document.getElementById('pmChatMessages');
   messagesContainer.innerHTML = '<div class="pm-loading">Loading messages...</div>';

   socket.emit('get_chat_history', {type: 'private', target: targetUser});
}

function sendPMMessage() {
   const input = document.getElementById('pmMessageInput');
   const message = input.value.trim();

   if (!message || !currentPMUser || !socket) return;

   const payload = makePayload(currentPMUser, message, 'text');
   socket.emit('private_message', payload);

   addPMMessage(username, message, new Date().toISOString(), true);

   input.value = '';
}

function handlePMInput(event) {
   if (event.key === 'Enter') {
       sendPMMessage();
   }
}

function addPMMessage(sender, content, timestamp, isSent = false) {
   const messagesContainer = document.getElementById('pmChatMessages');

   const loading = messagesContainer.querySelector('.pm-loading');
   if (loading) {
       loading.remove();
   }

   const messageDiv = document.createElement('div');
   messageDiv.className = `pm-message ${isSent ? 'sent' : 'received'}`;

   const time = new Date(timestamp).toLocaleTimeString();

   messageDiv.innerHTML = `
       <div class="pm-message-header">
           <span class="pm-message-sender">${sender}</span><span class="pm-message-time">${time}</span>
       </div>
       <div class="pm-message-content">${content}</div>
   `;

   messagesContainer.appendChild(messageDiv);

   messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function updatePMUserStatus(targetUser) {

   const statusSpan = document.getElementById('pmUserStatus');
   const userList = document.getElementById('userListContainer');

   if (userList) {
       const userItems = userList.querySelectorAll('.user-name');
       let isOnline = false;

       userItems.forEach(item => {
           if (item.textContent === targetUser) {
               isOnline = true;
           }
       });

       statusSpan.textContent = isOnline ? 'Online' : 'Offline';
       statusSpan.style.color = isOnline ? '#00ff00' : '#666666';
   }
}

function showNewPMDialog() {
   const targetUser = prompt('Enter username to start conversation:');
   if (targetUser && targetUser.trim()) {
       const cleanUser = targetUser.trim();
       if (cleanUser !== username) {
           openPMChat(cleanUser);
       } else {
           alert('You cannot send messages to yourself!');
       }
   }
}

function showPMFileUpload() {
   if (!currentPMUser) return;

   pendingReceiver = currentPMUser;
   pendingEmitEvent = 'private_message';
   document.getElementById('hiddenFileInput').click();
}

function displayPMConversations(conversations) {
   const conversationsList = document.getElementById('pmConversationsList');
   const emptyState = document.getElementById('pmEmptyState');

   if (!conversations || conversations.length === 0) {
       conversationsList.innerHTML = '';
       emptyState.style.display = 'block';
       return;
   }

   emptyState.style.display = 'none';

   conversationsList.innerHTML = conversations.map(conv => {
       const username = conv.useruid || 'Unknown';
       const messageCount = conv.message_count || 0;
       const lastMessage = conv.last_message_time || 'No messages yet';

       return `
           <div class="pm-conversation-item" onclick="openPMChat('${username}')">
               <div class="pm-user-info">
                   <div class="pm-username">${username}</div>
                   <div class="pm-last-message">Last: ${lastMessage}</div>
               </div>
               <div class="pm-message-count">${messageCount}</div>
           </div>
       `;
   }).join('');

   const unreadCount = conversations.reduce((total, conv) => total + (conv.unread_count || 0), 0);
   const unreadSpan = document.getElementById('unreadPMCount');
   if (unreadSpan) {
       unreadSpan.textContent = unreadCount > 0 ? unreadCount : '0';
       unreadSpan.style.background = unreadCount > 0 ? '#ff0000' : 'var(--primary)';
   }
}

function displayPMHistory(messages, targetUser) {
   const messagesContainer = document.getElementById('pmChatMessages');
   messagesContainer.innerHTML = '';

   if (!messages || messages.length === 0) {
       messagesContainer.innerHTML = '<div class="pm-empty-state">No messages yet. Start the conversation!</div>';
       return;
   }

   messages.reverse().forEach(msg => {
       const sender = msg.useruid || 'Unknown';
       const content = msg.message || '';
       const timestamp = msg.created_at || new Date().toISOString();
       const isSent = sender === username;

       if (msg.message_type === 'file' && msg.filename) {

           const fileContent = `[FILE: ${msg.filename}]`;
           addPMMessage(sender, fileContent, timestamp, isSent);
       } else {
           addPMMessage(sender, content, timestamp, isSent);
       }
   });
}

function logSystemMessage(message) {
   const systemLog = document.getElementById('systemLog');
   if (!systemLog) return;

   const logEntry = document.createElement('div');
   logEntry.className = 'log-entry';
   logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;

   systemLog.appendChild(logEntry);
   systemLog.scrollTop = systemLog.scrollHeight;

   while (systemLog.children.length > 50) {
       systemLog.removeChild(systemLog.firstChild);
   }
}

async function initializeVoiceChat() {
   try {
       localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });

       peerConnection = new RTCPeerConnection({
           iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
       });

       localStream.getTracks().forEach(track => {
           peerConnection.addTrack(track, localStream);
       });

       peerConnection.onicecandidate = event => {
           if (event.candidate && socket) {
               socket.emit('signal', { type: 'ice', candidate: event.candidate });
           }
       };

       peerConnection.ontrack = event => {
           const audio = document.createElement('audio');
           audio.srcObject = event.streams[0];
           audio.autoplay = true;
           document.body.appendChild(audio);
       };

       peerConnection.onconnectionstatechange = () => {
           logMessage(`[VOICE] Connection state: ${peerConnection.connectionState}`, 'system-msg');
       };

       isVoiceEnabled = true;
       updateVoiceStatus();
       logMessage('[VOICE] Voice chat enabled', 'system-msg');

       return true;
   } catch (error) {
       logMessage(`[VOICE] Error: ${error.message}`, 'server-msg');
       return false;
   }
}

function handleVoiceSignal(data) {
   if (!peerConnection) return;

   try {
       if (data.type === 'offer') {
           peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer))
               .then(() => peerConnection.createAnswer())
               .then(answer => peerConnection.setLocalDescription(answer))
               .then(() => {
                   if (socket) {
                       socket.emit('signal', { type: 'answer', answer: peerConnection.localDescription });
                   }
               });
       } else if (data.type === 'answer') {
           peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
       } else if (data.type === 'ice' && data.candidate) {
           peerConnection.addIceCandidate(data.candidate).catch(e => {
               console.error('Error adding ICE candidate:', e);
           });
       }
   } catch (error) {
       console.error('Voice signal handling error:', error);
   }
}

function toggleVoiceChat() {
   if (!isVoiceEnabled) {
       initializeVoiceChat().then(success => {
           if (success && socket) {
               socket.emit('signal', { type: 'join' });
           }
       });
   } else {
       if (localStream) {
           localStream.getTracks().forEach(track => track.stop());
           localStream = null;
       }
       if (peerConnection) {
           peerConnection.close();
           peerConnection = null;
       }
       isVoiceEnabled = false;
       updateVoiceStatus();
       logMessage('[VOICE] Voice chat disabled', 'system-msg');
   }
}

function toggleMute() {
   if (localStream) {
       const audioTrack = localStream.getAudioTracks()[0];
       if (audioTrack) {
           audioTrack.enabled = !audioTrack.enabled;
           isMuted = !audioTrack.enabled;
           updateVoiceStatus();
           logMessage(`[VOICE] Microphone ${isMuted ? 'muted' : 'unmuted'}`, 'system-msg');
       }
   }
}

document.addEventListener('DOMContentLoaded', () => {
   document.getElementById('voiceToggle').addEventListener('click', toggleVoiceChat);
   document.getElementById('muteMic').addEventListener('click', toggleMute);
});

function setupFileModal() {
   const modal = document.getElementById('fileModal');
   const fileInput = document.getElementById('fileInput');
   const fileInputLabel = document.getElementById('fileInputLabel');
   const fileInfo = document.getElementById('fileInfo');
   const fileName = document.getElementById('fileName');
   const fileSize = document.getElementById('fileSize');
   const transmitBtn = document.getElementById('transmitFile');
   const targetInputs = {
       private: document.getElementById('privateTarget'),
       room: document.getElementById('roomTarget'),
       adventure: document.getElementById('adventureTarget')
   };

   document.querySelectorAll('input[name="fileTarget"]').forEach(radio => {
       radio.addEventListener('change', () => {
           Object.values(targetInputs).forEach(input => input.disabled = true);
           if (targetInputs[radio.value]) {
               targetInputs[radio.value].disabled = false;
           }
       });
   });

   fileInput.addEventListener('change', () => {
       const file = fileInput.files[0];
       if (file) {
           fileName.textContent = file.name;
           fileSize.textContent = formatFileSize(file.size);
           fileInfo.innerHTML = `
               <strong>FILE:</strong> ${file.name}<br>
               <strong>SIZE:</strong> ${formatFileSize(file.size)}<br>
               <strong>TYPE:</strong> ${file.type || 'Unknown'}
           `;
           fileInfo.style.display = 'block';
           transmitBtn.disabled = false;

           fileInputLabel.classList.add('has-file');
           fileInputLabel.innerHTML = `📄 ${file.name} (${formatFileSize(file.size)})`;
       } else {
           fileInfo.style.display = 'none';
           transmitBtn.disabled = true;

           fileInputLabel.classList.remove('has-file');
           fileInputLabel.innerHTML = '📁 SELECT FILE FOR TRANSMISSION';
       }
   });
}

function closeFileModal() {
   document.getElementById('fileModal').style.display = 'none';
   document.getElementById('fileInput').value = '';
   document.getElementById('fileInfo').style.display = 'none';
   document.getElementById('transmitFile').disabled = true;

   const fileInputLabel = document.getElementById('fileInputLabel');
   fileInputLabel.classList.remove('has-file');
   fileInputLabel.innerHTML = '📁 SELECT FILE FOR TRANSMISSION';
}

function transmitFile() {
   const fileInput = document.getElementById('fileInput');
   const file = fileInput.files[0];
   if (!file || !socket) return;

   const target = document.querySelector('input[name="fileTarget"]:checked').value;
   let receiver, emitEvent;

   switch (target) {
       case 'global':
           receiver = 'all';
           emitEvent = 'chat_message';
           break;
       case 'private':
           receiver = document.getElementById('privateTarget').value.trim();
           if (!receiver) {
               alert('ENTER USERNAME FOR PRIVATE TRANSMISSION');
               return;
           }
           emitEvent = 'private_message';
           break;
       case 'room':
           receiver = document.getElementById('roomTarget').value.trim();
           if (!receiver) {
               alert('ENTER ROOM NAME');
               return;
           }
           emitEvent = 'room_message';
           break;
       case 'adventure':
           receiver = document.getElementById('adventureTarget').value.trim();
           if (!receiver) {
               alert('ENTER ADVENTURE ID');
               return;
           }
           emitEvent = 'adventure_message';
           break;
   }

   const reader = new FileReader();
   reader.onload = () => {
       const base64 = reader.result.split(',')[1];
       const payload = makePayload(
           receiver,
           { filename: file.name, blob: base64 },
           'file'
       );
       socket.emit(emitEvent, payload);
       logMessage(`[FILE TRANSMITTED] ${file.name} to ${receiver}`, 'system-msg');
       closeFileModal();
   };
   reader.readAsDataURL(file);
}

function formatFileSize(bytes) {
   if (bytes === 0) return '0 Bytes';
   const k = 1024;
   const sizes = ['Bytes', 'KB', 'MB', 'GB'];
   const i = Math.floor(Math.log(bytes) / Math.log(k));
   return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function setupThemeSystem() {
   const savedTheme = localStorage.getItem('termlink-theme') || 'amber';
   applyTheme(savedTheme);
   setupThemeSelector();
}

function setupThemeSelector() {
   const themeRadios = document.querySelectorAll('input[name="themeOption"]');
   const currentTheme = document.documentElement.getAttribute('data-theme') || 'amber';

   themeRadios.forEach(radio => {
       if (radio.value === currentTheme) {
           radio.checked = true;
       }

       radio.addEventListener('change', () => {
           if (radio.checked) {
               applyTheme(radio.value);
           }
       });
   });
}

function applyTheme(themeName) {
   document.documentElement.setAttribute('data-theme', themeName);
   localStorage.setItem('termlink-theme', themeName);
   updateMessageColors(themeName);
   logSystemMessage(`Theme changed to: ${themeName.toUpperCase().replace('-', ' ')}`);
}

function updateMessageColors(themeName) {
   const style = document.createElement('style');
   style.id = 'theme-message-colors';

   const existing = document.getElementById('theme-message-colors');
   if (existing) existing.remove();

   let messageColors = '';
   let backgroundColors = '';

   switch (themeName) {
       case 'amber':
           messageColors = `
               .server-msg { color: var(--primary-light); }
               .chat-msg { color: #dd9933; }
               .private-msg { color: #ff6666; }
               .adventure-msg { color: #66ff66; }
               .room-msg { color: #6666ff; }
               .system-msg { color: var(--primary-dark); }
           `;
           backgroundColors = `
               .quick-btn:hover { background: rgba(204, 119, 0, 0.2) !important; }
               .bbs-main-item:hover { background: rgba(204, 119, 0, 0.2) !important; }
               .bbs-room-item:hover { background: rgba(204, 119, 0, 0.25) !important; }
               .pm-conversation-item:hover { background: rgba(204, 119, 0, 0.2) !important; }
               .user-item:hover { background: rgba(204, 119, 0, 0.15) !important; }
               .room-list li:hover, .user-list li:hover { background: rgba(204, 119, 0, 0.15) !important; }
           `;
           break;
       case 'dark-contrast':
           messageColors = `
               .server-msg { color: #ffffff; }
               .chat-msg { color: #cccccc; }
               .private-msg { color: #ff9999; }
               .adventure-msg { color: #99ff99; }
               .room-msg { color: #9999ff; }
               .system-msg { color: #888888; }
           `;
           backgroundColors = `
               .quick-btn:hover { background: rgba(255, 255, 255, 0.2) !important; }
               .bbs-main-item:hover { background: rgba(255, 255, 255, 0.2) !important; }
               .bbs-room-item:hover { background: rgba(255, 255, 255, 0.25) !important; }
               .pm-conversation-item:hover { background: rgba(255, 255, 255, 0.2) !important; }
               .user-item:hover { background: rgba(255, 255, 255, 0.15) !important; }
               .room-list li:hover, .user-list li:hover { background: rgba(255, 255, 255, 0.15) !important; }
           `;
           break;
       case 'white-contrast':
           messageColors = `
               .server-msg { color: #000000; }
               .chat-msg { color: #333333; }
               .private-msg { color: #cc0000; }
               .adventure-msg { color: #009900; }
               .room-msg { color: #0000cc; }
               .system-msg { color: #666666; }
           `;
           backgroundColors = `
               .quick-btn:hover { background: rgba(0, 0, 0, 0.2) !important; }
               .bbs-main-item:hover { background: rgba(0, 0, 0, 0.2) !important; }
               .bbs-room-item:hover { background: rgba(0, 0, 0, 0.25) !important; }
               .pm-conversation-item:hover { background: rgba(0, 0, 0, 0.2) !important; }
               .user-item:hover { background: rgba(0, 0, 0, 0.15) !important; }
               .room-list li:hover, .user-list li:hover { background: rgba(0, 0, 0, 0.15) !important; }
           `;
           break;
       case 'terminal-green':
           messageColors = `
               .server-msg { color: #00ff41; }
               .chat-msg { color: #66ff77; }
               .private-msg { color: #ffff00; }
               .adventure-msg { color: #00ffff; }
               .room-msg { color: #ff00ff; }
               .system-msg { color: #00cc33; }
           `;
           backgroundColors = `
               .quick-btn:hover { background: rgba(0, 255, 65, 0.2) !important; }
               .bbs-main-item:hover { background: rgba(0, 255, 65, 0.2) !important; }
               .bbs-room-item:hover { background: rgba(0, 255, 65, 0.25) !important; }
               .pm-conversation-item:hover { background: rgba(0, 255, 65, 0.2) !important; }
               .user-item:hover { background: rgba(0, 255, 65, 0.15) !important; }
               .room-list li:hover, .user-list li:hover { background: rgba(0, 255, 65, 0.15) !important; }
           `;
           break;
   }

   style.textContent = messageColors + backgroundColors;
   document.head.appendChild(style);
}

function showThemeSelector() {
   document.getElementById('themeModal').style.display = 'flex';
}

function closeThemeModal() {
   document.getElementById('themeModal').style.display = 'none';
   const savedTheme = localStorage.getItem('termlink-theme') || 'amber';
   applyTheme(savedTheme);
   setupThemeSelector();
}

function applySelectedTheme() {
   const selectedTheme = document.querySelector('input[name="themeOption"]:checked')?.value;
   if (selectedTheme) {
       applyTheme(selectedTheme);
       closeThemeModal();
   }
}

function setupCursor() {
   const cursor = document.getElementById('retroCursor');

   document.addEventListener('mousemove', (e) => {
       cursor.style.left = e.clientX + 'px';
       cursor.style.top = e.clientY + 'px';
   });

   document.addEventListener('mouseenter', (e) => {
       if (e.target && e.target.classList &&
           (e.target.classList.contains('fallout-btn') || 
            e.target.classList.contains('quick-btn') ||
            e.target.classList.contains('fallout-input') ||
            e.target.classList.contains('voice-btn') ||
            e.target.classList.contains('bbs-main-item') ||
            e.target.classList.contains('bbs-room-item') ||
            e.target.classList.contains('bbs-enter-btn'))) {
           cursor.style.transform = 'scale(1.5)';
           cursor.querySelector('.cursor-block').style.background = 'var(--primary-light)';
       }
   }, true);

   document.addEventListener('mouseleave', (e) => {
       if (e.target && e.target.classList &&
           (e.target.classList.contains('fallout-btn') || 
            e.target.classList.contains('quick-btn') ||
            e.target.classList.contains('fallout-input') ||
            e.target.classList.contains('voice-btn') ||
            e.target.classList.contains('bbs-main-item') ||
            e.target.classList.contains('bbs-room-item') ||
            e.target.classList.contains('bbs-enter-btn'))) {
           cursor.style.transform = 'scale(1)';
           cursor.querySelector('.cursor-block').style.background = 'var(--primary)';
       }
   }, true);

   document.addEventListener('mousedown', () => {
       cursor.style.transform = 'scale(0.8)';
       cursor.querySelector('.cursor-block').style.background = 'var(--primary-dark)';
   });

   document.addEventListener('mouseup', () => {
       cursor.style.transform = 'scale(1)';
       cursor.querySelector('.cursor-block').style.background = 'var(--primary)';
   });
}

function initializeNotifications() {
   if ('Notification' in window) {
       if (Notification.permission === 'default') {
           Notification.requestPermission().then(permission => {
               if (permission === 'granted') {
                   logMessage('[SYSTEM] Notifications enabled', 'system-msg');
               }
           });
       }
   }
}

function showNotification(title, message) {
   if ('Notification' in window && Notification.permission === 'granted' && document.hidden) {
       const notification = new Notification(title, {
           body: message,
           icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" fill="%23ff9500"/><text x="16" y="20" text-anchor="middle" font-family="monospace" font-size="16" fill="%23000">T</text></svg>',
           tag: 'termlink-message'
       });

       setTimeout(() => {
           notification.close();
       }, 5000);
   }
}

function addTransitions() {
   const style = document.createElement('style');
   style.textContent = `
       .message-output {
           transition: opacity 0.3s ease, transform 0.3s ease;
       }

       .fallout-btn, .quick-btn, .voice-btn {
           transition: all 0.3s ease;
       }

       .led-indicator {
           transition: all 0.5s ease;
       }

       .file-modal, .theme-modal {
           transition: opacity 0.3s ease;
       }

       .fallout-input:focus {
           transition: all 0.3s ease;
       }
   `;
   document.head.appendChild(style);
}

document.addEventListener('keydown', (e) => {

   if (e.target.tagName.toLowerCase() === 'input') return;

   if (e.key === 'Escape') {
       if (document.getElementById('fileModal').style.display === 'flex') {
           closeFileModal();
       } else if (document.getElementById('themeModal').style.display === 'flex') {
           closeThemeModal();
       } else if (document.getElementById('pmChatInterface').style.display === 'block') {
           showPMConversations();
       } else if (document.getElementById('pmConversationsMenu').style.display === 'block') {
           showBBSMainMenu();
       } else if (document.getElementById('mainInterface').style.display !== 'none') {
           showBBSMainMenu();
       }
   }

   if (e.ctrlKey && e.key === 'l') {
       e.preventDefault();
       clearTerminal();
   }

   if (e.ctrlKey && e.key === 'u') {
       e.preventDefault();
       executeQuickCommand('/users');
   }

   if (e.ctrlKey && e.key === 'r') {
       e.preventDefault();
       executeQuickCommand('/rooms');
   }

   if (e.ctrlKey && e.key === 'h') {
       e.preventDefault();
       showHelp();
   }

   if (e.ctrlKey && e.key === 'f') {
       e.preventDefault();
       showFileModal();
   }

   if (e.ctrlKey && e.shiftKey && e.key === 'T') {
       e.preventDefault();
       showThemeSelector();
   }

   if (e.ctrlKey && e.key === 'm') {
       e.preventDefault();
       showBBSMainMenu();
   }
});

window.addEventListener('error', (e) => {
   console.error('Global error:', e.error);
   if (isConnected) {
       logMessage(`[ERROR] ${e.message}`, 'server-msg');
   }
});

window.addEventListener('unhandledrejection', (e) => {
   console.error('Unhandled promise rejection:', e.reason);
   if (isConnected) {
       logMessage(`[ERROR] Connection issue detected`, 'server-msg');
   }
});

function showSystemStatus() {
   console.log('🚀 RobCo Termlink Interface v2.1.7 Loaded');
   console.log('📡 Voice Chat System Ready');
   console.log('📁 File Transmission System Online');
   console.log('🔐 Authentication Module Active');
   console.log('🎨 Theme System Active');
   console.log('⚡ All systems operational');

   window.startTime = Date.now();
}

setTimeout(() => {
   setupThemeSystem();
   if (isConnected) {
       initializeNotifications();
   }
}, 1000);

setTimeout(showSystemStatus, 3000);