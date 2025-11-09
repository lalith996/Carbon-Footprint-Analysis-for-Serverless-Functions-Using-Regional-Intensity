import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { FaCheckCircle, FaTasks, FaClock, FaLeaf } from 'react-icons/fa';
import { getStatus, getLiveMetrics } from '../services/api';

const Container = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
`;

const Header = styled(motion.div)`
  text-align: center;
  margin-bottom: 3rem;
  color: white;
`;

const Title = styled.h1`
  font-size: 3rem;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #10b981, #34d399);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
`;

const Subtitle = styled.p`
  font-size: 1.2rem;
  color: #e2e8f0;
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
`;

const Card = styled(motion.div)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: transform 0.3s ease;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  }
`;

const CardIcon = styled.div`
  font-size: 2.5rem;
  color: ${props => props.color || '#10b981'};
  margin-bottom: 1rem;
`;

const CardTitle = styled.h3`
  color: white;
  font-size: 1.2rem;
  margin-bottom: 0.5rem;
`;

const CardValue = styled.div`
  font-size: 2.5rem;
  font-weight: bold;
  color: white;
  margin-bottom: 0.5rem;
`;

const CardSubtext = styled.p`
  color: #cbd5e0;
  font-size: 0.9rem;
`;

const StatusBadge = styled.span`
  display: inline-block;
  padding: 0.5rem 1rem;
  background: ${props => props.success ? '#10b981' : '#f59e0b'};
  color: white;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
`;

const Dashboard = () => {
  const [status, setStatus] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statusData = await getStatus();
        const metricsData = await getLiveMetrics();
        setStatus(statusData);
        setMetrics(metricsData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Container>
        <Header>
          <Title>Loading...</Title>
        </Header>
      </Container>
    );
  }

  return (
    <Container>
      <Header
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Title>🌱 GreenAI Carbon-Aware Dashboard</Title>
        <Subtitle>Real-time Serverless Scheduling Analytics</Subtitle>
        <div style={{ marginTop: '1rem' }}>
          <StatusBadge success={status?.experiments.completed === 4}>
            {status?.experiments.completed === 4 ? '✅ All Experiments Complete' : '⏳ In Progress'}
          </StatusBadge>
        </div>
      </Header>

      <Grid>
        <Card
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <CardIcon color="#10b981">
            <FaCheckCircle />
          </CardIcon>
          <CardTitle>Experiments Completed</CardTitle>
          <CardValue>{status?.experiments.completed}/{status?.experiments.total}</CardValue>
          <CardSubtext>{status?.experiments.percentage}% Complete</CardSubtext>
        </Card>

        <Card
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <CardIcon color="#3b82f6">
            <FaTasks />
          </CardIcon>
          <CardTitle>Total Tasks Executed</CardTitle>
          <CardValue>{status?.tasks.total.toLocaleString()}</CardValue>
          <CardSubtext>Runtime: {status?.tasks.runtime}s</CardSubtext>
        </Card>

        <Card
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          <CardIcon color="#f59e0b">
            <FaLeaf />
          </CardIcon>
          <CardTitle>CI Threshold</CardTitle>
          <CardValue>{status?.thresholds.ci}</CardValue>
          <CardSubtext>gCO₂/kWh crossover point</CardSubtext>
        </Card>

        <Card
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
        >
          <CardIcon color="#ef4444">
            <FaClock />
          </CardIcon>
          <CardTitle>Aging Threshold</CardTitle>
          <CardValue>{status?.thresholds.aging}%</CardValue>
          <CardSubtext>per year degradation</CardSubtext>
        </Card>
      </Grid>

      {metrics && (
        <Grid>
          <Card
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <CardTitle>Current Grid CI</CardTitle>
            <CardValue>{metrics.current_ci.toFixed(0)}</CardValue>
            <CardSubtext>gCO₂/kWh (live)</CardSubtext>
          </Card>

          <Card
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            <CardTitle>Active Tasks</CardTitle>
            <CardValue>{metrics.active_tasks}</CardValue>
            <CardSubtext>Currently running</CardSubtext>
          </Card>

          <Card
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
          >
            <CardTitle>Carbon Saved</CardTitle>
            <CardValue>{(metrics.carbon_saved / 1000).toFixed(1)}kg</CardValue>
            <CardSubtext>Total emissions reduced</CardSubtext>
          </Card>

          <Card
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
          >
            <CardTitle>System Efficiency</CardTitle>
            <CardValue>{metrics.efficiency.toFixed(1)}%</CardValue>
            <CardSubtext>Overall performance</CardSubtext>
          </Card>
        </Grid>
      )}
    </Container>
  );
};

export default Dashboard;
