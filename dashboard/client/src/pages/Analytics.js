import React from 'styled-components';
import styled from 'styled-components';

const Container = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  color: white;
  text-align: center;
`;

const Analytics = () => {
  return (
    <Container>
      <h1>📈 Analytics</h1>
      <p>Advanced analytics and statistical visualizations of experiment results.</p>
      <p>Coming soon: Historical trends, performance metrics, export capabilities</p>
    </Container>
  );
};

export default Analytics;
