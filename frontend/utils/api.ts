import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getSubjects = () => api.get('/subjects');
export const getQuestions = (params: {
  subject: string;
  num_questions: number;
}) => api.get('/quiz/generate', { params });
export const getStats = () => api.get('/stats');