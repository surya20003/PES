# 🤖 AI Chat API Backend

A comprehensive FastAPI backend for AI-powered chat applications with real-time messaging, user authentication, and intelligent AI responses.

## 🚀 Features

- **🔐 Authentication**: JWT-based user authentication with registration and login
- **💬 Real-time Chat**: WebSocket support for live messaging
- **🤖 AI Integration**: OpenAI API integration with smart fallback responses
- **📊 Database**: MySQL with optimized schema and relationships
- **📝 API Documentation**: Auto-generated Swagger/ReDoc documentation
- **🔒 Security**: Password hashing, CORS middleware, input validation
- **📡 WebSocket**: Real-time message broadcasting
- **🏥 Health Checks**: Monitoring and health check endpoints

## 📋 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user profile
- `PUT /api/auth/profile` - Update user profile

### Chat Management
- `GET /api/chat/rooms` - Get user's chat rooms
- `POST /api/chat/rooms` - Create new chat room
- `GET /api/chat/rooms/{room_id}` - Get room details
- `GET /api/chat/rooms/{room_id}/messages` - Get room messages (paginated)
- `POST /api/chat/rooms/{room_id}/messages` - Send message to room

### WebSocket
- `WS /ws/{room_id}` - Real-time messaging connection

### System
- `GET /health` - Health check endpoint
- `GET /docs` - Swagger API documentation
- `GET /redoc` - ReDoc API documentation

## 🛠️ Technology Stack

- **FastAPI**: Modern Python web framework
- **MySQL**: Relational database
- **JWT**: Token-based authentication
- **WebSocket**: Real-time communication
- **OpenAI**: AI integration
- **Pydantic**: Data validation
- **bcrypt**: Password hashing
- **Uvicorn**: ASGI server

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Database Setup
```bash
python database_setup.py
```

### 4. Run Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

### 5. Access API
- **API Documentation**: http://localhost:5000/docs
- **ReDoc Documentation**: http://localhost:5000/resdoc
- **Health Check**: http://localhost:5000/health

## 📊 Database Schema

### Users Table
- User accounts with authentication
- Profile information and avatars
- Activity tracking

### Rooms Table
- Chat rooms (direct and group)
- Room metadata and settings
- Activity tracking

### Messages Table
- Chat messages with full-text search
- Message types (user, AI, system)
- Reply threading support

### Room Participants
- Room membership management
- Role-based permissions (admin/member)

### Message Reactions
- Emoji reactions to messages
- User-specific reactions

### AI Context
- Conversation context for AI
- Room-specific AI memory

## 🔧 Configuration

### Environment Variables
```env
# Server
PORT=5000
HOST=0.0.0.0

# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ai_chat_app

# Security
JWT_SECRET=your-super-secret-jwt-key

# AI Integration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo

# CORS
FRONTEND_URL=http://localhost:3000
```

## 🤖 AI Integration

### OpenAI Integration
- Automatic AI responses to user messages
- Context-aware conversations
- Configurable model and parameters

### Fallback Responses
- Smart keyword-based responses
- Multiple response templates
- Topic-specific answers (MySQL, React, Python, etc.)

## 🔒 Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Authentication**: Secure token-based auth
- **Input Validation**: Pydantic models
- **CORS Protection**: Configurable origins
- **SQL Injection Prevention**: Parameterized queries
- **Rate Limiting**: Ready for implementation

## 📡 Real-time Features

### WebSocket Implementation
- Room-based connections
- Message broadcasting
- Connection management
- Automatic reconnection support

### Message Broadcasting
- Real-time message delivery
- AI response notifications
- User presence indicators

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t ai-chat-backend .
```

### Run Container
```bash
docker run -p 5000:5000 --env-file .env ai-chat-backend
```

### Docker Compose
```bash
docker-compose up --build
```

## 📝 API Examples

### User Registration
```bash
curl -X POST "http://localhost:5000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### User Login
```bash
curl -X POST "http://localhost:5000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### Send Message
```bash
curl -X POST "http://localhost:5000/api/chat/rooms/1/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "message": "Hello, AI!",
    "type": "user"
  }'
```

## 🧪 Testing

### Health Check
```bash
curl http://localhost:5000/health
```

### API Documentation
Visit http://localhost:5000/docs for interactive API testing

## 🔍 Monitoring

### Health Endpoints
- `/health` - Basic health check
- Database connectivity
- Service status

### Logging
- Structured error logging
- Request/response logging
- Performance monitoring ready

## 🚀 Production Considerations

### Security
- Use HTTPS in production
- Rotate JWT secrets regularly
- Implement rate limiting
- Set up proper CORS origins
- Use environment variables for secrets

### Performance
- Database connection pooling
- Redis for session storage
- CDN for static assets
- Load balancing

### Scalability
- Horizontal scaling support
- Database sharding ready
- Microservices architecture compatible

## 📚 Documentation

- **Swagger UI**: Interactive API documentation
- **ReDoc**: Alternative API documentation
- **OpenAPI Schema**: Machine-readable API spec
- **Code Comments**: Comprehensive inline documentation

## 🤝 Contributing

1. Fork repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Check the API documentation at `/docs`
- Review the health check endpoint
- Check logs for error messages
- Create an issue in the repository
