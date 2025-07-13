"""
Authentication module for the chat application
"""
from aiohttp import web
from aiohttp_session import setup as setup_session, get_session, new_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import base64
import os
from pathlib import Path
from persistence.authdb import get_user_by_email, get_user_by_username, create_user, verify_password, init_auth_db
import functools

# Get the static directory path
STATIC_DIR = Path(__file__).parent / "static"


def setup_auth(app):
    """Setup authentication for the application"""
    # Generate a secret key for cookie encryption (32 bytes)
    secret_key = os.urandom(32)
    
    # Setup session with encrypted cookies
    setup_session(app, EncryptedCookieStorage(secret_key))
    
    return app


async def get_current_user(request):
    """Get the current logged in user from session"""
    session = await get_session(request)
    user_id = session.get('user_id')
    if user_id:
        return {
            'user_id': user_id,
            'username': session.get('username'),
            'email': session.get('email'),
            'is_anonymous': session.get('is_anonymous', True),
            'is_authenticated': True
        }
    return {'is_authenticated': False}


async def login_user(request, user_data):
    """Log in a user by setting session data"""
    session = await get_session(request)
    session['user_id'] = user_data['id']
    session['username'] = user_data['useruid']
    session['email'] = user_data.get('email')
    session['is_anonymous'] = user_data.get('is_anonymous', True)


async def logout_user(request):
    """Log out the current user"""
    session = await get_session(request)
    session.clear()


def require_auth(handler):
    """Decorator to require authentication for a handler"""
    @functools.wraps(handler)
    async def wrapper(request):
        user = await get_current_user(request)
        if not user['is_authenticated']:
            return web.json_response({'error': 'Authentication required'}, status=401)
        request['user'] = user
        return await handler(request)
    return wrapper


# Login and registration handlers
async def login_handler(request):
    """Handle login form submission"""
    if request.method == 'POST':
        data = await request.post()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username:
            return web.json_response({'error': 'Username is required'}, status=400)
        
        if not password:
            return web.json_response({'error': 'Password is required'}, status=400)
        
        # First try by email
        user_data = get_user_by_email(username)
        if not user_data:
            # Then try by username
            user_data = get_user_by_username(username)
        
        if not user_data:
            return web.json_response({'error': 'Invalid credentials'}, status=401)
        
        # Don't allow login for anonymous users with password
        if user_data['is_anonymous']:
            return web.json_response({'error': 'Invalid credentials'}, status=401)
        
        if not user_data['password_hash']:
            return web.json_response({'error': 'Invalid credentials'}, status=401)
        
        if verify_password(password, user_data['password_hash']):
            await login_user(request, user_data)
            return web.json_response({'success': True, 'username': user_data['useruid']})
        else:
            return web.json_response({'error': 'Invalid credentials'}, status=401)
    
    # Return login form for GET request
    return web.FileResponse(STATIC_DIR / "login.html")


async def register_handler(request):
    """Handle registration form submission"""
    if request.method == 'POST':
        data = await request.post()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        if not username:
            return web.json_response({'error': 'Username is required'}, status=400)
        
        if not email:
            return web.json_response({'error': 'Email is required'}, status=400)
        
        if not password:
            return web.json_response({'error': 'Password is required'}, status=400)
        
        if password != confirm_password:
            return web.json_response({'error': 'Passwords do not match'}, status=400)
        
        if len(password) < 6:
            return web.json_response({'error': 'Password must be at least 6 characters'}, status=400)
        
        # Check if user already exists
        if get_user_by_username(username):
            return web.json_response({'error': 'Username already exists'}, status=400)
        
        if get_user_by_email(email):
            return web.json_response({'error': 'Email already registered'}, status=400)
        
        # Create new user
        try:
            user_id = create_user(username, email, password, is_anonymous=False)
            user_data = {
                'id': user_id,
                'useruid': username,
                'email': email,
                'is_anonymous': False
            }
            await login_user(request, user_data)
            return web.json_response({'success': True, 'username': username})
        except Exception as e:
            return web.json_response({'error': 'Registration failed'}, status=500)
    
    # Return registration form for GET request
    return web.FileResponse(STATIC_DIR / "register.html")


async def anonymous_login_handler(request):
    """Handle anonymous login"""
    data = await request.json()
    username = data.get('username', '').strip()
    
    if not username:
        return web.json_response({'error': 'Username is required'}, status=400)
    
    # Check if username is already taken by a registered user
    existing_user = get_user_by_username(username)
    if existing_user and not existing_user['is_anonymous']:
        return web.json_response({'error': 'Username is already taken by a registered user'}, status=400)
    
    try:
        # Create or get anonymous user
        if existing_user and existing_user['is_anonymous']:
            user_id = existing_user['id']
        else:
            user_id = create_user(username, is_anonymous=True)
        
        user_data = {
            'id': user_id,
            'useruid': username,
            'email': None,
            'is_anonymous': True
        }
        await login_user(request, user_data)
        return web.json_response({'success': True, 'username': username})
    except Exception as e:
        return web.json_response({'error': 'Anonymous login failed'}, status=500)


async def logout_handler(request):
    """Handle logout"""
    await logout_user(request)
    return web.json_response({'success': True})


async def status_handler(request):
    """Get current authentication status"""
    user = await get_current_user(request)
    return web.json_response(user)
