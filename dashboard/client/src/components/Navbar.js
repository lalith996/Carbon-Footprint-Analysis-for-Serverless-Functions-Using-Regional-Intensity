import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { FaLeaf, FaBars, FaTimes } from 'react-icons/fa';
import { motion } from 'framer-motion';

const Nav = styled(motion.nav)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 70px;
  background: rgba(26, 32, 44, 0.95);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2rem;
  z-index: 1000;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const Logo = styled(Link)`
  display: flex;
  align-items: center;
  text-decoration: none;
  color: #10b981;
  font-size: 1.5rem;
  font-weight: bold;
  gap: 0.5rem;

  &:hover {
    color: #34d399;
  }
`;

const NavLinks = styled.div`
  display: flex;
  gap: 2rem;
  align-items: center;

  @media (max-width: 768px) {
    position: fixed;
    top: 70px;
    left: ${props => props.isOpen ? '0' : '-100%'};
    width: 100%;
    height: calc(100vh - 70px);
    background: rgba(26, 32, 44, 0.98);
    flex-direction: column;
    padding: 2rem;
    transition: left 0.3s ease;
    gap: 1rem;
  }
`;

const NavLink = styled(Link)`
  color: #e2e8f0;
  text-decoration: none;
  font-size: 1rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.3s;

  &:hover {
    background: rgba(102, 126, 234, 0.2);
    color: #667eea;
  }

  @media (max-width: 768px) {
    width: 100%;
    text-align: center;
  }
`;

const MenuButton = styled.button`
  display: none;
  background: none;
  border: none;
  color: #e2e8f0;
  font-size: 1.5rem;
  cursor: pointer;

  @media (max-width: 768px) {
    display: block;
  }
`;

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Logo to="/">
        <FaLeaf />
        GreenAI
      </Logo>

      <NavLinks isOpen={isOpen}>
        <NavLink to="/" onClick={() => setIsOpen(false)}>Dashboard</NavLink>
        <NavLink to="/experiments" onClick={() => setIsOpen(false)}>Experiments</NavLink>
        <NavLink to="/calculator" onClick={() => setIsOpen(false)}>Calculator</NavLink>
        <NavLink to="/regional-map" onClick={() => setIsOpen(false)}>Regional Map</NavLink>
        <NavLink to="/analytics" onClick={() => setIsOpen(false)}>Analytics</NavLink>
      </NavLinks>

      <MenuButton onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? <FaTimes /> : <FaBars />}
      </MenuButton>
    </Nav>
  );
};

export default Navbar;
