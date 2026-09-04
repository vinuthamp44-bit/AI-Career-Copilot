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
  dashboard: () => request('/dashboard'),
};

export const api = {
  resume: (file) => { const body = new FormData(); body.append('resume', file); return request('/resume/analyze', { method: 'POST', body }); },
  atsAnalyze: (file, description, role = '') => { const body = new FormData(); body.append('resume', file); body.append('description', description); body.append('role', role); return request('/ats/analyze', { method: 'POST', body }); },
  ats: (resumeId, role, description) => request('/ats/analyze', { method: 'POST', body: JSON.stringify({ resume_id: resumeId, role, description }) }),
  jobs: (skills, targetRole) => request('/jobs/match', { method: 'POST', body: JSON.stringify({ skills, target_role: targetRole }) }),
  questions: (role, skills, jobDescription) => request('/interview/questions', { method: 'POST', body: JSON.stringify({ role, skills, job_description: jobDescription }) }),
  evaluate: (role, question, answer) => request('/interview/evaluate', { method: 'POST', body: JSON.stringify({ role, question, answer }) }),
  roadmap: (skills, targetRole) => request('/roadmap', { method: 'POST', body: JSON.stringify({ skills, target_role: targetRole }) }),
};
