import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Avatar,
} from '@mui/material';
import { Logout as LogoutIcon } from '@mui/icons-material';

interface LogoutDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  username?: string;
}

const LogoutDialog: React.FC<LogoutDialogProps> = ({
  open,
  onClose,
  onConfirm,
  username,
}) => {
  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <LogoutIcon color="error" />
          Confirm Logout
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ textAlign: 'center', py: 2 }}>
          <Avatar sx={{ bgcolor: 'secondary.main', mx: 'auto', mb: 2, width: 56, height: 56 }}>
            {username?.charAt(0).toUpperCase()}
          </Avatar>
          <Typography variant="h6" gutterBottom>
            Are you sure you want to logout?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {username && `Logged in as: ${username}`}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            You will need to login again to access your account.
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: 3 }}>
        <Button onClick={onClose} variant="outlined" sx={{ mr: 1 }}>
          Cancel
        </Button>
        <Button 
          onClick={handleConfirm} 
          variant="contained" 
          color="error"
          startIcon={<LogoutIcon />}
        >
          Logout
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default LogoutDialog;
