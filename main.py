from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import mysql.connector
from mysql.connector import Error
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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'ai_chat_app'),
    'charset': 'utf8mb4',
    'autocommit': True
}

# JWT Secret
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')

# Database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

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
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch == "one":
            result = cursor.fetchone()
        elif fetch == "many":
            result = cursor.fetchall()
        else:
            result = cursor.lastrowid
        connection.commit()
        return result
    finally:
        cursor.close()
        connection.close()

# Authentication Routes
@app.post("/api/auth/register", 
          summary="Register a new user",
          description="Create a new user account with username, email and password",
          response_model=dict,
          tags=["Authentication"])
async def register(user: UserCreate):
    try:
        # Check if user exists
        existing_user = execute_query(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (user.username, user.email),
            fetch="one"
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Hash password
        hashed_password = hash_password(user.password)
        
        # Create user
        user_id = execute_query(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (user.username, user.email, hashed_password),
            fetch="id"
        )
        
        # Get created user
        new_user = execute_query(
            "SELECT id, username, email, avatar FROM users WHERE id = %s",
            (user_id,),
            fetch="one"
        )
        
        # Generate token
        token = create_access_token({"username": new_user["username"], "userId": new_user["id"]})
        
        return {
            "message": "User registered successfully",
            "token": token,
            "user": new_user
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login",
          summary="User login",
          description="Authenticate user and return JWT token",
          response_model=dict,
          tags=["Authentication"])
async def login(user: UserLogin):
    try:
        # Find user
        db_user = execute_query(
            "SELECT id, username, email, password_hash, avatar FROM users WHERE username = %s OR email = %s",
            (user.username, user.username),
            fetch="one"
        )
        
        if not db_user or not verify_password(user.password, db_user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last seen
        execute_query(
            "UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE id = %s",
            (db_user["id"],)
        )
        
        # Generate token
        token = create_access_token({"username": db_user["username"], "userId": db_user["id"]})
        
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/me",
         summary="Get current user",
         description="Get details of currently authenticated user",
         response_model=dict,
         tags=["Authentication"])
async def get_current_user(current_user: dict = Depends(verify_token)):
    try:
        user = execute_query(
            "SELECT id, username, email, avatar, last_seen FROM users WHERE id = %s AND is_active = TRUE",
            (current_user["userId"],),
            fetch="one"
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"user": user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/auth/profile",
         summary="Update user profile",
         description="Update current user's profile information",
         response_model=dict,
         tags=["Authentication"])
async def update_profile(
    profile_data: dict,
    current_user: dict = Depends(verify_token)
):
    try:
        updates = []
        params = []
        
        if "username" in profile_data:
            updates.append("username = %s")
            params.append(profile_data["username"])
        if "email" in profile_data:
            updates.append("email = %s")
            params.append(profile_data["email"])
        if "avatar" in profile_data:
            updates.append("avatar = %s")
            params.append(profile_data["avatar"])
        
        if not updates:
            raise HTTPException(status_code=400, detail="No valid fields provided")
        
        params.append(current_user["userId"])
        
        execute_query(
            f"UPDATE users SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            tuple(params)
        )
        
        updated_user = execute_query(
            "SELECT id, username, email, avatar FROM users WHERE id = %s",
            (current_user["userId"],),
            fetch="one"
        )
        
        return {
            "message": "Profile updated successfully",
            "user": updated_user
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat Routes
@app.get("/api/chat/rooms",
         summary="Get user rooms",
         description="Get all chat rooms for current user",
         response_model=dict,
         tags=["Chat"])
async def get_user_rooms(current_user: dict = Depends(verify_token)):
    try:
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
            WHERE rp.user_id = %s AND r.is_active = TRUE
            GROUP BY r.id, rp.role
            ORDER BY r.last_activity DESC
        """, (current_user["userId"],))
        
        return {"rooms": rooms}
    except Exception as e:
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
            "INSERT INTO rooms (name, description, type, created_by) VALUES (%s, %s, %s, %s)",
            (room.name, room.description, room.type, current_user["userId"]),
            fetch="id"
        )
        
        # Add creator as participant
        execute_query(
            "INSERT INTO room_participants (room_id, user_id, role) VALUES (%s, %s, 'admin')",
            (room_id, current_user["userId"])
        )
        
        # Get created room
        new_room = execute_query(
            "SELECT id, name, description, type, created_by, last_activity FROM rooms WHERE id = %s",
            (room_id,),
            fetch="one"
        )
        
        return {"room": new_room}
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
        # Check if user has access
        participant = execute_query(
            "SELECT 1 FROM room_participants WHERE room_id = %s AND user_id = %s",
            (room_id, current_user["userId"]),
            fetch="one"
        )
        if not participant:
            raise HTTPException(status_code=403, detail="Access denied to this room")
        
        # Get room details
        room = execute_query("""
            SELECT r.*, u.username as creator_username
            FROM rooms r
            LEFT JOIN users u ON r.created_by = u.id
            WHERE r.id = %s AND r.is_active = TRUE
        """, (room_id,), fetch="one")
        
        if not room:
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
            WHERE rp.room_id = %s AND u.is_active = TRUE
            ORDER BY rp.joined_at ASC
        """, (room_id,))
        
        return {"room": room, "participants": participants}
    except Exception as e:
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
        # Check if user has access
        participant = execute_query(
            "SELECT 1 FROM room_participants WHERE room_id = %s AND user_id = %s",
            (room_id, current_user["userId"]),
            fetch="one"
        )
        if not participant:
            raise HTTPException(status_code=403, detail="Access denied to this room")
        
        offset = (page - 1) * limit
        
        # Get messages
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
            WHERE m.room_id = %s
            ORDER BY m.created_at DESC
            LIMIT %s OFFSET %s
        """, (room_id, limit, offset))
        
        # Get total count
        total = execute_query(
            "SELECT COUNT(*) as total FROM messages WHERE room_id = %s",
            (room_id,),
            fetch="one"
        )
        
        return {
            "messages": messages,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total["total"],
                "pages": (total["total"] + limit - 1) // limit
            }
        }
    except Exception as e:
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
        # Check if user has access
        participant = execute_query(
            "SELECT 1 FROM room_participants WHERE room_id = %s AND user_id = %s",
            (room_id, current_user["userId"]),
            fetch="one"
        )
        if not participant:
            raise HTTPException(status_code=403, detail="Access denied to this room")
        
        # Create message
        message_id = execute_query(
            "INSERT INTO messages (room_id, user_id, message, type, reply_to) VALUES (%s, %s, %s, %s, %s)",
            (room_id, current_user["userId"], message.message, message.type, message.reply_to),
            fetch="id"
        )
        
        # Update room activity
        execute_query(
            "UPDATE rooms SET last_activity = CURRENT_TIMESTAMP WHERE id = %s",
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
            WHERE m.id = %s
        """, (message_id,), fetch="one")
        
        # Generate AI response if user message
        if message.type == "user":
            asyncio.create_task(generate_ai_response(room_id, message.message))
        
        return {"message": new_message}
    except Exception as e:
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
            "SELECT role FROM room_participants WHERE room_id = %s AND user_id = %s",
            (room_id, current_user["userId"]),
            fetch="one"
        )
        if not participant:
            raise HTTPException(status_code=403, detail="Access denied to this room")
        
        # Get message details
        message = execute_query(
            "SELECT user_id, type FROM messages WHERE id = %s AND room_id = %s",
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
            "DELETE FROM message_reactions WHERE message_id = %s",
            (message_id,)
        )
        
        # Delete the message
        execute_query(
            "DELETE FROM messages WHERE id = %s AND room_id = %s",
            (message_id, room_id)
        )
        
        return {
            "message": "Message deleted successfully",
            "message_id": message_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/rooms/{room_id}/messages/{message_id}/reactions",
           summary="Remove reaction",
           description="Remove a user's reaction from a message",
           response_model=dict,
           tags=["Chat"])
