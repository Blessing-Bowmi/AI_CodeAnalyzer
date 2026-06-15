import axios from 'axios';

const API = axios.create({ baseURL: '/api' });

// Attach JWT token to requests
API.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

// Auth
export const register = (data) => API.post('/auth/register', data);
export const login = (data) => API.post('/auth/login', data);
export const getMe = () => API.get('/auth/me');

// Projects
export const getProjects = () => API.get('/projects/');
export const getProject = (id) => API.get(`/projects/${id}`);
export const deleteProject = (id) => API.delete(`/projects/${id}`);
export const uploadProject = (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return API.post('/projects/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
};

// Analysis
export const analyzeProject = (id) => API.post(`/projects/${id}/analyze`);
export const getEntities = (id) => API.get(`/projects/${id}/entities`);

// Dependencies
export const getDependencies = (id) => API.get(`/projects/${id}/dependencies`);
export const getDependencyGraph = (id) => API.get(`/projects/${id}/dependencies/graph`);
export const getCircular = (id) => API.get(`/projects/${id}/circular`);

// Smells
export const getSmells = (id) => API.get(`/projects/${id}/smells`);
export const getDuplicates = (id) => API.get(`/projects/${id}/duplicates`);

// Refactoring
export const getRefactorings = (id) => API.get(`/projects/${id}/refactorings`);
export const applyRefactor = (pid, rid) => API.post(`/projects/${pid}/refactor/${rid}/apply`);
export const rejectRefactor = (pid, rid) => API.post(`/projects/${pid}/refactor/${rid}/reject`);
export const getPreview = (pid, rid) => API.get(`/projects/${pid}/refactor/${rid}/preview`);
export const getAllPreviews = (id) => API.get(`/projects/${id}/previews`);

// Risk
export const getRisk = (id) => API.get(`/projects/${id}/risk`);

// AI
export const getRecommendations = (id) => API.get(`/projects/${id}/recommendations`);
export const getMaintainability = (id) => API.get(`/projects/${id}/maintainability`);

// Learning
export const getLearningStats = () => API.get('/projects/learning/stats');

// Reports
export const getJsonReport = (id) => API.get(`/projects/${id}/report/json`);
export const getPdfReport = (id) => API.get(`/projects/${id}/report/pdf`, { responseType: 'blob' });

// Review Comments
export const getReviewComments = (id) => API.get(`/projects/${id}/comments`);
export const addReviewComment = (id, comment) => API.post(`/projects/${id}/comments`, { comment });

// Profile
export const updateProfile = (data) => API.put('/auth/profile', data);
export const changePassword = (data) => API.put('/auth/password', data);

// Admin
export const getAdminDashboard = () => API.get('/admin/dashboard');
export const getAdminUsers = () => API.get('/admin/users');
export const getAdminUserDetail = (id) => API.get(`/admin/users/${id}`);
export const updateUserRole = (id, role) => API.put(`/admin/users/${id}/role`, { role });
export const deleteUser = (id) => API.delete(`/admin/users/${id}`);
export const getAdminProjects = () => API.get('/admin/projects');
export const adminDeleteProject = (pid) => API.delete(`/admin/projects/${pid}`);
export const getSystemAnalytics = () => API.get('/admin/analytics');
export const getAdminActivity = () => API.get('/admin/activity');

export default API;
