# DevOnboard 🚀

> Automatically generate comprehensive developer onboarding documentation for any GitHub repository

[![IBM Hackathon](https://img.shields.io/badge/IBM-Hackathon-blue)](https://ibm.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue)](https://www.typescriptlang.org)

## Overview

**DevOnboard** helps developers quickly understand and onboard to new GitHub repositories by automatically analyzing the codebase and generating comprehensive onboarding documentation.

### What It Does

Simply provide a GitHub repository URL, and DevOnboard will:

1. 📊 **Analyze the repository structure** - Understand the project layout and organization
2. 🎯 **Identify the top 10 most important files** - Know where to focus your attention
3. 🔄 **Map the data flow** - Understand how information moves through the system
4. 📝 **Generate a step-by-step feature guide** - Learn how to add new features

### Perfect For

- 🆕 New team members joining a project
- 🔍 Developers exploring open-source projects
- 📚 Creating documentation for existing codebases
- 🎓 Learning from well-structured projects
- 🏆 Hackathon teams understanding starter code

## Features

### Current Features (v1.0)

- ✅ GitHub repository analysis via REST API
- ✅ Intelligent file importance scoring
- ✅ Architecture pattern detection
- ✅ Data flow visualization
- ✅ Feature addition guide generation
- ✅ Clean, responsive React UI
- ✅ Support for multiple programming languages
- ✅ Error handling and validation

### Coming Soon

- 🤖 AI-powered intelligent summaries (GPT-4/Claude integration)
- 📊 Dependency graph visualization
- 🔒 Security vulnerability scanning
- 📈 Code quality metrics
- 💾 Save and share analysis results
- 🔄 Compare repository versions

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **API Client**: httpx for async GitHub API calls
- **Validation**: Pydantic for data models
- **Server**: Uvicorn ASGI server

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Markdown**: react-markdown

### External APIs
- **GitHub REST API**: Repository data fetching

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- GitHub personal access token ([Create one here](https://github.com/settings/tokens))

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
   
   # Create .env file
   cp .env.example .env
   # Edit .env and add your configuration
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
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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

1. Open the application in your browser
2. Enter a GitHub repository URL (e.g., `https://github.com/fastapi/fastapi`)
3. Provide your GitHub personal access token
4. Click "Analyze Repository"
5. View the generated onboarding document

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

**Security Note**: Your token is never stored by DevOnboard. It's only used to make API requests to GitHub and is kept in memory during your session.

## Project Structure

```
devonboard/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # Application entry point
│   │   ├── config.py          # Configuration
│   │   ├── models/            # Pydantic models
│   │   ├── services/          # Business logic
│   │   ├── api/               # API routes
│   │   └── utils/             # Utility functions
│   ├── tests/                 # Backend tests
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API client
│   │   ├── types/             # TypeScript types
│   │   ├── hooks/             # Custom hooks
│   │   └── App.tsx            # Main component
│   └── package.json           # Node dependencies
│
├── docs/                       # Documentation
│   ├── IMPLEMENTATION_PLAN.md # Detailed implementation guide
│   ├── ARCHITECTURE_PLAN.md   # System architecture
│   └── API_DOCUMENTATION.md   # API reference
│
└── README.md                   # This file
```

## API Documentation

### Endpoints

#### POST /api/v1/analyze
Analyze a GitHub repository and generate onboarding documentation.

**Request:**
```json
{
  "repository_url": "https://github.com/owner/repo",
  "github_token": "ghp_xxxxxxxxxxxxx",
  "options": {
    "include_readme": true,
    "max_files_to_analyze": 100,
    "file_size_limit_kb": 500
  }
}
```

**Response:**
```json
{
  "repository": {
    "name": "repo-name",
    "owner": "owner-name",
    "description": "Repository description",
    "language": "Python",
    "stars": 1234,
    "forks": 56
  },
  "analysis": {
    "architecture_summary": { ... },
    "important_files": [ ... ],
    "data_flow": { ... },
    "feature_guide": { ... }
  },
  "metadata": {
    "analyzed_at": "2026-05-02T16:30:00Z",
    "total_files": 45,
    "analyzed_files": 38
  }
}
```

For complete API documentation, see [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) or visit `http://localhost:8000/docs` when running the backend.

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

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend
npm test
```

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

- Built for the IBM Hackathon 2026
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- UI built with [React](https://react.dev/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Data from [GitHub REST API](https://docs.github.com/en/rest)

## Support

- 📧 Email: support@devonboard.dev
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/devonboard/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/devonboard/discussions)

## Authors

- Your Name - [@yourhandle](https://github.com/yourhandle)

---

**Made with ❤️ for developers, by developers**

*Simplifying codebase onboarding, one repository at a time.*