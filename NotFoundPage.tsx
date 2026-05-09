import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
} from '@mui/material';
import { Home, ArrowBack } from '@mui/icons-material';

interface NotFoundPageProps {
  onBack?: () => void;
}

const NotFoundPage: React.FC<NotFoundPageProps> = ({ onBack }) => {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/');
  };

  const handleGoBack = () => {
    if (onBack) {
      onBack();
    } else {
      window.history.back();
    }
  };

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Paper sx={{ p: 6, textAlign: 'center', maxWidth: 500 }}>
          <Typography variant="h1" component="h1" color="primary.main" sx={{ fontSize: '6rem', fontWeight: 'bold' }}>
            404
          </Typography>
          <Typography variant="h4" component="h2" gutterBottom>
            Page Not Found
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            The page you're looking for doesn't exist or has been moved.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              startIcon={<Home />}
              onClick={handleGoHome}
            >
              Go Home
            </Button>
            <Button
              variant="outlined"
              startIcon={<ArrowBack />}
              onClick={handleGoBack}
            >
              Go Back
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default NotFoundPage;
