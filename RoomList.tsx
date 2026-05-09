import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Button,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Box,
  Chip,
  CircularProgress,
  IconButton,
  Avatar,
} from '@mui/material';
import { Add, Chat, ExitToApp } from '@mui/icons-material';
import { Room } from '../types';
import { chatAPI } from '../services/api';
import ChatRoom from './ChatRoom';
import LogoutDialog from './LogoutDialog';

interface RoomListProps {
  onLogout: () => void;
  username: string;
}

const RoomList: React.FC<RoomListProps> = ({ onLogout, username }) => {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false);
  const [newRoom, setNewRoom] = useState({ name: '', description: '', type: 'direct' });

  useEffect(() => {
    loadRooms();
  }, []);

  const loadRooms = async () => {
    try {
      setLoading(true);
      const response = await chatAPI.getRooms();
      setRooms(response.data.rooms);
    } catch (error) {
      console.error('Failed to load rooms:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRoom = async () => {
    try {
      await chatAPI.createRoom(newRoom);
      setCreateDialogOpen(false);
      setNewRoom({ name: '', description: '', type: 'direct' });
      loadRooms();
    } catch (error) {
      console.error('Failed to create room:', error);
    }
  };

  const handleLogoutClick = () => {
    setLogoutDialogOpen(true);
  };

  const handleConfirmLogout = () => {
    onLogout();
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString();
    }
  };

  if (selectedRoom) {
    return (
      <ChatRoom
        room={selectedRoom}
        onBack={() => setSelectedRoom(null)}
      />
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" component="h1">
            AI Chat App
          </Typography>
          <Button 
            onClick={handleLogoutClick} 
            variant="outlined"
            startIcon={<ExitToApp />}
            sx={{ minWidth: '120px' }}
          >
            Logout
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Welcome back! Select a room to start chatting or create a new one.
        </Typography>
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Your Rooms
        </Typography>
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : rooms.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Chat sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="body1" color="text.secondary" gutterBottom>
              No rooms yet
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Create your first room to start chatting!
            </Typography>
          </Box>
        ) : (
          <List>
            {rooms.map((room) => (
              <ListItem key={room.id} disablePadding>
                <ListItemButton
                  onClick={() => setSelectedRoom(room)}
                  sx={{
                    borderRadius: 1,
                    mb: 1,
                    border: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Box sx={{ flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                        {room.name}
                      </Typography>
                      <Chip
                        label={room.type}
                        size="small"
                        color="primary"
                        sx={{ ml: 1 }}
                      />
                    </Box>
                    {room.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {room.description}
                      </Typography>
                    )}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        {room.message_count || 0} messages
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {room.last_activity && formatTime(room.last_activity)}
                      </Typography>
                    </Box>
                  </Box>
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </Paper>

      <Fab
        color="primary"
        aria-label="add"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => setCreateDialogOpen(true)}
      >
        <Add />
      </Fab>

      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Room</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Room Name"
            fullWidth
            variant="outlined"
            value={newRoom.name}
            onChange={(e) => setNewRoom({ ...newRoom, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description (optional)"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={newRoom.description}
            onChange={(e) => setNewRoom({ ...newRoom, description: e.target.value })}
            sx={{ mb: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateRoom} variant="contained" disabled={!newRoom.name.trim()}>
            Create Room
          </Button>
        </DialogActions>
      </Dialog>
      
      <LogoutDialog
        open={logoutDialogOpen}
        onClose={() => setLogoutDialogOpen(false)}
        onConfirm={handleConfirmLogout}
        username={username}
      />
    </Container>
  );
};

export default RoomList;
