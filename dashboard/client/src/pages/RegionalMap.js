import React from 'react';
import styled from 'styled-components';

const Container = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  color: white;
  text-align: center;
`;

const RegionalMap = () => {
  return (
    <Container>
      <h1>🗺️ Regional Map</h1>
      <p>Interactive map showing carbon intensity across Indian regions.</p>
      <p>Coming soon: Leaflet-based map with regional markers</p>
    </Container>
  );
};

export default RegionalMap;
