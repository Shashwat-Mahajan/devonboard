# DevOnboard 🚀

> AI-powered developer onboarding for any GitHub repository in under 60 seconds

[![IBM Bob Hackathon](https://img.shields.io/badge/IBM_Bob-Hackathon_2026-blue)](https://ibm.com)
[![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-purple)](https://www.ibm.com/watsonx)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue)](https://react.dev)

## Overview

**DevOnboard** revolutionizes developer onboarding by automatically analyzing GitHub repositories and generating comprehensive onboarding documentation powered by **IBM watsonx.ai**. Built entirely with **IBM Bob**, it transforms days of manual exploration into minutes of AI-guided understanding.

### What It Does

Simply provide a GitHub repository URL, and DevOnboard will:

1. 📊 **Analyze the repository structure** - Understand the project layout and organization
2. 🎯 **Identify the top 10 most important files** - Know where to focus your attention
3. 🔄 **Map the data flow** - Understand how information moves through the system
4. 📝 **Generate a step-by-step feature guide** - Learn how to add new features
5. 🤖 **AI Insights powered by watsonx.ai** - Get intelligent observations using Llama 70B
6. 💬 **Interactive Q&A** - Ask follow-up questions and get AI-powered answers

### Perfect For

- 🆕 New team members joining a project
- 🔍 Developers exploring open-source projects
- 📚 Creating documentation for existing codebases
- 🎓 Learning from well-structured projects
- 🏆 Hackathon teams understanding starter code

## Features

### Current Features (v1.0 - Hackathon Demo)

- ✅ GitHub repository analysis via REST API
- ✅ Intelligent file importance scoring
- ✅ Architecture pattern detection
- ✅ Data flow visualization
- ✅ Feature addition guide generation
- ✅ **AI Insights powered by IBM watsonx.ai (Llama 70B)**
- ✅ **Interactive Q&A with AI-powered answers**
- ✅ Clean, responsive React UI
- ✅ Support for multiple programming languages
- ✅ Comprehensive error handling and validation
- ✅ **62 comprehensive unit tests**
- ✅ **Built entirely with IBM Bob**

### Coming Soon (Post-Hackathon)

- 📊 Interactive dependency graph visualization
- 🔒 Security vulnerability scanning
- 📈 Code quality metrics and recommendations
- 💾 Save and share analysis results
- 🔄 Compare repository versions
- 👥 Team collaboration features
- 🔌 IDE extensions (VS Code, JetBrains)

## Tech Stack

### Core Technologies
- **IBM Bob**: Complete development environment (Plan + Code modes)
- **IBM watsonx.ai**: AI inference using meta-llama/llama-3-3-70b-instruct
- **GitHub REST API**: Repository data fetching

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **API Client**: httpx for async GitHub API calls
- **Validation**: Pydantic for data models
- **Server**: Uvicorn ASGI server
- **Testing**: pytest with 62 comprehensive tests

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Plain CSS (minimal, clean design)
- **Markdown**: Custom markdown renderer

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- GitHub personal access token ([Create one here](https://github.com/settings/tokens))
- IBM watsonx.ai API credentials ([Get started here](https://www.ibm.com/watsonx))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/devonboard.git
   cd devonboard
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   
   pip install -r requirements.txt
   
   # Create .env file with your credentials
   echo GITHUB_TOKEN=your_github_token_here > .env
   echo WATSONX_API_KEY=your_watsonx_api_key_here >> .env
   echo WATSONX_PROJECT_ID=your_project_id_here >> .env
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   
   # Create .env file
   cp .env.example .env
   # Edit .env if needed
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   Backend will be available at: `http://localhost:8000`
   
   API documentation: `http://localhost:8000/docs`

2. **Start the frontend development server**
   ```bash
   cd frontend
   npm run dev
   ```
   
   Frontend will be available at: `http://localhost:5173`

3. **Open your browser**
   
   Navigate to `http://localhost:5173` and start analyzing repositories!

## Usage

### Basic Usage

1. Open the application in your browser at `http://localhost:5173`
2. Enter a GitHub repository URL (e.g., `https://github.com/fastapi/fastapi`)
3. Click "Analyze Repository"
4. View the generated onboarding document with AI insights
5. Ask follow-up questions using the interactive Q&A feature

### GitHub Token Setup

To use DevOnboard, you need a GitHub personal access token:

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "DevOnboard")
4. Select scopes:
   - `repo` (for private repositories)
   - `public_repo` (for public repositories only)
5. Click "Generate token"
6. Copy the token and use it in the application

**Security Note**: Your GitHub token is stored in the backend `.env` file and used for API requests. Never commit your `.env` file to version control.

### IBM watsonx.ai Setup

1. Sign up for IBM watsonx.ai at [ibm.com/watsonx](https://www.ibm.com/watsonx)
2. Create a new project and note your Project ID
3. Generate an API key from your account settings
4. Add credentials to backend `.env` file:
   ```
   WATSONX_API_KEY=your_api_key_here
   WATSONX_PROJECT_ID=your_project_id_here
   ```

## Project Structure

```
devonboard/
├── backend/                    # FastAPI backend
│   ├── main.py                # Application entry point
│   ├── github_client.py       # GitHub API integration
│   ├── doc_generator.py       # Documentation generation
│   ├── watsonx_client.py      # IBM watsonx.ai integration
│   ├── orchestrate_agent.py   # Analysis orchestration
│   ├── test_watson.py         # watsonx.ai testing
│   ├── tests/                 # 62 comprehensive unit tests
│   │   ├── test_doc_generator.py
│   │   └── test_github_client.py
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── App.jsx            # Main application (98 lines)
│   │   ├── MarkdownRenderer.jsx  # Markdown rendering (54 lines)
│   │   ├── App.css            # Styling
│   │   └── main.jsx           # Entry point
│   └── package.json           # Node dependencies
│
├── docs/                       # Comprehensive documentation
│   ├── IMPLEMENTATION_PLAN.md # Detailed implementation guide
│   ├── ARCHITECTURE_PLAN.md   # System architecture
│   ├── PLANNING_SUMMARY.md    # Planning phase summary
│   ├── QUICK_START_GUIDE.md   # Quick start guide
│   ├── EDGE_CASES_FIXED.md    # Edge cases documentation
│   └── FILE_STRUCTURE_CHECKLIST.md
│
├── bob-sessions/               # IBM Bob development sessions
│   ├── bob_task_plan.md
│   ├── bob_task_backend-creation.md
│   ├── bob_task_IBM-watsonx.ai-Integration.md
│   ├── bob_task_frontend_development.md
│   └── ... (14+ detailed session logs)
│
├── README.md                   # This file
└── SUBMISSION.md               # Hackathon submission details
```

## API Documentation

### Endpoints

#### POST /analyze
Analyze a GitHub repository and generate onboarding documentation with AI insights.

**Request:**
```json
{
  "repo_url": "https://github.com/owner/repo"
}
```

**Response:**
```json
{
  "markdown": "# Repository Analysis\n\n## Architecture Summary\n...",
  "metadata": {
    "repo_name": "repo",
    "owner": "owner",
    "analyzed_at": "2026-05-03T11:30:00Z"
  }
}
```

#### POST /ask
Ask follow-up questions about the analyzed repository using AI.

**Request:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "question": "How does authentication work in this project?"
}
```

**Response:**
```json
{
  "answer": "Based on the repository analysis, authentication is implemented using...",
  "context_used": true
}
```

For complete API documentation, visit `http://localhost:8000/docs` when running the backend.

## How It Works

### File Importance Scoring

DevOnboard uses a sophisticated scoring algorithm to identify the most important files:

- **Location Score (0-30 points)**: Root-level files score higher
- **Name Pattern Score (0-25 points)**: Files with names like `main`, `app`, `index` score higher
- **File Type Score (0-20 points)**: Source code files score higher than config files
- **Size Score (0-15 points)**: Files with 100-1000 lines score highest
- **Special Files Score (0-10 points)**: README, package.json, etc. get bonus points

### Architecture Detection

The system detects common project patterns:

- FastAPI, Django, Flask (Python)
- React, Next.js, Vue (JavaScript/TypeScript)
- Express, NestJS (Node.js)
- Spring Boot (Java)
- And more...

### Data Flow Analysis

Identifies key components:
1. Entry points (main files)
2. Routers/Controllers (HTTP handlers)
3. Services (business logic)
4. Models (data structures)
5. Database/Storage layers
6. External API integrations

## Development

### Running Tests

**Backend (62 comprehensive tests):**
```bash
cd backend
pytest tests/ -v
```

**Test Coverage:**
- 31 tests for `doc_generator.py`
- 31 tests for `github_client.py`
- All tests passing ✅
- Mocked GitHub API calls (no real API usage)
- Comprehensive edge case coverage

### Code Style

**Backend:**
```bash
cd backend
black app/
flake8 app/
mypy app/
```

**Frontend:**
```bash
cd frontend
npm run lint
npm run format
```

### Building for Production

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run build
npm run preview
```

## Troubleshooting

### Common Issues

**Issue**: "GitHub API rate limit exceeded"
- **Solution**: Make sure you're using an authenticated token. Unauthenticated requests are limited to 60/hour, while authenticated requests get 5000/hour.

**Issue**: "Repository not found"
- **Solution**: Check that the repository URL is correct and that your token has access to it (for private repos).

**Issue**: "CORS error"
- **Solution**: Make sure the backend is running and the `CORS_ORIGINS` in backend `.env` includes your frontend URL.

**Issue**: "Analysis taking too long"
- **Solution**: Large repositories (>500 files) may take longer. Consider adjusting `max_files_to_analyze` in the request options.

## Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow the existing code style
- Write tests for new features
- Update documentation as needed
- Keep commits atomic and well-described

## Roadmap

### Version 1.0 (Current - Hackathon Demo)
- ✅ Core repository analysis
- ✅ File importance ranking
- ✅ Architecture detection
- ✅ Basic UI

### Version 2.0 (Post-Hackathon)
- 🤖 AI-powered analysis with GPT-4/Claude
- 💾 Save and share analysis results
- 📊 Dependency graph visualization
- 🔒 Security scanning

### Version 3.0 (Future)
- 👥 Team collaboration features
- 📈 Historical analysis
- 🔌 IDE extensions (VS Code, JetBrains)
- 🔄 CI/CD integration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Built entirely with IBM Bob** - Plan mode + Code mode
- **Powered by IBM watsonx.ai** - Llama 70B for AI insights
- **Created for IBM Bob Hackathon 2026**
- Backend: [FastAPI](https://fastapi.tiangolo.com/)
- Frontend: [React](https://react.dev/)
- Data source: [GitHub REST API](https://docs.github.com/en/rest)

## IBM Bob Development Journey

This entire project was built using IBM Bob across multiple development sessions:

1. **Planning Phase** - Architecture and implementation planning
2. **Backend Development** - FastAPI setup, GitHub integration, watsonx.ai integration
3. **Frontend Development** - React UI with minimal, clean design
4. **Testing** - Comprehensive pytest suite with 62 tests
5. **Documentation** - Complete documentation generation
6. **Refinement** - Edge case handling and performance optimization

See `bob-sessions/` directory for detailed session logs.

## Support

- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/devonboard/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/devonboard/discussions)
- 📖 Documentation: See `docs/` directory

---

**Made with ❤️ using IBM Bob and IBM watsonx.ai**

*Transforming developer onboarding from days to minutes.*

---

**See [SUBMISSION.md](SUBMISSION.md) for complete hackathon submission details.**