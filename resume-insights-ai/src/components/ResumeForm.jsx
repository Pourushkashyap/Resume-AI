import { useState, useRef } from 'react';
import { Upload, FileText, X, AlertCircle, Loader2 } from 'lucide-react';

const ResumeForm = ({ onAnalyze, isLoading, activeAnalysis }) => {
  const [resume, setResume] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateFile = (file) => {
    if (!file) return false;
    if (file.type !== 'application/pdf') {
      setError('Please upload a PDF file only');
      return false;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return false;
    }
    setError('');
    return true;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const file = e.dataTransfer.files?.[0];
    if (validateFile(file)) {
      setResume(file);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (validateFile(file)) {
      setResume(file);
    }
  };

  const removeFile = () => {
    setResume(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleAnalyze = (type) => {
    if (!resume) {
      setError('Please upload a resume');
      return;
    }
    if (!jobDescription.trim()) {
      setError('Please enter a job description');
      return;
    }
    setError('');
    onAnalyze(type, resume, jobDescription);
  };

  const analysisButtons = [
    { type: 'semantic', label: 'Semantic Match', icon: '🎯', description: 'Match resume to job requirements' },
    { type: 'quality', label: 'Resume Quality', icon: '📊', description: 'Check ATS compatibility score' },
    { type: 'improve', label: 'Improve Resume', icon: '✨', description: 'Get improvement suggestions' },
    { type: 'ml', label: 'ML Score', icon: '🤖', description: 'AI-powered resume scoring' },
  ];

  return (
    <div className="space-y-6">
      {/* Resume Upload Section */}
      <div className="card-elevated p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          Upload Resume
        </h3>
        
        <div
          className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
            dragActive
              ? 'border-primary bg-primary/5'
              : resume
              ? 'border-success bg-success/5'
              : 'border-border hover:border-primary/50 hover:bg-secondary/50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          
          {resume ? (
            <div className="flex items-center justify-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-success/10">
                <FileText className="h-6 w-6 text-success" />
              </div>
              <div className="text-left">
                <p className="font-medium text-foreground">{resume.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(resume.size / 1024).toFixed(1)} KB
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  removeFile();
                }}
                className="ml-4 p-2 rounded-lg hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex justify-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
                  <Upload className="h-7 w-7 text-primary" />
                </div>
              </div>
              <div>
                <p className="font-medium text-foreground">
                  Drop your resume here or <span className="text-primary">browse</span>
                </p>
                <p className="text-sm text-muted-foreground mt-1">PDF files only, max 10MB</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Job Description Section */}
      <div className="card-elevated p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <span className="text-xl">📋</span>
          Job Description
        </h3>
        <textarea
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste the job description here..."
          className="input-field min-h-[200px] resize-y"
        />
        <p className="text-xs text-muted-foreground mt-2">
          {jobDescription.length} characters
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 p-4 rounded-lg bg-destructive/10 border border-destructive/20">
          <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0" />
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Analysis Buttons */}
      <div className="card-elevated p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Choose Analysis Type</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {analysisButtons.map((btn) => (
            <button
              key={btn.type}
              onClick={() => handleAnalyze(btn.type)}
              disabled={isLoading}
              className={`group relative flex items-center gap-4 p-4 rounded-xl border transition-all duration-200 ${
                isLoading && activeAnalysis === btn.type
                  ? 'bg-primary/10 border-primary'
                  : 'bg-card border-border hover:border-primary hover:shadow-md'
              } disabled:opacity-60 disabled:cursor-not-allowed`}
            >
              <span className="text-2xl">{btn.icon}</span>
              <div className="text-left flex-1">
                <p className="font-semibold text-foreground group-hover:text-primary transition-colors">
                  {btn.label}
                </p>
                <p className="text-xs text-muted-foreground">{btn.description}</p>
              </div>
              {isLoading && activeAnalysis === btn.type && (
                <Loader2 className="h-5 w-5 text-primary animate-spin" />
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ResumeForm;
