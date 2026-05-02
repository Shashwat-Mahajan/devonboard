# DevOnboard - Implementation Plan

## Project Overview

**DevOnboard** is a web application that helps developers quickly understand and onboard to new GitHub repositories by automatically generating comprehensive onboarding documentation.

### Core Features
1. Accept GitHub repository URL from user
2. Fetch repository structure and key file contents via GitHub REST API
3. Analyze repository to identify important files and patterns
4. Generate developer onboarding document containing:
   - Architecture summary
   - Top 10 most important files with explanations
   - Data flow description
   - Step-by-step guide for adding new features

### Tech Stack
- **Backend**: Python 3.10+ with FastAPI
- **Frontend**: React 18+ with TypeScript
- **API Integration**: GitHub REST API (with personal access token)
- **Future Enhancement**: AI integration for intelligent analysis

---

## Project Structure

```
devonboard/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── config.py                  # Configuration and environment variables
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── repository.py          # Pydantic models for repository data
│   │   │   └── analysis.py            # Pydantic models for analysis results
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── github_service.py      # GitHub API integration
│   │   │   ├── analyzer_service.py    # Repository analysis logic
│   │   │   └── document_generator.py  # Onboarding document generation
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py              # API route definitions
│   │   │   └── dependencies.py        # Dependency injection
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_analyzer.py       # File importance scoring
│   │       └── helpers.py             # Utility functions
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_github_service.py
│   │   └── test_analyzer_service.py
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Environment variables template
│   └── README.md                      # Backend setup instructions
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── RepositoryInput.tsx    # URL input component
│   │   │   ├── LoadingSpinner.tsx     # Loading state component
│   │   │   ├── ErrorMessage.tsx       # Error display component
│   │   │   ├── OnboardingDocument.tsx # Main results display
│   │   │   ├── ArchitectureSummary.tsx
│   │   │   ├── ImportantFiles.tsx
│   │   │   ├── DataFlowDiagram.tsx
│   │   │   └── FeatureGuide.tsx
│   │   ├── services/
│   │   │   └── api.ts                 # API client for backend
│   │   ├── types/
│   │   │   └── index.ts               # TypeScript type definitions
│   │   ├── hooks/
│   │   │   └── useRepository.ts       # Custom hook for repo analysis
│   │   ├── utils/
│   │   │   └── helpers.ts             # Utility functions
│   │   ├── App.tsx                    # Main application component
│   │   ├── App.css                    # Application styles
│   │   ├── main.tsx                   # Application entry point
│   │   └── vite-env.d.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── README.md                      # Frontend setup instructions
│
├── docs/
│   ├── ARCHITECTURE_PLAN.md           # System architecture documentation
│   ├── IMPLEMENTATION_PLAN.md         # This file
│   └── API_DOCUMENTATION.md           # API endpoint documentation
│
├── .gitignore
└── README.md                          # Project overview and setup
```

---

## API Design

### Backend Endpoints

#### 1. Analyze Repository
**POST** `/api/v1/analyze`

Accepts a GitHub repository URL and returns comprehensive analysis.

