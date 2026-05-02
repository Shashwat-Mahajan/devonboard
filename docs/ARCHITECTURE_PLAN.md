# DevOnboard - System Architecture

## High-Level Architecture

```mermaid
graph TB
    User[User Browser]
    Frontend[React Frontend]
    Backend[FastAPI Backend]
    GitHub[GitHub REST API]
    
    User -->|Enters Repo URL + Token| Frontend
    Frontend -->|HTTP Request| Backend
    Backend -->|Fetch Repo Data| GitHub
    GitHub -->|Repository Data| Backend
    Backend -->|Analyze & Generate| Backend
    Backend -->|Onboarding Document| Frontend
    Frontend -->|Display Results| User
    
    style User fill:#e1f5ff
    style Frontend fill:#fff4e1
    style Backend fill:#e8f5e9
    style GitHub fill:#f3e5f5
```

## Component Architecture

### Frontend Architecture

```mermaid
graph LR
    subgraph "React Application"
        UI[UI Components]
        Hooks[Custom Hooks]
        API[API Service]
        Types[TypeScript Types]
        
        UI --> Hooks
        Hooks --> API
        API --> Types
    end
    
    API -->|HTTP| Backend[Backend API]
    
    style UI fill:#bbdefb
    style Hooks fill:#c8e6c9
    style API fill:#fff9c4
    style Types fill:#f8bbd0
```

### Backend Architecture

```mermaid
graph TB
    subgraph "FastAPI Application"
        Routes[API Routes]
        Services[Service Layer]
        Models[Data Models]
        Utils[Utilities]
        
        Routes --> Services
        Services --> Models
        Services --> Utils
    end
    
    subgraph "Service Layer Details"
        GH[GitHub Service]
        Analyzer[Analyzer Service]
        DocGen[Document Generator]
        
        Services --> GH
        Services --> Analyzer
        Services --> DocGen
    end
    
    GH -->|API Calls| GitHub[GitHub API]
    
    style Routes fill:#ffccbc
    style Services fill:#c5cae9
    style Models fill:#b2dfdb
    style Utils fill:#f0f4c3
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant GitHub
    
    User->>Frontend: Enter Repository URL
    User->>Frontend: Provide GitHub Token
    Frontend->>Frontend: Validate Input
    Frontend->>Backend: POST /api/v1/analyze
    
    Backend->>GitHub: GET /repos/owner/repo
    GitHub-->>Backend: Repository Metadata
    
    Backend->>GitHub: GET /repos/owner/repo/git/trees
    GitHub-->>Backend: File Tree Structure
    
    Backend->>GitHub: GET /repos/owner/repo/contents
    GitHub-->>Backend: File Contents
    
    Backend->>Backend: Analyze Repository
    Backend->>Backend: Score File Importance
    Backend->>Backend: Detect Architecture
    Backend->>Backend: Generate Document
    
    Backend-->>Frontend: Analysis Results
    Frontend->>Frontend: Render Components
    Frontend-->>User: Display Onboarding Doc
```

## File Importance Scoring Flow

```mermaid
graph TD
    Start[Start Analysis] --> Fetch[Fetch File Tree]
    Fetch --> Filter[Filter Files]
    Filter --> Score[Calculate Scores]
    
    Score --> Location[Location Score 0-30]
    Score --> Name[Name Pattern Score 0-25]
    Score --> Type[File Type Score 0-20]
    Score --> Size[Size Score 0-15]
    Score --> Special[Special Files Score 0-10]
    
    Location --> Combine[Combine Scores]
    Name --> Combine
    Type --> Combine
    Size --> Combine
    Special --> Combine
    
    Combine --> Sort[Sort by Score]
    Sort --> Top10[Select Top 10]
    Top10 --> End[Return Results]
    
    style Start fill:#c8e6c9
    style End fill:#ffccbc
    style Combine fill:#fff9c4
```

## Repository Analysis Process

```mermaid
graph LR
    subgraph "Input"
        URL[Repository URL]
        Token[GitHub Token]
    end
    
    subgraph "Fetch Phase"
        Meta[Fetch Metadata]
        Tree[Fetch File Tree]
        Content[Fetch Key Files]
    end
    
    subgraph "Analysis Phase"
        Detect[Detect Architecture]
        Score[Score Files]
        Flow[Analyze Data Flow]
    end
    
    subgraph "Generation Phase"
        Summary[Generate Summary]
        Files[List Important Files]
        Guide[Create Feature Guide]
    end
    
    subgraph "Output"
        Doc[Onboarding Document]
    end
    
    URL --> Meta
    Token --> Meta
    Meta --> Tree
    Tree --> Content
    Content --> Detect
    Content --> Score
    Detect --> Flow
    Score --> Files
    Flow --> Summary
    Detect --> Guide
    Summary --> Doc
    Files --> Doc
    Guide --> Doc
    
    style URL fill:#e1f5ff
    style Token fill:#e1f5ff
    style Doc fill:#c8e6c9
```

