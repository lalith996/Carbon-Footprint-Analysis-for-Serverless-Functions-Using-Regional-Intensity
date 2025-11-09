import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import styled from 'styled-components';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Experiments from './pages/Experiments';
import Calculator from './pages/Calculator';
import RegionalMap from './pages/RegionalMap';
import Analytics from './pages/Analytics';
import './App.css';

const AppContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
`;

const Content = styled.div`
  padding-top: 70px;
  min-height: calc(100vh - 70px);
`;

function App() {
  return (
    <Router>
      <AppContainer>
        <Navbar />
        <Content>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/calculator" element={<Calculator />} />
            <Route path="/regional-map" element={<RegionalMap />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </Content>
      </AppContainer>
    </Router>
  );
}

export default App;
