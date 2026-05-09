import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  List,
  ListItem,
  Avatar,
  CircularProgress,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import { Send, SmartToy, Person, ExitToApp } from '@mui/icons-material';
import { Message, Room } from '../types';
import { chatAPI } from '../services/api';
import LogoutDialog from './LogoutDialog';

interface ChatRoomProps {
  room: Room;
  onBack: () => void;
}

const ChatRoom: React.FC<ChatRoomProps> = ({ room, onBack }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    loadMessages();
  }, [room.id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadMessages = async () => {
    try {
      setLoading(true);
      const response = await chatAPI.getMessages(room.id);
      setMessages(response.data.messages.reverse());
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    try {
      setSending(true);
      const response = await chatAPI.sendMessage(room.id, {
        message: newMessage,
        type: 'user',
      });
      
      const userMessage: Message = {
        ...response.data.message,
        username: 'You',
        created_at: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, userMessage]);
      setNewMessage('');
      
      // Simulate AI response (in real app, this would come via WebSocket)
      setTimeout(async () => {
        try {
          const aiResponse = await chatAPI.sendMessage(room.id, {
            message: `AI response to: "${newMessage}"`,
            type: 'ai',
          });
          
          const aiMessage: Message = {
            ...aiResponse.data.message,
            username: 'AI Assistant',
            created_at: new Date().toISOString(),
          };
          
          setMessages(prev => [...prev, aiMessage]);
        } catch (error) {
          console.error('Failed to get AI response:', error);
        }
      }, 1000);
      
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setSending(false);
    }
  };

  const handleLogoutClick = () => {
    setLogoutDialogOpen(true);
  };

  const handleConfirmLogout = () => {
    // Clear any local state and redirect to login
    localStorage.removeItem('token');
    window.location.href = '/';
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <Container maxWidth="md" sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Paper sx={{ p: 2, mb: 2, display: 'flex', alignItems: 'center' }}>
        <Button onClick={onBack} sx={{ mr: 2 }}>
          ← Back
        </Button>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h6">{room.name}</Typography>
          <Typography variant="body2" color="text.secondary">
            {room.description}
          </Typography>
        </Box>
        <Chip label={room.type} color="primary" size="small" sx={{ mr: 1 }} />
        <Tooltip title="Logout">
          <IconButton onClick={handleLogoutClick} color="error">
            <ExitToApp />
          </IconButton>
        </Tooltip>
      </Paper>

      <Paper sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 2, overflow: 'hidden' }}>
        <Box sx={{ flexGrow: 1, overflow: 'auto', mb: 2 }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <List>
              {messages.map((message) => (
                <ListItem
                  key={message.id}
                  sx={{
                    flexDirection: 'column',
                    alignItems: message.type === 'user' ? 'flex-end' : 'flex-start',
                    py: 1,
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      maxWidth: '70%',
                      gap: 1,
                    }}
                  >
                    {message.type === 'ai' && (
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        <SmartToy />
                      </Avatar>
                    )}
                    {message.type === 'user' && (
                      <Avatar sx={{ bgcolor: 'secondary.main' }}>
                        <Person />
                      </Avatar>
                    )}
                    <Paper
                      sx={{
                        p: 2,
                        bgcolor: message.type === 'user' ? 'primary.main' : 'grey.100',
                        color: message.type === 'user' ? 'white' : 'text.primary',
                      }}
                    >
                      <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                        {message.username}
                      </Typography>
                      <Typography variant="body1">{message.message}</Typography>
                      <Typography variant="caption" sx={{ mt: 0.5, opacity: 0.7 }}>
                        {formatTime(message.created_at)}
                      </Typography>
                    </Paper>
                    {message.type === 'user' && (
                      <Avatar sx={{ bgcolor: 'secondary.main' }}>
                        <Person />
                      </Avatar>
                    )}
                  </Box>
                </ListItem>
              ))}
              <div ref={messagesEndRef} />
            </List>
          )}
        </Box>

        <Box component="form" onSubmit={handleSendMessage} sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            placeholder="Type your message..."
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            disabled={sending}
            variant="outlined"
          />
          <Button
            type="submit"
            variant="contained"
            disabled={sending || !newMessage.trim()}
            sx={{ minWidth: 'auto' }}
          >
            {sending ? <CircularProgress size={24} /> : <Send />}
          </Button>
        </Box>
      </Paper>
      
      <LogoutDialog
        open={logoutDialogOpen}
        onClose={() => setLogoutDialogOpen(false)}
        onConfirm={handleConfirmLogout}
      />
    </Container>
  );
};

export default ChatRoom;
