const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api';

async function request(path, options = {}) {
  const token = localStorage.getItem('career_token');
  const isForm = options.body instanceof FormData;
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, { headers: { ...(isForm ? {} : { 'Content-Type': 'application/json' }), ...(token ? { Authorization: `Bearer ${token}` } : {}) }, ...options });
  } catch {
    throw new Error('Unable to reach the career server. Make sure Flask is running on 127.0.0.1:5000.');
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || 'Something went wrong.');
  return data;
}

export const auth = {
  login: (payload) => request('/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  register: (payload) => request('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  google: (credential) => request('/auth/google', { method: 'POST', body: JSON.stringify({ credential }) }),
  forgotPassword: (email) => request('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) }),
  resetPassword: (token, password) => request('/auth/reset-password', { method: 'POST', body: JSON.stringify({ token, password }) }),
  dashboard: () => request('/dashboard'),
  saveProfile: (payload) => request('/profile', { method: 'POST', body: JSON.stringify(payload) }),
};

export const api = {
  resume: (file) => { const body = new FormData(); body.append('resume', file); return request('/resume/analyze', { method: 'POST', body }); },
  atsAnalyze: (file, description, role = '') => { const body = new FormData(); body.append('resume', file); body.append('description', description); body.append('role', role); return request('/ats/analyze', { method: 'POST', body }); },
  ats: (resumeId, role, description) => request('/ats/analyze', { method: 'POST', body: JSON.stringify({ resume_id: resumeId, role, description }) }),
  jobs: (skills, targetRole) => request('/jobs/match', { method: 'POST', body: JSON.stringify({ skills, target_role: targetRole }) }),
  questions: (role, skills, jobDescription, interviewType = 'Mixed', difficulty = 'Medium') => request('/interview/questions', { method: 'POST', body: JSON.stringify({ role, skills, job_description: jobDescription, interview_type: interviewType, difficulty }) }),
  evaluate: (role, question, answer, interviewType = 'Mixed') => request('/interview/evaluate', { method: 'POST', body: JSON.stringify({ role, question, answer, interview_type: interviewType }) }),
  interviewHistory: () => request('/interview/history'),
  roadmap: (skills, targetRole) => request('/roadmap', { method: 'POST', body: JSON.stringify({ skills, target_role: targetRole }) }),
  careerRoadmap: () => request('/career-roadmap'),
  generateCareerRoadmap: (payload) => request('/career-roadmap', { method: 'POST', body: JSON.stringify(payload) }),
  updateCareerRoadmap: () => request('/career-roadmap/update', { method: 'POST' }),
  completeRoadmapTask: (taskId, completed) => request(`/career-roadmap/tasks/${taskId}`, { method: 'PATCH', body: JSON.stringify({ completed }) }),
  skillGaps: () => request('/skill-gaps'),
  updateSkillPlanTask: (taskId, completed) => request(`/skill-gaps/tasks/${taskId}`, { method: 'PATCH', body: JSON.stringify({ completed }) }),
  careerReadiness: () => request('/career-readiness'),
  applications: (query = '') => request(`/applications${query ? `?${query}` : ''}`),
  application: (id) => request(`/applications/${id}`),
  createApplication: (payload) => request('/applications', { method: 'POST', body: JSON.stringify(payload) }),
  updateApplication: (id, payload) => request(`/applications/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteApplication: (id) => request(`/applications/${id}`, { method: 'DELETE' }),
  gdTopics: () => request('/gd/topics'),
  randomGdTopic: () => request('/gd/topics/random'),
  evaluateGd: (payload) => request('/gd/evaluate', { method: 'POST', body: JSON.stringify(payload) }),
  improveResumeBullet: (bullet) => request('/resume/improve-bullet', { method: 'POST', body: JSON.stringify({ bullet }) }),
  analyzeJobDescription: (description) => request('/jobs/analyze-description', { method: 'POST', body: JSON.stringify({ description }) }),
};
