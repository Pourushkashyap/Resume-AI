import axios from 'axios';

// Base API URL
const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds timeout
});

/* =====================================================
   🔐 REQUEST INTERCEPTOR (AUTO TOKEN ATTACH)
===================================================== */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/* =====================================================
   🔴 RESPONSE INTERCEPTOR (OPTIONAL)
   Auto logout on 401 (token expired / invalid)
===================================================== */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("currentUser");
      window.location.href = "/"; // back to login
    }
    return Promise.reject(error);
  }
);

/* =====================================================
   🧠 SEMANTIC MATCH
===================================================== */
export const getSemanticMatch = async (resume, jobDescription) => {
  const formData = new FormData();
  formData.append('resume', resume);
  formData.append('job_description', jobDescription);

  const response = await api.post(
    '/semantic/full-gap-analysis',
    formData
  );
  return response.data;
};

/* =====================================================
   📊 RESUME QUALITY SCORE
===================================================== */
export const getResumeQuality = async (resume) => {
  const formData = new FormData();
  formData.append('resume', resume);

  const response = await api.post(
    '/quality/score',
    formData
  );
  return response.data;
};

/* =====================================================
   ✨ IMPROVEMENT SUGGESTIONS
===================================================== */
export const getImprovementSuggestions = async (resume, jobDescription) => {
  const formData = new FormData();
  formData.append('resume', resume);
  formData.append('job_description', jobDescription);

  const response = await api.post(
    '/improvement/suggestions',
    formData
  );
  return response.data;
};

/* =====================================================
   🤖 ML SCORE
===================================================== */
export const getMLScore = async (resume) => {
  const formData = new FormData();
  formData.append('resume', resume);

  const response = await api.post(
    '/ml-score/predict',
    formData
  );
  return response.data;
};

export default api;