## Technology Stack

### Backend Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | FastAPI | High-performance async web framework |
| Language | Python 3.10+ | Backend logic and API |
| HTTP Client | httpx | Async GitHub API requests |
| Validation | Pydantic | Data validation and serialization |
| Server | Uvicorn | ASGI server |
| Environment | python-dotenv | Environment variable management |

### Frontend Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | React 18 | UI component library |
| Language | TypeScript | Type-safe JavaScript |
| Build Tool | Vite | Fast development and building |
| HTTP Client | Axios | API communication |
| Styling | Tailwind CSS | Utility-first CSS framework |
| Markdown | react-markdown | Render markdown content |
| Icons | lucide-react | Icon library |

### External Services

| Service | Purpose | Rate Limit |
|---------|---------|------------|
| GitHub REST API | Repository data fetching | 5000 req/hour (authenticated) |

## API Endpoint Design

### POST /api/v1/analyze

**Purpose**: Analyze a GitHub repository and generate onboarding documentation

**Request Flow**:
1. Validate repository URL format
2. Validate GitHub token
3. Fetch repository metadata
4. Fetch file tree structure
5. Fetch contents of important files
6. Analyze and score files
7. Detect architecture patterns
8. Generate onboarding document
9. Return structured response

**Response Structure**:
```json
{
  "repository": {
    "name": "string",
    "owner": "string",
    "description": "string",
    "language": "string",
    "stars": "number",
    "forks": "number"
  },
  "analysis": {
    "architecture_summary": {
      "project_type": "string",
      "tech_stack": ["string"],
      "description": "string"
    },
    "important_files": [
      {
        "path": "string",
        "importance_score": "number",
        "reason": "string",
        "lines_of_code": "number",
        "language": "string"
      }
    ],
    "data_flow": {
      "description": "string",
      "components": [
        {
          "name": "string",
          "description": "string",
          "files": ["string"]
        }
      ]
    },
    "feature_guide": {
      "steps": [
        {
          "step": "number",
          "title": "string",
          "description": "string",
          "files_to_modify": ["string"]
        }
      ]
    }
  },
  "metadata": {
    "analyzed_at": "string",
    "total_files": "number",
    "analyzed_files": "number"
  }
}
```

## Security Considerations

### GitHub Token Handling

```mermaid
graph LR
    User[User] -->|Provides Token| Frontend
    Frontend -->|HTTPS Only| Backend
    Backend -->|Use in Header| GitHub
    Backend -->|Never Store| Backend
    Backend -->|Never Log| Backend
    
    style User fill:#e1f5ff
    style Frontend fill:#fff4e1
    style Backend fill:#e8f5e9
    style GitHub fill:#f3e5f5
```

**Security Measures**:
1. Token transmitted over HTTPS only
2. Token never stored in database or logs
3. Token used only for GitHub API requests
4. Token included in Authorization header
5. Frontend stores token in memory only (not localStorage)
6. Clear security warnings in UI

## Error Handling Strategy

### Error Types and Responses

| Error Type | HTTP Status | User Message |
|------------|-------------|--------------|
| Invalid URL | 400 | "Please provide a valid GitHub repository URL" |
| Invalid Token | 401 | "GitHub token is invalid or expired" |
| Repository Not Found | 404 | "Repository not found or not accessible" |
| Rate Limit Exceeded | 429 | "GitHub API rate limit exceeded. Please try again later" |
| Repository Too Large | 413 | "Repository is too large to analyze" |
| Network Error | 503 | "Unable to connect to GitHub. Please check your connection" |
| Server Error | 500 | "An unexpected error occurred. Please try again" |

### Error Flow

```mermaid
graph TD
    Request[API Request] --> Validate[Validate Input]
    Validate -->|Invalid| Error400[400 Bad Request]
    Validate -->|Valid| GitHub[Call GitHub API]
    
    GitHub -->|Success| Process[Process Data]
    GitHub -->|Auth Error| Error401[401 Unauthorized]
    GitHub -->|Not Found| Error404[404 Not Found]
    GitHub -->|Rate Limit| Error429[429 Too Many Requests]
    GitHub -->|Server Error| Error500[500 Server Error]
    
    Process -->|Success| Response[Return Results]
    Process -->|Error| Error500
    
    Error400 --> Frontend[Display Error]
    Error401 --> Frontend
    Error404 --> Frontend
    Error429 --> Frontend
    Error500 --> Frontend
    Response --> Frontend[Display Results]
    
    style Request fill:#c8e6c9
    style Response fill:#c8e6c9
    style Frontend fill:#fff4e1
```

