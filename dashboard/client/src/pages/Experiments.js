import React from 'react';
import styled from 'styled-components';

const Container = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  color: white;
  text-align: center;
`;

const Experiments = () => {
  return (
    <Container>
      <h1>🔬 Experiments</h1>
      <p>Explore all 4 completed experiments with interactive visualizations.</p>
      <p>Coming soon: EXP-001, EXP-002, EXP-003, EXP-004 detailed views</p>
    </Container>
  );
};

export default Experiments;
