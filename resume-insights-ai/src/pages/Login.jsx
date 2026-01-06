import { useState } from 'react';
import {
  FileText,
  Mail,
  Lock,
  User,
  ArrowRight,
  Sparkles,
  CheckCircle
} from 'lucide-react';

import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const Login = ({ onLogin }) => {
  const [isSignUp, setIsSignUp] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const features = [
    'AI-powered resume analysis',
    'ATS compatibility scoring',
    'Smart improvement suggestions',
    'Job description matching',
  ];

  const validateForm = () => {
    const newErrors = {};

    if (isSignUp && !formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setErrors({});

    try {
      if (isSignUp) {
        // 🔹 SIGNUP
        await axios.post(`${API_BASE_URL}/auth/signup`, {
          name: formData.name,
          email: formData.email,
          password: formData.password,
        });
      }

      // 🔹 LOGIN (after signup OR normal login)
      const res = await axios.post(`${API_BASE_URL}/auth/login`, {
        email: formData.email,
        password: formData.password,
      });

      // Save token & user
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem(
        'currentUser',
        JSON.stringify(res.data.user)
      );

      onLogin(res.data.user);
    } catch (err) {
      setErrors({
        password:
          err.response?.data?.detail ||
          'Invalid email or password',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary via-primary to-info p-12 flex-col justify-between">
        <div>
          <div className="flex items-center gap-3 mb-16">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-foreground/20 backdrop-blur">
              <FileText className="h-6 w-6 text-primary-foreground" />
            </div>
            <span className="text-2xl font-bold text-primary-foreground">
              ResumeAI
            </span>
          </div>

          <div className="space-y-6">
            <h1 className="text-4xl font-bold text-primary-foreground leading-tight">
              Land Your Dream Job with
              <span className="block mt-2">
                AI-Powered Resume Analysis
              </span>
            </h1>
            <p className="text-lg text-primary-foreground/80 max-w-md">
              Get instant feedback on your resume, match it with job
              descriptions, and stand out from the competition.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {features.map((feature, i) => (
            <div
              key={i}
              className="flex items-center gap-3 text-primary-foreground/90"
            >
              <CheckCircle className="h-5 w-5" />
              <span>{feature}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right Panel */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center lg:text-left">
            <h2 className="text-2xl font-bold text-foreground">
              {isSignUp ? 'Create your account' : 'Welcome back'}
            </h2>
            <p className="text-muted-foreground mt-2">
              {isSignUp
                ? 'Start analyzing your resume in minutes'
                : 'Sign in to continue to your dashboard'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {isSignUp && (
              <div>
                <label className="text-sm font-medium">Full Name</label>
                <input
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="input-field"
                />
                {errors.name && (
                  <p className="text-sm text-destructive">{errors.name}</p>
                )}
              </div>
            )}

            <div>
              <label className="text-sm font-medium">Email</label>
              <input
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="input-field"
              />
              {errors.email && (
                <p className="text-sm text-destructive">{errors.email}</p>
              )}
            </div>

            <div>
              <label className="text-sm font-medium">Password</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="input-field"
              />
              {errors.password && (
                <p className="text-sm text-destructive">{errors.password}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground"
            >
              {loading
                ? 'Please wait...'
                : isSignUp
                ? 'Create Account'
                : 'Sign In'}
              <ArrowRight className="h-5 w-5" />
            </button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            {isSignUp
              ? 'Already have an account?'
              : "Don't have an account?"}{' '}
            <button
              type="button"
              onClick={() => {
                setIsSignUp(!isSignUp);
                setErrors({});
              }}
              className="font-medium text-primary hover:underline"
            >
              {isSignUp ? 'Sign in' : 'Sign up'}
            </button>
          </p>

          <div className="flex items-center justify-center gap-2 p-4 rounded-xl bg-accent/50 border">
            <Sparkles className="h-5 w-5 text-primary" />
            <p className="text-sm">
              Authentication powered by FastAPI + JWT
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
