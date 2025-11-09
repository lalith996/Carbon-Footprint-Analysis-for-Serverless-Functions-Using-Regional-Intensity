import React, { useState } from 'react';
import styled from 'styled-components';
import { calculateCarbon } from '../services/api';

const Container = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  color: white;
`;

const Title = styled.h1`
  text-align: center;
  font-size: 2.5rem;
  margin-bottom: 2rem;
  background: linear-gradient(135deg, #10b981, #34d399);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
`;

const Calculator = () => {
  const [result, setResult] = useState(null);

  const handleCalculate = async () => {
    try {
      const data = await calculateCarbon({
        duration: 4,
        power: 100,
        ci: 607,
        serverAge: 2,
        agingRate: 7,
        strategies: ['operational_only', 'embodied_prioritized']
      });
      setResult(data);
    } catch (error) {
      console.error('Calculation error:', error);
    }
  };

  return (
    <Container>
      <Title>🔮 Carbon Calculator</Title>
      <div style={{ textAlign: 'center' }}>
        <button onClick={handleCalculate} style={{
          padding: '1rem 2rem',
          fontSize: '1.2rem',
          background: '#10b981',
          color: 'white',
          border: 'none',
          borderRadius: '10px',
          cursor: 'pointer'
        }}>
          Calculate Sample
        </button>
        {result && (
          <div style={{ marginTop: '2rem' }}>
            <pre style={{ background: 'rgba(255,255,255,0.1)', padding: '1rem', borderRadius: '10px' }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </Container>
  );
};

export default Calculator;
