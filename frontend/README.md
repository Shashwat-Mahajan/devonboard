# DevOnboard Frontend

A clean, minimal React application for analyzing GitHub repositories and generating AI-powered onboarding documentation.

## Features

- ✅ Centered input box for GitHub URL
- ✅ "Analyze Repo" button with loading state
- ✅ Loading spinner during API calls
- ✅ Markdown rendering for onboarding documents
- ✅ **Interactive Q&A feature with AI-powered answers**
- ✅ Error handling for invalid URLs and API failures
- ✅ Clean, minimal styling with plain CSS
- ✅ No external UI libraries
- ✅ **Built entirely with IBM Bob**

## Tech Stack

- React 18
- Vite
- Plain CSS (no Tailwind, no UI libraries)
- Custom Markdown Renderer

## Getting Started

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

## Usage

1. Enter a valid GitHub repository URL (e.g., `https://github.com/fastapi/fastapi`)
2. Click "Analyze Repo" or press Enter
3. Wait for the analysis to complete (typically < 60 seconds)
4. View the generated onboarding documentation with AI insights
5. Ask follow-up questions using the Q&A feature

## API Integration

### Analyze Repository
POST request to `http://localhost:8000/analyze`:
```json
{
  "repo_url": "https://github.com/username/repo"
}
```

### Ask Questions
POST request to `http://localhost:8000/ask`:
```json
{
  "repo_url": "https://github.com/username/repo",
  "question": "How does authentication work?"
}
```

Make sure the backend server is running on port 8000.

## File Structure

- `App.jsx` (98 lines) - Main application component with state management, API calls, and Q&A feature
- `MarkdownRenderer.jsx` (54 lines) - Safe markdown rendering component
- `App.css` - Clean, minimal styling
- `index.css` - Global styles
- `main.jsx` - Application entry point

**Total: 152 lines of React code** (minimal, clean implementation)

## Key Features

### 1. Repository Analysis
- Input GitHub repository URL
- Real-time loading state
- Error handling for invalid URLs
- Markdown rendering of analysis results

### 2. AI-Powered Insights
- Automatic AI insights generation using IBM watsonx.ai
- Contextual observations about the codebase
- Recommendations for onboarding

### 3. Interactive Q&A
- Ask follow-up questions about the repository
- Get AI-powered answers using Llama 70B
- Context-aware responses based on analysis

## Built with IBM Bob

This entire frontend was developed using IBM Bob:
- Component structure planned in Plan mode
- All React code generated in Code mode
- Styling and UX refined through Bob
- Documentation written by Bob

## Performance

- Fast initial load
- Efficient API calls
- Responsive UI
- Minimal bundle size (no heavy dependencies)
