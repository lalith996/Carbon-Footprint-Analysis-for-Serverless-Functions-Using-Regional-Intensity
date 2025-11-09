import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

export const getStatus = async () => {
  const response = await axios.get(`${API_BASE_URL}/status`);
  return response.data;
};

export const getExperiment = async (id) => {
  const response = await axios.get(`${API_BASE_URL}/experiments/${id}`);
  return response.data;
};

export const calculateCarbon = async (data) => {
  const response = await axios.post(`${API_BASE_URL}/calculate`, data);
  return response.data;
};

export const getRegions = async () => {
  const response = await axios.get(`${API_BASE_URL}/regions`);
  return response.data;
};

export const getLiveMetrics = async () => {
  const response = await axios.get(`${API_BASE_URL}/metrics/live`);
  return response.data;
};
