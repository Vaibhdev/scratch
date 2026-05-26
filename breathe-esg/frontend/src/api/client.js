import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// ── Clients ──
export const getClients = () => api.get('/clients/');
export const createClient = (data) => api.post('/clients/', data);

// ── Ingestion ──
export const uploadFile = (formData) =>
  api.post('/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
export const getIngestions = (params) => api.get('/ingestions/', { params });
export const getIngestion = (id) => api.get(`/ingestions/${id}/`);

// ── Records ──
export const getRecords = (params) => api.get('/records/', { params });
export const getRecord = (id) => api.get(`/records/${id}/`);
export const reviewRecord = (id, data) => api.patch(`/records/${id}/review/`, data);
export const bulkReview = (data) => api.post('/records/bulk-action/', data);
export const getRecordSummary = (params) => api.get('/records/summary/', { params });

export default api;