**Request Body:**
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
    "architecture_summary": {
      "project_type": "Web Application",
      "tech_stack": ["Python", "FastAPI", "React"],
      "description": "Detailed architecture description..."
    },
    "important_files": [
      {
        "path": "src/main.py",
        "importance_score": 95,
        "reason": "Main application entry point",
        "lines_of_code": 250,
        "language": "Python"
      }
    ],
    "data_flow": {
      "description": "Data flow description...",
      "components": [
        {
          "name": "API Layer",
          "description": "Handles HTTP requests",
          "files": ["src/api/routes.py"]
        }
      ]
    },
    "feature_guide": {
      "steps": [
        {
          "step": 1,
          "title": "Identify the feature location",
          "description": "Determine which module handles similar features",
          "files_to_modify": ["src/features/"]
        }
      ]
    }
  },
  "metadata": {
    "analyzed_at": "2026-05-02T16:30:00Z",
    "total_files": 45,
    "analyzed_files": 38
  }
}
```

#### 2. Health Check
**GET** `/api/v1/health`

Returns API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

#### 3. Validate Repository
**POST** `/api/v1/validate`

Validates if a GitHub URL is accessible with provided token.

**Request Body:**
```json
{
  "repository_url": "https://github.com/owner/repo",
  "github_token": "ghp_xxxxxxxxxxxxx"
}
```

**Response:**
```json
{
  "valid": true,
  "accessible": true,
  "repository_exists": true,
  "message": "Repository is accessible"
}
```

---

## Implementation Phases

### Phase 1: Backend Foundation (Days 1-2)

#### Step 1.1: Project Setup
- Initialize Python virtual environment
- Install FastAPI, uvicorn, pydantic, httpx, python-dotenv
- Create basic project structure
- Set up `.env.example` with required variables

**Key Files to Create:**
- [`backend/requirements.txt`](backend/requirements.txt)
- [`backend/app/main.py`](backend/app/main.py)
- [`backend/app/config.py`](backend/app/config.py)
- [`backend/.env.example`](backend/.env.example)

#### Step 1.2: GitHub API Service
- Implement GitHub REST API client
- Add methods for:
  - Fetching repository metadata
  - Getting repository tree (file structure)
  - Fetching file contents
  - Handling rate limits and errors

**Key Files to Create:**
- [`backend/app/services/github_service.py`](backend/app/services/github_service.py)
- [`backend/app/models/repository.py`](backend/app/models/repository.py)

**GitHub API Endpoints to Use:**
- `GET /repos/{owner}/{repo}` - Repository metadata
- `GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1` - File tree
- `GET /repos/{owner}/{repo}/contents/{path}` - File contents
- `GET /repos/{owner}/{repo}/languages` - Language statistics

#### Step 1.3: Repository Analyzer
- Implement file importance scoring algorithm
- Create logic to identify:
  - Entry points (main.py, index.js, etc.)
  - Configuration files
  - Core business logic files
  - Test files
  - Documentation files

**Scoring Criteria:**
- File location (root vs nested)
- File type and extension
- File size (not too small, not too large)
- Naming patterns (main, app, index, config)
- Import/dependency frequency
- README mentions

**Key Files to Create:**
- [`backend/app/services/analyzer_service.py`](backend/app/services/analyzer_service.py)
- [`backend/app/utils/file_analyzer.py`](backend/app/utils/file_analyzer.py)
- [`backend/app/models/analysis.py`](backend/app/models/analysis.py)

### Phase 2: Backend API Endpoints (Day 2)

#### Step 2.1: Create API Routes
- Implement `/api/v1/analyze` endpoint
- Implement `/api/v1/health` endpoint
- Implement `/api/v1/validate` endpoint
- Add CORS middleware for frontend integration
- Add request validation and error handling

**Key Files to Create:**
- [`backend/app/api/routes.py`](backend/app/api/routes.py)
- [`backend/app/api/dependencies.py`](backend/app/api/dependencies.py)

#### Step 2.2: Document Generator
- Create service to generate structured onboarding document
- Implement architecture summary generation
- Implement data flow analysis
- Create feature addition guide template

**Key Files to Create:**
- [`backend/app/services/document_generator.py`](backend/app/services/document_generator.py)

### Phase 3: Frontend Foundation (Days 3-4)

#### Step 3.1: React Project Setup
- Initialize React project with Vite + TypeScript
- Install dependencies: axios, react-markdown, tailwindcss
- Set up project structure
- Configure environment variables

**Key Files to Create:**
- [`frontend/package.json`](frontend/package.json)
- [`frontend/vite.config.ts`](frontend/vite.config.ts)
- [`frontend/tsconfig.json`](frontend/tsconfig.json)
- [`frontend/.env.example`](frontend/.env.example)

**Dependencies:**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "react-markdown": "^9.0.0",
    "lucide-react": "^0.300.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

#### Step 3.2: API Service Layer
- Create API client for backend communication
- Implement error handling and retry logic
- Add TypeScript types for API responses

**Key Files to Create:**
- [`frontend/src/services/api.ts`](frontend/src/services/api.ts)
- [`frontend/src/types/index.ts`](frontend/src/types/index.ts)

### Phase 4: Frontend UI Components (Day 4-5)

#### Step 4.1: Input Components
- Create repository URL input form
- Add GitHub token input (with secure handling)
- Implement form validation
- Add loading spinner component

**Key Files to Create:**
- [`frontend/src/components/RepositoryInput.tsx`](frontend/src/components/RepositoryInput.tsx)
- [`frontend/src/components/LoadingSpinner.tsx`](frontend/src/components/LoadingSpinner.tsx)
- [`frontend/src/components/ErrorMessage.tsx`](frontend/src/components/ErrorMessage.tsx)

#### Step 4.2: Results Display Components
- Create main onboarding document component
- Build architecture summary display
- Create important files list with explanations
- Implement data flow visualization
- Build feature guide component

**Key Files to Create:**
- [`frontend/src/components/OnboardingDocument.tsx`](frontend/src/components/OnboardingDocument.tsx)
- [`frontend/src/components/ArchitectureSummary.tsx`](frontend/src/components/ArchitectureSummary.tsx)
- [`frontend/src/components/ImportantFiles.tsx`](frontend/src/components/ImportantFiles.tsx)
- [`frontend/src/components/DataFlowDiagram.tsx`](frontend/src/components/DataFlowDiagram.tsx)
- [`frontend/src/components/FeatureGuide.tsx`](frontend/src/components/FeatureGuide.tsx)

#### Step 4.3: Custom Hooks
- Create `useRepository` hook for state management
- Handle loading, error, and success states
- Implement data fetching logic

**Key Files to Create:**
- [`frontend/src/hooks/useRepository.ts`](frontend/src/hooks/useRepository.ts)

### Phase 5: Integration & Testing (Day 5-6)

#### Step 5.1: End-to-End Integration
- Connect frontend to backend API
- Test with various repository types
- Handle edge cases and errors
- Optimize performance

#### Step 5.2: Error Handling
- Add comprehensive error messages
- Implement retry mechanisms
- Handle GitHub API rate limits
- Add user-friendly error displays

#### Step 5.3: Testing
- Test with public repositories
- Test with private repositories
- Test with different repository sizes
- Test error scenarios

**Test Repositories:**
- Small project: Simple Python script repo
- Medium project: FastAPI application
- Large project: Popular open-source project
- Different languages: Python, JavaScript, Go, etc.

### Phase 6: Documentation & Polish (Day 6-7)

#### Step 6.1: Documentation
- Write comprehensive README
- Document API endpoints
- Create setup instructions
- Add troubleshooting guide

**Key Files to Create:**
- [`README.md`](README.md) - Main project documentation
- [`backend/README.md`](backend/README.md) - Backend setup
- [`frontend/README.md`](frontend/README.md) - Frontend setup
- [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) - API reference

#### Step 6.2: UI/UX Polish
- Add responsive design
- Improve loading states
- Add animations and transitions
- Implement dark mode (optional)

#### Step 6.3: Deployment Preparation
- Add Docker configuration (optional)
- Create deployment scripts
- Document deployment process

---

## Analysis Algorithm Details

### File Importance Scoring

The analyzer will score files based on multiple factors:

```python
def calculate_importance_score(file_info):
    score = 0
    
    # Location scoring (0-30 points)
    if file_info.depth == 0:  # Root level
        score += 30
    elif file_info.depth == 1:
        score += 20
    elif file_info.depth == 2:
        score += 10
    
    # Name pattern scoring (0-25 points)
    important_names = ['main', 'app', 'index', 'server', 'config', 'settings']
    if any(name in file_info.name.lower() for name in important_names):
        score += 25
    
    # File type scoring (0-20 points)
    if file_info.extension in ['.py', '.js', '.ts', '.go', '.java']:
        score += 20
    elif file_info.extension in ['.json', '.yaml', '.yml', '.toml']:
        score += 15
    
    # Size scoring (0-15 points)
    if 100 < file_info.lines_of_code < 1000:
        score += 15
    elif 50 < file_info.lines_of_code < 2000:
        score += 10
    
    # Special files (0-10 points)
    if file_info.name.lower() in ['readme.md', 'package.json', 'requirements.txt']:
        score += 10
    
    return score
