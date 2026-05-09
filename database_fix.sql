-- Drop existing tables and recreate with correct structure
DROP TABLE IF EXISTS message_reactions;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS ai_context;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS room_participants;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS users;

-- Create users table with correct structure
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    avatar VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_last_seen (last_seen)
);

-- Create rooms table
CREATE TABLE rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type ENUM('direct', 'group') DEFAULT 'direct',
    created_by INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_created_by (created_by),
    INDEX idx_last_activity (last_activity),
    INDEX idx_type (type)
);

-- Create room participants table
CREATE TABLE room_participants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    user_id INT NOT NULL,
    role ENUM('admin', 'member') DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_room_user (room_id, user_id),
    INDEX idx_room_id (room_id),
    INDEX idx_user_id (user_id)
);

-- Create messages table
CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    type ENUM('user', 'ai', 'system') DEFAULT 'user',
    is_edited BOOLEAN DEFAULT FALSE,
    edited_at TIMESTAMP NULL,
    reply_to INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reply_to) REFERENCES messages(id) ON DELETE SET NULL,
    INDEX idx_room_id_created (room_id, created_at DESC),
    INDEX idx_user_id_created (user_id, created_at DESC),
    INDEX idx_type (type),
    FULLTEXT idx_message_content (message)
);

-- Create message reactions table
CREATE TABLE message_reactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message_id INT NOT NULL,
    user_id INT NOT NULL,
    emoji VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_message_user_emoji (message_id, user_id, emoji),
    INDEX idx_message_id (message_id),
    INDEX idx_user_id (user_id)
);

-- Create AI context table
CREATE TABLE ai_context (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    user_id INT NOT NULL,
    context_data JSON,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_room_user (room_id, user_id),
    INDEX idx_room_id (room_id),
    INDEX idx_user_id (user_id)
);

-- Insert default AI user with proper password hash
INSERT INTO users (username, email, password_hash, is_active) VALUES 
('ai-assistant', 'ai@chatapp.com', '$2b$12$LQv3c1yqBWVHxkd0Ld1uXKv5jO2Yxq9rHqGvTqTqGd0f', TRUE);

-- Insert sample users with proper password hashes
INSERT INTO users (username, email, password_hash) VALUES 
('testuser', 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0Ld1uXKv5jO2Yxq9rHqGvTqTqGd0f'),
('alice', 'alice@example.com', '$2b$12$LQv3c1yqBWVHxkd0Ld1uXKv5jO2Yxq9rHqGvTqTqGd0f'),
('bob', 'bob@example.com', '$2b$12$LQv3c1yqBWVHxkd0Ld1uXKv5jO2Yxq9rHqGvTqTqGd0f');

-- Create a sample room
INSERT INTO rooms (name, description, type, created_by) VALUES 
('General Chat', 'A general chat room for everyone', 'group', 1);

-- Add users to room
INSERT INTO room_participants (room_id, user_id, role) VALUES 
(1, 1, 'admin'),
(1, 2, 'member'),
(1, 3, 'member'),
(1, 4, 'member'),
(1, 5, 'member');

-- Add sample messages
INSERT INTO messages (room_id, user_id, message, type) VALUES 
(1, 1, 'Welcome to AI Chat App!', 'user'),
(1, 5, 'Hello! I''m AI assistant. How can I help you today?', 'ai'),
(1, 2, 'This is great! Can you tell me more about features?', 'user'),
(1, 5, 'This app supports real-time messaging, multiple rooms, AI responses, and much more!', 'ai');