## Performance Optimization

### Caching Strategy (Future Enhancement)

```mermaid
graph LR
    Request[API Request] --> Cache{Cache Hit?}
    Cache -->|Yes| Return[Return Cached]
    Cache -->|No| Fetch[Fetch from GitHub]
    Fetch --> Analyze[Analyze Repository]
    Analyze --> Store[Store in Cache]
    Store --> Return
    
    style Request fill:#e1f5ff
    style Return fill:#c8e6c9
    style Cache fill:#fff9c4
```

### Optimization Techniques

1. **Lazy Loading**: Fetch file contents only for top-scored files
2. **Pagination**: Process large repositories in chunks
3. **Parallel Requests**: Fetch multiple files concurrently
4. **Response Compression**: Enable gzip compression
5. **File Size Limits**: Skip files larger than 500KB
6. **Smart Filtering**: Ignore common directories (node_modules, .git, etc.)

## Deployment Architecture (Future)

```mermaid
graph TB
    subgraph "Frontend Deployment"
        CDN[CDN - Vercel/Netlify]
        Static[Static Assets]
        CDN --> Static
    end
    
    subgraph "Backend Deployment"
        API[API Server - Railway/Render]
        Worker[Background Workers]
        API --> Worker
    end
    
    subgraph "External Services"
        GitHub[GitHub API]
        Cache[Redis Cache]
    end
    
    User[Users] --> CDN
    CDN --> API
    API --> GitHub
    API --> Cache
    
    style User fill:#e1f5ff
    style CDN fill:#fff4e1
    style API fill:#e8f5e9
    style GitHub fill:#f3e5f5
```

## Scalability Considerations

### Current Design (Hackathon)
- Single server deployment
- Synchronous processing
- No caching layer
- Direct GitHub API calls

### Future Scalability
- Horizontal scaling with load balancer
- Background job processing with Celery/RQ
- Redis caching layer
- Database for storing analysis results
- CDN for static assets
- Rate limiting per user
- WebSocket for real-time updates

## Development Environment Setup

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher
- Git
- GitHub personal access token
- Code editor (VS Code recommended)

### Local Development Ports
- Backend API: `http://localhost:8000`
- Frontend Dev Server: `http://localhost:5173`
- API Documentation: `http://localhost:8000/docs`

## Testing Strategy

### Backend Testing
- Unit tests for analyzer logic
- Integration tests for GitHub API service
- API endpoint tests
- Mock GitHub API responses

### Frontend Testing
- Component unit tests
- Integration tests for API calls
- E2E tests with Playwright (optional)

### Manual Testing Checklist
- [ ] Small repository (< 50 files)
- [ ] Medium repository (50-200 files)
- [ ] Large repository (> 200 files)
- [ ] Python project
- [ ] JavaScript/TypeScript project
- [ ] Multi-language project
- [ ] Repository with README
- [ ] Repository without README
- [ ] Private repository
- [ ] Invalid repository URL
- [ ] Invalid GitHub token
- [ ] Rate limit handling

## Success Criteria

### Functional Requirements
✅ Accept GitHub repository URL
✅ Validate GitHub token
✅ Fetch repository structure
✅ Analyze file importance
✅ Detect project architecture
✅ Generate onboarding document
✅ Display results in clean UI
✅ Handle errors gracefully

### Non-Functional Requirements
✅ Response time < 10 seconds for typical repository
✅ Support repositories up to 500 files
✅ Mobile-responsive UI
✅ Clear error messages
✅ Intuitive user experience

## Future Enhancements Roadmap

### Phase 1: AI Integration
- OpenAI GPT-4 for intelligent summaries
- Context-aware feature guides
- Code explanation generation

### Phase 2: Advanced Analysis
- Dependency graph visualization
- Code quality metrics
- Security vulnerability scanning
- Test coverage analysis

### Phase 3: Collaboration Features
- Team workspaces
- Shared analysis results
- Comments and annotations
- Export to various formats

### Phase 4: Platform Integration
- VS Code extension
- GitHub App integration
- Slack/Discord notifications
- CI/CD pipeline integration

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-02  
**Status**: Ready for Implementation