```

### Architecture Detection

Detect project type based on files present:

```python
def detect_architecture(file_tree):
    patterns = {
        'FastAPI': ['main.py', 'app/', 'requirements.txt'],
        'Django': ['manage.py', 'settings.py', 'wsgi.py'],
        'Flask': ['app.py', 'requirements.txt'],
        'React': ['package.json', 'src/', 'public/'],
        'Next.js': ['next.config.js', 'pages/'],
        'Express': ['package.json', 'server.js', 'app.js'],
        'Spring Boot': ['pom.xml', 'src/main/java/'],
    }
    
    detected = []
    for framework, required_files in patterns.items():
        if all(file_exists(f, file_tree) for f in required_files):
            detected.append(framework)
    
    return detected
```

### Data Flow Analysis

Identify common patterns:

1. **Entry Points**: Files that start the application
2. **Routers/Controllers**: Handle HTTP requests
3. **Services/Business Logic**: Core functionality
4. **Models/Schemas**: Data structures
5. **Database/Storage**: Data persistence
6. **External APIs**: Third-party integrations

---

## Environment Variables

### Backend (.env)
```
# GitHub API
GITHUB_TOKEN=your_github_token_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Analysis Settings
MAX_FILES_TO_ANALYZE=100
FILE_SIZE_LIMIT_KB=500
GITHUB_API_TIMEOUT=30
```

### Frontend (.env)
```
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=DevOnboard
```

---

## Development Workflow

### Running the Application

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Testing Flow

1. Start backend server
2. Start frontend development server
3. Open browser to `http://localhost:5173`
4. Enter a GitHub repository URL
5. Provide GitHub personal access token
6. Click "Analyze Repository"
7. View generated onboarding document

