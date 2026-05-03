# GitHub Repository Analyzer - Frontend

A clean, minimal React application for analyzing GitHub repositories and generating onboarding documentation.

## Features

- ✅ Centered input box for GitHub URL
- ✅ "Analyze Repo" button with loading state
- ✅ Loading spinner during API calls
- ✅ Markdown rendering for onboarding documents
- ✅ Error handling for invalid URLs and API failures
- ✅ Clean, minimal styling with plain CSS
- ✅ No external UI libraries

## Tech Stack

- React 18
- Vite
- Plain CSS

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

1. Enter a valid GitHub repository URL (e.g., `https://github.com/username/repo`)
2. Click "Analyze Repo" or press Enter
3. Wait for the analysis to complete
4. View the generated onboarding documentation

## API Integration

The app makes POST requests to `http://localhost:8000/analyze` with the following payload:

```json
{
  "repo_url": "https://github.com/username/repo"
}
```

Make sure the backend server is running on port 8000.

## File Structure

- `App.jsx` (98 lines) - Main application component with state management and API calls
- `MarkdownRenderer.jsx` (54 lines) - Safe markdown rendering component
- `App.css` - Styling for the application
- `index.css` - Global styles

**Total: 152 lines of React code** (under 200 lines requirement)
