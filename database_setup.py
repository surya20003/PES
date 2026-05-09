#!/usr/bin/env python3

"""
Database setup script for AI Chat App
Creates all necessary tables and inserts sample data
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'ai_chat_app'),
    'charset': 'utf8mb4'
}

def get_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def execute_script(connection, script):
    """Execute SQL script"""
    cursor = connection.cursor()
    try:
        for statement in script.split(';'):
            if statement.strip():
                cursor.execute(statement)
        connection.commit()
        print("✅ Database setup completed successfully!")
    except Error as e:
        print(f"❌ Error executing script: {e}")
        connection.rollback()
    finally:
        cursor.close()

# SQL Script to create all tables
SQL_SCRIPT = """
-- Create database if not exists
CREATE DATABASE IF NOT EXISTS ai_chat_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the database
USE ai_chat_app;

-- Users table
CREATE TABLE IF NOT EXISTS users (
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

-- Rooms table
CREATE TABLE IF NOT EXISTS rooms (
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

-- Room participants table
CREATE TABLE IF NOT EXISTS room_participants (
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

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
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

-- Message reactions table
CREATE TABLE IF NOT EXISTS message_reactions (
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

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_token_hash (token_hash),
    INDEX idx_expires_at (expires_at)
);

-- AI conversation context table
CREATE TABLE IF NOT EXISTS ai_context (
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

-- Insert default AI user
INSERT IGNORE INTO users (username, email, password_hash, is_active) VALUES 
('ai-assistant', 'ai@chatapp.com', 'dummy-hash-for-ai-user', TRUE);

-- Insert sample users
INSERT IGNORE INTO users (username, email, password_hash) VALUES 
('testuser', 'test@example.com', '$2b$12$dummy.hash.for.testing'),
('alice', 'alice@example.com', '$2b$12$dummy.hash.for.alice'),
('bob', 'bob@example.com', '$2b$12$dummy.hash.for.bob');

-- Create a sample room
INSERT IGNORE INTO rooms (name, description, type, created_by) VALUES 
('General Chat', 'A general chat room for everyone', 'group', 1);

-- Add users to the room
INSERT IGNORE INTO room_participants (room_id, user_id, role) VALUES 
(1, 1, 'admin'),
(1, 2, 'member'),
(1, 3, 'member'),
(1, 4, 'member');

-- Add sample messages
INSERT IGNORE INTO messages (room_id, user_id, message, type) VALUES 
(1, 1, 'Welcome to the AI Chat App!', 'user'),
(1, 4, 'Hello! I''m the AI assistant. How can I help you today?', 'ai'),
(1, 2, 'This is great! Can you tell me more about the features?', 'user'),
(1, 4, 'This app supports real-time messaging, multiple rooms, AI responses, and much more!', 'ai');
"""

def main():
    """Main function to setup database"""
    print("🗄️  Setting up AI Chat App Database...")
    
    # Connect to MySQL server (without database first)
    config = DB_CONFIG.copy()
    del config['database']  # Remove database to connect to server
    
    try:
        connection = mysql.connector.connect(**config)
        print("✅ Connected to MySQL server")
        
        # Execute the setup script
        execute_script(connection, SQL_SCRIPT)
        
    except Error as e:
        print(f"❌ Database setup failed: {e}")
        return 1
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("🔌 Connection closed")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
