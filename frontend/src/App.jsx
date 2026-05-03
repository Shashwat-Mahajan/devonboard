import { useState, useRef, useEffect } from 'react';
import './App.css';
import MarkdownRenderer from './MarkdownRenderer';

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [markdown, setMarkdown] = useState('');
  const [error, setError] = useState('');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [askLoading, setAskLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check health endpoint on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('http://localhost:8000/health');
        if (response.ok) {
          setIsConnected(true);
        } else {
          setIsConnected(false);
        }
      } catch (err) {
        setIsConnected(false);
      }
    };
    
    checkHealth();
  }, []);

  const validateGitHubUrl = (url) => {
    const githubPattern = /^https?:\/\/(www\.)?github\.com\/[\w-]+\/[\w.-]+\/?$/;
    return githubPattern.test(url.trim());
  };

  const handleAnalyze = async () => {
    const trimmedUrl = url.trim();
    
    if (!trimmedUrl) {
      setError('Please enter a GitHub repository URL');
      return;
    }

    if (!validateGitHubUrl(trimmedUrl)) {
      setError('Please enter a valid GitHub repository URL (e.g., https://github.com/username/repo)');
      return;
    }

    setLoading(true);
    setError('');
    setMarkdown('');
    setMessages([]); // Clear messages when analyzing new repo

    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ github_url: trimmedUrl }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }

      const data = await response.json();
      setMarkdown(data.onboarding_doc || 'No documentation generated');
    } catch (err) {
      setError(err.message || 'Failed to analyze repository. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleAnalyze();
    }
  };

  const handleAskQuestion = async (questionText = null) => {
    const trimmedQuestion = (questionText || question).trim();
    
    if (!trimmedQuestion) {
      return;
    }

    if (!markdown) {
      return;
    }

    // Add user question to messages
    const userMessage = {
      type: 'question',
      content: trimmedQuestion,
      timestamp: Date.now()
    };
    setMessages(prev => [...prev, userMessage]);
    setQuestion('');
    setAskLoading(true);

    try {
      const response = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: trimmedQuestion,
          context: markdown
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }

      const data = await response.json();
      
      // Add AI answer to messages
      const answerMessage = {
        type: 'answer',
        content: data.answer || 'No answer generated',
        sources: data.sources || [],
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, answerMessage]);
    } catch (err) {
      // Add error message
      const errorMessage = {
        type: 'answer',
        content: err.message || 'Failed to get answer. Please try again.',
        isError: true,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setAskLoading(false);
    }
  };

  const handleQuestionKeyPress = (e) => {
    if (e.key === 'Enter' && !askLoading && question.trim()) {
      handleAskQuestion();
    }
  };

  const handleSuggestedQuestion = (suggestedQuestion) => {
    handleAskQuestion(suggestedQuestion);
  };

  const suggestedQuestions = [
    "Where is authentication handled?",
    "What API endpoints exist?",
    "What database is used?",
    "How do I add a new feature?"
  ];

  return (
    <div className="app">
      {/* Health Status Bar */}
      <div className="health-status-bar">
        {isConnected ? (
          <span>✅ IBM watsonx.ai connected  |  🤖 meta-llama/llama-3-3-70b-instruct  |  ⚡ IBM Bob Built</span>
        ) : (
          <span>⚠️ Running in offline mode</span>
        )}
      </div>

      {/* Status Banner */}
      {!markdown && (
        <div className="status-banner">
          <div className="banner-content">
            <h1>GitHub Repository Analyzer</h1>
            <p className="subtitle">Generate onboarding documentation for any GitHub repository</p>
            
            <div className="input-section">
              <input
                type="text"
                className="url-input"
                placeholder="https://github.com/username/repository"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={loading}
              />
              <button
                className="analyze-button"
                onClick={handleAnalyze}
                disabled={loading}
              >
                {loading ? 'Analyzing...' : 'Analyze Repo'}
              </button>
            </div>

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}

            {loading && (
              <div className="loading-container">
                <div className="spinner"></div>
                <p>Analyzing repository...</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Two Column Layout */}
      {markdown && !loading && (
        <>
          {/* Top Status Banner */}
          <div className="top-status-banner">
            <div className="banner-content-inline">
              <div className="status-info">
                <span className="status-icon">✓</span>
                <span>Repository analyzed successfully</span>
              </div>
              <button className="new-analysis-btn" onClick={() => { setMarkdown(''); setMessages([]); setUrl(''); }}>
                New Analysis
              </button>
            </div>
          </div>

          <div className="two-column-layout">
            {/* Left Column - Document */}
            <div className="document-panel">
              <MarkdownRenderer content={markdown} />
            </div>

            {/* Right Column - Q&A Panel */}
            <div className="qna-panel">
              {/* Header */}
              <div className="qna-header">
                <div className="qna-title">Ask about this repo</div>
                <div className="qna-subtitle">Powered by IBM watsonx.ai</div>
              </div>

              {/* Messages Area */}
              <div className="qna-messages">
                {messages.length === 0 && !askLoading && (
                  <div className="empty-state">
                    <p className="empty-state-text">Ask a question to get started</p>
                    <div className="suggested-questions">
                      {suggestedQuestions.map((q, idx) => (
                        <button
                          key={idx}
                          className="suggested-question-chip"
                          onClick={() => handleSuggestedQuestion(q)}
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {messages.map((msg, idx) => (
                  <div key={idx}>
                    {msg.type === 'question' && (
                      <div className="message-bubble question-bubble">
                        {msg.content}
                      </div>
                    )}
                    {msg.type === 'answer' && (
                      <div className="message-bubble answer-bubble">
                        <div className="watsonx-badge">IBM watsonx.ai</div>
                        <div className="answer-text">{msg.content}</div>
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="sources">
                            <span className="sources-label">Sources:</span>
                            {msg.sources.map((source, i) => (
                              <span key={i} className="source-item">{source}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}

                {askLoading && (
                  <div className="message-bubble answer-bubble loading-bubble">
                    <div className="watsonx-badge">IBM watsonx.ai</div>
                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="qna-input-area">
                <input
                  type="text"
                  className="qna-input"
                  placeholder="Ask a question..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyPress={handleQuestionKeyPress}
                  disabled={askLoading}
                />
                <button
                  className="qna-ask-button"
                  onClick={() => handleAskQuestion()}
                  disabled={askLoading || !question.trim()}
                >
                  Ask
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default App;

// Made with Bob
