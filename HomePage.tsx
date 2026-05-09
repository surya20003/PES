import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  Avatar,
} from '@mui/material';
import {
  Chat,
  SmartToy,
  Speed,
  Security,
  Groups,
  Timeline,
} from '@mui/icons-material';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  
  const features = [
    {
      icon: <SmartToy />,
      title: 'AI-Powered Chat',
      description: 'Intelligent responses powered by advanced AI technology',
      color: 'primary',
    },
    {
      icon: <Security />,
      title: 'Secure & Private',
      description: 'End-to-end encryption keeps your conversations safe',
      color: 'secondary',
    },
    {
      icon: <Speed />,
      title: 'Lightning Fast',
      description: 'Real-time messaging with minimal latency',
      color: 'success',
    },
    {
      icon: <Groups />,
      title: 'Multiple Rooms',
      description: 'Create and manage multiple chat rooms for different topics',
      color: 'info',
    },
  ];

  const stats = [
    { label: 'Active Users', value: '10K+', icon: <Groups /> },
    { label: 'Messages Sent', value: '1M+', icon: <Chat /> },
    { label: 'AI Responses', value: '500K+', icon: <SmartToy /> },
    { label: 'Uptime', value: '99.9%', icon: <Timeline /> },
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Hero Section */}
      <Paper
        sx={{
          p: 6,
          mb: 6,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          textAlign: 'center',
          borderRadius: 3,
        }}
      >
        <Avatar
          sx={{
            width: 80,
            height: 80,
            bgcolor: 'white',
            color: 'primary.main',
            mx: 'auto',
            mb: 3,
          }}
        >
          <SmartToy sx={{ fontSize: 40 }} />
        </Avatar>
        <Typography 
          variant="h2" 
          component="h1" 
          gutterBottom 
          sx={{ fontWeight: 'bold' }}
        >
          AI Chat App
        </Typography>
        <Typography variant="h5" gutterBottom sx={{ mb: 4, opacity: 0.9 }}>
          Experience the future of conversational AI
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          <Button 
            variant="contained" 
            size="large" 
            sx={{ bgcolor: 'white', color: 'primary.main' }}
            onClick={() => navigate('/rooms')}
          >
            Get Started
          </Button>
          <Button 
            variant="outlined" 
            size="large" 
            sx={{ borderColor: 'white', color: 'white' }}
            onClick={() => navigate('/rooms')}
          >
            Learn More
          </Button>
        </Box>
      </Paper>

      {/* Stats Section */}
      <Grid container spacing={3} sx={{ mb: 6 }}>
        {stats.map((stat, index) => (
          <Grid size={{ xs: 6, md: 3 }} key={index}>
            <Card sx={{ textAlign: 'center', py: 3 }}>
              <CardContent>
                <Avatar sx={{ bgcolor: 'primary.main', mx: 'auto', mb: 2 }}>
                  {stat.icon}
                </Avatar>
                <Typography variant="h4" component="div" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  {stat.value}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {stat.label}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Features Section */}
      <Typography variant="h4" component="h2" gutterBottom sx={{ textAlign: 'center', mb: 4 }}>
        Why Choose AI Chat App?
      </Typography>
      <Grid container spacing={4}>
        {features.map((feature, index) => (
          <Grid size={{ xs: 12, md: 6, lg: 3 }} key={index}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <Avatar
                  sx={{
                    width: 60,
                    height: 60,
                    bgcolor: `${feature.color}.main`,
                    mx: 'auto',
                    mb: 2,
                  }}
                >
                  {feature.icon}
                </Avatar>
                <Typography variant="h6" component="h3" gutterBottom sx={{ fontWeight: 'bold' }}>
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {feature.description}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* CTA Section */}
      <Paper sx={{ p: 6, mt: 6, textAlign: 'center', bgcolor: 'grey.50' }}>
        <Typography variant="h4" component="h2" gutterBottom>
          Ready to Get Started?
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Join thousands of users already experiencing the power of AI conversations
        </Typography>
        <Button 
            variant="contained" 
            size="large" 
            sx={{ px: 4 }}
            onClick={() => navigate('/rooms')}
          >
            Start Chatting Now
          </Button>
      </Paper>
    </Container>
  );
};

export default HomePage;
