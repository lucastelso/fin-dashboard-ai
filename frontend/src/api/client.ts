// frontend/src/api/client.ts
import axios from 'axios';

// Em produção, o frontend bate no faturamento relativo do Nginx. 
// Em desenvolvimento, aponta para o gateway local.
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api-financeira';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});