---

## Future Enhancements (Post-Hackathon)

### Phase 7: AI Integration
- Integrate OpenAI GPT-4 or Claude API
- Generate intelligent architecture summaries
- Create context-aware feature guides
- Improve file importance analysis with AI

### Phase 8: Advanced Features
- Repository comparison
- Historical analysis (track changes over time)
- Team collaboration features
- Export to PDF/Markdown
- Integration with documentation platforms
- Code snippet extraction and explanation
- Dependency graph visualization
- Security vulnerability scanning

### Phase 9: Performance Optimization
- Caching layer for analyzed repositories
- Background job processing
- Database for storing analysis results
- CDN for static assets

---

## Success Metrics

For the hackathon demo, success means:

1. ✅ User can input any public GitHub repository URL
2. ✅ System fetches and analyzes repository structure
3. ✅ Generates comprehensive onboarding document with:
   - Clear architecture summary
   - Top 10 important files with explanations
   - Data flow description
   - Feature addition guide
4. ✅ Clean, intuitive UI
5. ✅ Handles errors gracefully
6. ✅ Works with repositories of various sizes and languages

---

## Risk Mitigation

### Potential Issues & Solutions

1. **GitHub API Rate Limits**
   - Solution: Use authenticated requests (5000/hour vs 60/hour)
   - Implement caching for repeated requests
   - Show rate limit status to user

2. **Large Repositories**
   - Solution: Limit analysis to top-level files initially
   - Implement pagination for file fetching
   - Set maximum file size limits

3. **Private Repositories**
   - Solution: Require user's personal access token
   - Clear instructions on token creation
   - Secure token handling (never store)

4. **Complex Project Structures**
   - Solution: Focus on common patterns first
   - Graceful degradation for unknown structures
   - Allow manual hints from user

5. **Analysis Accuracy**
   - Solution: Use multiple heuristics for scoring
   - Test with diverse repository types
   - Iterate based on feedback

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1: Backend Foundation | 2 days | GitHub API service, analyzer logic |
| Phase 2: Backend API | 1 day | REST endpoints, document generator |
| Phase 3: Frontend Setup | 1 day | React project, API client |
| Phase 4: Frontend UI | 1.5 days | All UI components |
| Phase 5: Integration & Testing | 1 day | Working end-to-end flow |
| Phase 6: Documentation & Polish | 0.5 days | Documentation, UI polish |
| **Total** | **7 days** | **Complete hackathon demo** |

---

## Next Steps

1. ✅ Review this implementation plan
2. Set up development environment
3. Start with Phase 1: Backend Foundation
4. Follow the implementation order outlined above
5. Test frequently with real repositories
6. Iterate based on results

Ready to start building! 🚀