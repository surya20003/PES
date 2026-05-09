from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import sqlite3
import hashlib
import jwt
import bcrypt
import asyncio
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import openai

load_dotenv()

# OpenAI Configuration
openai.api_key = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

# Create FastAPI app with Swagger documentation
app = FastAPI(
    title="AI Chat API",
    description="A comprehensive AI chat application backend with FastAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Security
security = HTTPBearer()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Configuration
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_chat_app.db")

# JWT Secret
JWT_SECRET = os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-change-this-in-production-32-bytes-minimum')

# Database connection
def get_db_connection():
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection

# Execute query function
def execute_query(query: str, params: tuple = None, fetch: str = "all"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch == "one":
            result = cursor.fetchone()
        elif fetch == "many":
            result = cursor.fetchall()
        elif fetch == "id":
            result = cursor.lastrowid
        else:
            result = cursor.fetchall()
        
        # Always commit for INSERT/UPDATE/DELETE operations
        if any(keyword in query.upper() for keyword in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP']):
            conn.commit()
        else:
            # For SELECT queries, don't commit but still close connection
            pass
        
        return result
    except Exception as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

# Initialize database
def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            avatar TEXT,
            is_active BOOLEAN DEFAULT 1,
            last_seen DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            type TEXT DEFAULT 'direct',
            created_by INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS room_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT DEFAULT 'member',
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(room_id, user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'user',
            is_edited BOOLEAN DEFAULT 0,
            edited_at DATETIME,
            reply_to INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (reply_to) REFERENCES messages(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            emoji TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (message_id) REFERENCES messages(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(message_id, user_id, emoji)
        )
    ''')
    
    # Insert default AI user
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash, is_active)
        VALUES ('ai-assistant', 'ai@chatapp.com', 'dummy-hash-for-ai-user', 1)
    ''')
    
    # Insert sample users
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash)
        VALUES ('testuser', 'test@example.com', '$2b$12$dummy.hash.for.testing'),
               ('alice', 'alice@example.com', '$2b$12$dummy.hash.for.alice'),
               ('bob', 'bob@example.com', '$2b$12$dummy.hash.for.bob')
    ''')
    
    # Create sample room
    cursor.execute('''
        INSERT OR IGNORE INTO rooms (name, description, type, created_by)
        VALUES ('General Chat', 'A general chat room for everyone', 'group', 1)
    ''')
    
    # Add users to room
    cursor.execute('''
        INSERT OR IGNORE INTO room_participants (room_id, user_id, role)
        VALUES (1, 1, 'admin'), (1, 2, 'member'), (1, 3, 'member'), (1, 4, 'member')
    ''')
    
    # Add sample messages
    cursor.execute('''
        INSERT OR IGNORE INTO messages (room_id, user_id, message, type)
        VALUES (1, 1, 'Welcome to AI Chat App!', 'user'),
               (1, 4, 'Hello! I''m AI assistant. How can I help you today?', 'ai'),
               (1, 2, 'This is great! Can you tell me more about features?', 'user'),
               (1, 4, 'This app supports real-time messaging, multiple rooms, AI responses, and much more!', 'ai')
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
try:
    init_database()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    raise e
    # Continue anyway - database might already exist

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    avatar: Optional[str] = None
    last_seen: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class RoomCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: str = "direct"

class RoomResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    type: str
    created_by: int
    last_activity: datetime
    participant_count: int

class MessageCreate(BaseModel):
    room_id: int
    message: str
    type: str = "user"
    reply_to: Optional[int] = None

class MessageResponse(BaseModel):
    id: int
    room_id: int
    user_id: int
    message: str
    type: str
    username: str
    avatar: Optional[str]
    created_at: datetime
    is_edited: bool = False
    reaction_count: int = 0

# Authentication
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def execute_query(query: str, params: tuple = None, fetch: str = "all"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch == "one":
            result = cursor.fetchone()
        elif fetch == "many":
            result = cursor.fetchall()
        else:
            result = cursor.lastrowid
        
        conn.commit()
        return result
    finally:
        conn.close()

# Authentication Routes
@app.post("/api/auth/register", 
          summary="Register a new user",
          description="Create a new user account with username, email and password",
          response_model=dict,
          tags=["Authentication"])
async def register(user: UserCreate):
    try:
        print(f"🔍 Registration attempt: {user.username}, {user.email}")
        
        # Check if user exists
        existing_user = execute_query(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (user.username, user.email),
            fetch="one"
        )
        if existing_user:
            print(f"❌ User already exists: {user.username}")
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Use plain password (no hashing)
        print(f"📝 Creating user with password: {user.password}")
        # Create user
        user_id = execute_query(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (user.username, user.email, user.password),
            fetch="id"
        )
        
        print(f"✅ User created with ID: {user_id}")
        
        # Get created user
        new_user = execute_query(
            "SELECT id, username, email, avatar FROM users WHERE id = ?",
            (user_id,),
            fetch="one"
        )
        
        if not new_user:
            print(f"❌ Failed to retrieve created user with ID: {user_id}")
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # Generate token
        token = create_access_token({"username": new_user["username"], "userId": new_user["id"]})
        
        print(f"🎉 Registration successful for: {new_user['username']}")
        return {
            "message": "User registered successfully",
            "token": token,
            "user": dict(new_user)
        }
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login",
          summary="User login",
          description="Authenticate user and return JWT token",
          response_model=dict,
          tags=["Authentication"])
async def login(user: UserLogin):
    try:
        print(f"🔍 Login attempt: {user.username}")
        
        # Find user
        db_user = execute_query(
            "SELECT id, username, email, password, avatar FROM users WHERE username = ? OR email = ?",
            (user.username, user.username),
            fetch="one"
        )
        
        if not db_user:
            print(f"❌ User not found: {user.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if db_user["password"] != user.password:
            print(f"❌ Password mismatch for user: {user.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last seen
        execute_query(
            "UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE id = ?",
            (db_user["id"],)
        )
        
        # Generate token
        token = create_access_token({"username": db_user["username"], "userId": db_user["id"]})
        
        print(f"✅ Login successful for: {db_user['username']}")
        return {
            "message": "Login successful",
            "token": token,
            "user": {
                "id": db_user["id"],
                "username": db_user["username"],
                "email": db_user["email"],
                "avatar": db_user["avatar"]
            }
        }
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/me",
         summary="Get current user",
         description="Get details of currently authenticated user",
         response_model=dict,
         tags=["Authentication"])
async def get_current_user(current_user: dict = Depends(verify_token)):
    try:
        user = execute_query(
            "SELECT id, username, email, avatar, last_seen FROM users WHERE id = ? AND is_active = 1",
            (current_user["userId"],),
            fetch="one"
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"user": dict(user)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/auth/profile",
         summary="Update user profile",
         description="Update current user's profile information",
         response_model=dict,
         tags=["Authentication"])
async def update_profile(
    profile: UserUpdate,
    current_user: dict = Depends(verify_token)
):
    try:
        print(f"🔍 Updating profile for user: {current_user['username']}")
        
        # Check if username/email already exists
        if profile.username or profile.email:
            existing_user = execute_query(
                "SELECT id FROM users WHERE (username = ? OR email = ?) AND id != ?",
                (profile.username or current_user["username"], 
                 profile.email or current_user["email"], 
                 current_user["userId"]),
                fetch="one"
            )
            if existing_user:
                print(f"❌ Username/email already exists")
                raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Update user
        update_fields = []
        update_values = []
        
        if profile.username:
            update_fields.append("username = ?")
            update_values.append(profile.username)
        
        if profile.email:
            update_fields.append("email = ?")
            update_values.append(profile.email)
        
        if profile.password:
            hashed_password = hash_password(profile.password)
            update_fields.append("password = ?")
            update_values.append(hashed_password)
        
        if update_fields:
            update_values.append(current_user["userId"])
            query = f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            execute_query(query, tuple(update_values))
            print(f"✅ Profile updated successfully")
        
        # Get updated user
        updated_user = execute_query(
            "SELECT id, username, email, avatar FROM users WHERE id = ?",
            (current_user["userId"],),
            fetch="one"
        )
        
        return {
            "message": "Profile updated successfully",
            "user": dict(updated_user)
        }
    except Exception as e:
        print(f"❌ Profile update error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Chat Routes
@app.get("/api/chat/rooms",
         summary="Get user rooms",
         description="Get all chat rooms for current user",
         response_model=dict,
         tags=["Chat"])
async def get_user_rooms(current_user: dict = Depends(verify_token)):
    try:
        print(f"🔍 Getting rooms for user: {current_user}")
        
        rooms = execute_query("""
            SELECT 
                r.id,
                r.name,
                r.description,
                r.type,
                r.last_activity,
                rp.role,
                COUNT(m.id) as message_count,
                MAX(m.created_at) as last_message_time
            FROM rooms r
            JOIN room_participants rp ON r.id = rp.room_id
            LEFT JOIN messages m ON r.id = m.room_id
            WHERE rp.user_id = ? AND r.is_active = 1
            GROUP BY r.id, rp.role
            ORDER BY r.last_activity DESC
        """, (current_user["userId"],), fetch="many")
        
        rooms_list = list(rooms) if rooms else []
        print(f"✅ Found {len(rooms_list)} rooms for user {current_user['username']}")
        return {"rooms": [dict(room) for room in rooms_list]}
    except Exception as e:
        print(f"❌ Error getting rooms: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/rooms",
         summary="Create room",
         description="Create a new chat room",
         response_model=dict,
         tags=["Chat"])
async def create_room(
    room: RoomCreate,
    current_user: dict = Depends(verify_token)
):
    try:
        # Create room
        room_id = execute_query(
            "INSERT INTO rooms (name, description, type, created_by) VALUES (?, ?, ?, ?)",
            (room.name, room.description, room.type, current_user["userId"]),
            fetch="id"
        )
        
        # Add creator as participant
        execute_query(
            "INSERT INTO room_participants (room_id, user_id, role) VALUES (?, ?, 'admin')",
            (room_id, current_user["userId"])
        )
        
        # Get created room
        new_room = execute_query(
            "SELECT id, name, description, type, created_by, last_activity FROM rooms WHERE id = ?",
            (room_id,),
            fetch="one"
        )
        
        return {"room": dict(new_room)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/rooms/{room_id}",
         summary="Get room details",
         description="Get detailed information about a specific room",
         response_model=dict,
         tags=["Chat"])
async def get_room_details(
    room_id: int,
    current_user: dict = Depends(verify_token)
):
    try:
        print(f"🔍 Getting room {room_id} for user {current_user['username']}")
        
        # Check if user has access
        participant = execute_query(
            "SELECT 1 FROM room_participants WHERE room_id = ? AND user_id = ?",
            (room_id, current_user["userId"]),
            fetch="one"
        )
        if not participant:
            print(f"❌ User {current_user['username']} not in room {room_id}")
            raise HTTPException(status_code=403, detail="Access denied to this room")
        
        # Get room details
        room = execute_query("""
            SELECT r.*, u.username as creator_username
            FROM rooms r
            LEFT JOIN users u ON r.created_by = u.id
            WHERE r.id = ? AND r.is_active = 1
        """, (room_id,), fetch="one")
        
        if not room:
            print(f"❌ Room {room_id} not found")
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Get participants
        participants = execute_query("""
            SELECT 
                u.id,
                u.username,
                u.avatar,
                u.last_seen,
                rp.role,
                rp.joined_at
            FROM room_participants rp
            JOIN users u ON rp.user_id = u.id
            WHERE rp.room_id = ? AND u.is_active = 1
            ORDER BY rp.joined_at ASC
        """, (room_id,))
        
        participants_list = list(participants) if participants else []
        print(f"✅ Room {room_id} found with {len(participants_list)} participants")
        return {"room": dict(room), "participants": [dict(p) for p in participants_list]}
    except Exception as e:
        print(f"❌ Error getting room {room_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/rooms/{room_id}/messages",
         summary="Get room messages",
         description="Get paginated messages from a room",
         response_model=dict,
         tags=["Chat"])
async def get_room_messages(
    room_id: int,
    page: int = 1,
    limit: int = 50,
    current_user: dict = Depends(verify_token)
):
    try:
        print(f"🔍 Getting messages for room {room_id}, page {page}, user {current_user['username']}")
        
        # Check if user has access
        participant = execute_query(
            "SELECT 1 FROM room_participants WHERE room_id = ? AND user_id = ?",
            (room_id, current_user["userId"]),
            fetch="one"
        )
        if not participant:
            print(f"❌ User {current_user['username']} not in room {room_id}")
            raise HTTPException(status_code=403, detail="Access denied to this room")
        
        # First, let's see what messages actually exist in this room
        all_messages = execute_query(
            "SELECT id, message, type, user_id, created_at FROM messages WHERE room_id = ? ORDER BY created_at DESC",
            (room_id,),
            fetch="many"
        )
        print(f"📊 All messages in room {room_id}: {len(all_messages) if all_messages else 0}")
        for msg in all_messages[:3]:
            print(f"   - Message {msg['id']}: {msg['message'][:50]}...")
        
        offset = (page - 1) * limit
        
        # Get messages with pagination
        messages = execute_query("""
            SELECT 
                m.id,
                m.message,
                m.type,
                m.user_id,
                m.is_edited,
                m.edited_at,
                m.reply_to,
                m.created_at,
                u.username,
                u.avatar,
                (SELECT COUNT(*) FROM message_reactions mr WHERE mr.message_id = m.id) as reaction_count
            FROM messages m
            JOIN users u ON m.user_id = u.id
            WHERE m.room_id = ?
            ORDER BY m.created_at DESC
            LIMIT ? OFFSET ?
        """, (room_id, limit, offset))
        
        # Get total count
        total = execute_query(
            "SELECT COUNT(*) as total FROM messages WHERE room_id = ?",
            (room_id,),
            fetch="one"
        )
        
        messages_list = list(messages) if messages else []
        print(f"✅ Found {len(messages_list)} messages for room {room_id}")
        total_count = total["total"] if total else 0
        return {
            "messages": [dict(msg) for msg in messages_list],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
    except Exception as e:
        print(f"❌ Error getting messages for room {room_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/rooms/{room_id}/messages",
         summary="Send message",
         description="Send a message to a room",
         response_model=dict,
         tags=["Chat"])
async def send_message(
    room_id: int,
    message: MessageCreate,
    current_user: dict = Depends(verify_token)
):
    try:
        print(f"🔍 Sending message to room {room_id} from user {current_user['username']}")
        print(f"📝 Message content: {message.message}")
        
        # Check if user has access
        participant = execute_query(
            "SELECT 1 FROM room_participants WHERE room_id = ? AND user_id = ?",
            (room_id, current_user["userId"]),
            fetch="one"
        )
        if not participant:
            print(f"❌ User {current_user['username']} not in room {room_id}")
            raise HTTPException(status_code=403, detail="Access denied to this room")
        
        # Create message
        message_id = execute_query(
            "INSERT INTO messages (room_id, user_id, message, type, reply_to) VALUES (?, ?, ?, ?, ?)",
            (room_id, current_user["userId"], message.message, message.type, message.reply_to),
            fetch="id"
        )
        
        print(f"✅ Message created with ID: {message_id}")
        
        # Update room activity
        execute_query(
            "UPDATE rooms SET last_activity = CURRENT_TIMESTAMP WHERE id = ?",
            (room_id,)
        )
        
        # Get created message
        new_message = execute_query("""
            SELECT 
                m.id,
                m.message,
                m.type,
                m.user_id,
                m.created_at,
                u.username,
                u.avatar
            FROM messages m
            JOIN users u ON m.user_id = u.id
            WHERE m.id = ?
        """, (message_id,), fetch="one")
        
        print(f"✅ Retrieved message: {dict(new_message)}")
        
        # Generate AI response if user message
        if message.type == "user":
            print(f"🤖 Generating AI response for room {room_id}")
            asyncio.create_task(generate_ai_response(room_id, message.message))
        
        return {"message": dict(new_message)}
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/rooms/{room_id}/messages/{message_id}",
           summary="Delete message",
           description="Delete a message from a room (only message owner or room admin)",
           response_model=dict,
           tags=["Chat"])
async def delete_message(
    room_id: int,
    message_id: int,
    current_user: dict = Depends(verify_token)
):
    try:
        # Check if user has access to room
        participant = execute_query(
            "SELECT role FROM room_participants WHERE room_id = ? AND user_id = ?",
            (room_id, current_user["userId"]),
            fetch="one"
        )
        if not participant:
            raise HTTPException(status_code=403, detail="Access denied to this room")
        
        # Get message details
        message = execute_query(
            "SELECT user_id, type FROM messages WHERE id = ? AND room_id = ?",
            (message_id, room_id),
            fetch="one"
        )
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Check if user can delete message (owner or admin)
        is_owner = message["user_id"] == current_user["userId"]
        is_admin = participant["role"] == "admin"
        is_system_message = message["type"] == "system"
        
        if not is_owner and not is_admin:
            raise HTTPException(status_code=403, detail="Only message owner or room admin can delete messages")
        
        if is_system_message:
            raise HTTPException(status_code=403, detail="System messages cannot be deleted")
        
        # Delete message reactions first
        execute_query(
            "DELETE FROM message_reactions WHERE message_id = ?",
            (message_id,)
        )
        
        # Delete message
        execute_query(
            "DELETE FROM messages WHERE id = ? AND room_id = ?",
            (message_id, room_id)
        )
        
        return {
            "message": "Message deleted successfully",
            "message_id": message_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI Response Generation
async def generate_ai_response(room_id: int, user_message: str):
    try:
        ai_message = ""
        
        # Use OpenAI if API key is available
        if openai.api_key:
            try:
                response = await openai.ChatCompletion.acreate(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant. Be friendly, concise, and helpful."},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                ai_message = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"OpenAI API error: {e}")
                # Fallback to mock responses
                ai_message = get_fallback_response(user_message)
        else:
            # Fallback responses when no OpenAI key
            ai_message = get_fallback_response(user_message)
        
        # Get AI user ID
        ai_user = execute_query(
            "SELECT id FROM users WHERE username = 'ai-assistant'",
            fetch="one"
        )
        
        if ai_user:
            # Create AI message
            message_id = execute_query(
                "INSERT INTO messages (room_id, user_id, message, type) VALUES (?, ?, ?, 'ai')",
                (room_id, ai_user["id"], ai_message),
                fetch="id"
            )
            
            # Update room activity
            execute_query(
                "UPDATE rooms SET last_activity = CURRENT_TIMESTAMP WHERE id = ?",
                (room_id,)
            )
            
            # Broadcast via WebSocket (if implemented)
            await broadcast_message(room_id, {
                "id": message_id,
                "message": ai_message,
                "type": "ai",
                "user_id": ai_user["id"],
                "username": "ai-assistant",
                "created_at": datetime.now().isoformat()
            })
    except Exception as e:
        print(f"AI response error: {e}")

def get_fallback_response(user_message: str) -> str:
    """Fallback AI responses when OpenAI is not available"""
    ai_responses = [
        "That's an interesting question! Let me think about that...",
        "I understand what you're saying. Here's my perspective...",
        "Great point! Have you considered this approach?",
        "I'd be happy to help you with that. Let me provide some insights...",
        "That's a thoughtful observation. Here's what I think..."
    ]
    
    user_lower = user_message.lower()
    if "hello" in user_lower or "hi" in user_lower:
        return "Hello! How can I assist you today?"
    elif "help" in user_lower:
        return "I'm here to help! What do you need assistance with?"
    elif "mysql" in user_lower:
        return "MySQL is a powerful relational database system. It's known for reliability and performance. What specific aspect would you like to know about?"
    elif "react" in user_lower:
        return "React is a popular JavaScript library for building user interfaces. It's component-based and great for creating interactive web applications!"
    elif "python" in user_lower:
        return "Python is a versatile programming language known for its simplicity and readability. It's great for web development, data science, and AI!"
    else:
        return ai_responses[hash(user_message) % len(ai_responses)]

# WebSocket support
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, room_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
    
    async def broadcast(self, room_id: int, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(json.dumps(message))

manager = ConnectionManager()

async def broadcast_message(room_id: int, message: dict):
    await manager.broadcast(room_id, message)

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    # This is a simplified WebSocket implementation
    # In production, you'd want proper authentication
    await manager.connect(websocket, 0, room_id)  # user_id would come from token
    
    try:
        while True:
            data = await websocket.receive_text()
            # Process WebSocket messages here
            await manager.broadcast(room_id, {"type": "message", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

# Health Check
@app.get("/health",
         summary="Health check",
         description="Check if API is running properly",
         response_model=dict,
         tags=["System"])
async def health_check():
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