async def remove_reaction(
    room_id: int,
    message_id: int,
    emoji: str,
    current_user: dict = Depends(verify_token)
):
    try:
        # Check if user has access to room
        participant = execute_query(
            "SELECT 1 FROM room_participants WHERE room_id = %s AND user_id = %s",
            (room_id, current_user["userId"]),
            fetch="one"
        )
        if not participant:
            raise HTTPException(status_code=403, detail="Access denied to this room")
        
        # Check if message exists
        message = execute_query(
            "SELECT 1 FROM messages WHERE id = %s AND room_id = %s",
            (message_id, room_id),
            fetch="one"
        )
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Remove reaction
        execute_query(
            "DELETE FROM message_reactions WHERE message_id = %s AND user_id = %s AND emoji = %s",
            (message_id, current_user["userId"], emoji)
        )
        
        return {
            "message": "Reaction removed successfully",
            "message_id": message_id,
            "emoji": emoji
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
                "INSERT INTO messages (room_id, user_id, message, type) VALUES (%s, %s, %s, 'ai')",
                (room_id, ai_user["id"], ai_message),
                fetch="id"
            )
            
            # Update room activity
            execute_query(
                "UPDATE rooms SET last_activity = CURRENT_TIMESTAMP WHERE id = %s",
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
    uvicorn.run(app, host="0.0.0.0", port=5000)
