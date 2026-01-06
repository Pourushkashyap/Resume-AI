import { useState } from 'react';
import Navbar from '../components/Navbar';
import ResumeForm from '../components/ResumeForm';
import ResultCard from '../components/ResultCard';
import { getSemanticMatch, getResumeQuality, getImprovementSuggestions, getMLScore } from '../services/api';
import { Sparkles, BarChart2, Target, Zap } from 'lucide-react';

const Dashboard = ({ user, onLogout }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [activeAnalysis, setActiveAnalysis] = useState(null);
  const [results, setResults] = useState({
    semantic: null,
    quality: null,
    improve: null,
    ml: null,
  });

  const handleAnalyze = async (type, resume, jobDescription) => {
    setIsLoading(true);
    setActiveAnalysis(type);
    
    // Clear previous result of this type
    setResults((prev) => ({ ...prev, [type]: null }));

    try {
      let response;
      
      switch (type) {
        case 'semantic':
          response = await getSemanticMatch(resume, jobDescription);
          break;
        case 'quality':
          response = await getResumeQuality(resume, jobDescription);
          break;
        case 'improve':
          response = await getImprovementSuggestions(resume, jobDescription);
          break;
        case 'ml':
          response = await getMLScore(resume, jobDescription);
          break;
        default:
          throw new Error('Unknown analysis type');
      }

      console.log(response)
      
      setResults((prev) => ({ ...prev, [type]: response }));
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'An error occurred';
      setResults((prev) => ({ 
        ...prev, 
        [type]: { error: errorMessage } 
      }));
    } finally {
      setIsLoading(false);
      setActiveAnalysis(null);
    }
  };

  const stats = [
    { icon: Target, label: 'Semantic Match', value: 'AI-Powered', color: 'text-primary' },
    { icon: BarChart2, label: 'Quality Score', value: 'ATS Check', color: 'text-info' },
    { icon: Sparkles, label: 'Improvements', value: 'Smart Tips', color: 'text-warning' },
    { icon: Zap, label: 'ML Score', value: 'Predictions', color: 'text-success' },
  ];

  const hasResults = Object.values(results).some((r) => r !== null);

  return (
    <div className="min-h-screen bg-background">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Resume Analyzer</h1>
          <p className="text-muted-foreground">
            Upload your resume and job description to get AI-powered insights
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {stats.map((stat, i) => (
            <div 
              key={i} 
              className="card-elevated p-4 flex items-center gap-3"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <div className={`p-2 rounded-lg bg-secondary ${stat.color}`}>
                <stat.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
                <p className="text-sm font-semibold text-foreground">{stat.value}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Form */}
          <div>
            <ResumeForm 
              onAnalyze={handleAnalyze} 
              isLoading={isLoading}
              activeAnalysis={activeAnalysis}
            />
          </div>

          {/* Right Column - Results */}
          <div className="space-y-6">
            {!hasResults && !isLoading && (
              <div className="card-elevated p-12 text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-4">
                  <Sparkles className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  Ready to Analyze
                </h3>
                <p className="text-muted-foreground max-w-sm mx-auto">
                  Upload your resume and paste a job description, then choose an analysis type to get started.
                </p>
              </div>
            )}

            {isLoading && activeAnalysis && (
              <ResultCard type={activeAnalysis} isLoading={true} />
            )}

            {/* Display results in order of most recent */}
            {['semantic', 'quality', 'improve', 'ml'].map((type) => {
              if (results[type] && !(isLoading && activeAnalysis === type)) {
                return (
                  <ResultCard 
                    key={type} 
                    type={type} 
                    data={results[type]} 
                  />
                );
              }
              return null;
            })}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-muted-foreground">
              © 2024 ResumeAI. AI-powered resume analysis.
            </p>
            <div className="flex items-center gap-6">
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Privacy
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Terms
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Help
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;
