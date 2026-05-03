"""
Unit tests for github_client module.
Tests GitHub API interactions with the new implementation.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from github_client import (
    parse_github_url,
    detect_language,
    detect_framework,
    detect_repo_type,
    fetch_repo_data,
)


class TestParseGithubUrl:
    """Tests for parse_github_url function."""
    
    def test_https_url(self):
        """Test parsing standard HTTPS GitHub URL."""
        owner, repo = parse_github_url("https://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_https_url_with_www(self):
        """Test parsing HTTPS URL with www."""
        owner, repo = parse_github_url("https://www.github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_http_url(self):
        """Test parsing HTTP GitHub URL."""
        owner, repo = parse_github_url("http://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_url_with_trailing_slash(self):
        """Test URL with trailing slash."""
        owner, repo = parse_github_url("https://github.com/owner/repo/")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_url_with_git_extension(self):
        """Test URL with .git extension."""
        owner, repo = parse_github_url("https://github.com/owner/repo.git")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_invalid_url_empty(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            parse_github_url("")
    
    def test_invalid_url_whitespace(self):
        """Test that whitespace-only URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            parse_github_url("   ")
    
    def test_invalid_url_not_github(self):
        """Test that non-GitHub URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            parse_github_url("https://gitlab.com/owner/repo")
    
    def test_invalid_url_format(self):
        """Test that malformed GitHub URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            parse_github_url("https://github.com/owner")
    
    def test_invalid_url_none(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            parse_github_url(None)


class TestDetectLanguage:
    """Tests for detect_language function."""
    
    def test_javascript_detection(self):
        """Test JavaScript detection from .js files."""
        files = ["src/app.js", "utils.js", "index.js"]
        result = detect_language(files)
        assert result == "JavaScript"
    
    def test_typescript_detection(self):
        """Test TypeScript detection from .ts files."""
        files = ["src/app.ts", "utils.ts", "index.ts"]
        result = detect_language(files)
        assert result == "TypeScript"
    
    def test_python_detection(self):
        """Test Python detection from .py files."""
        files = ["main.py", "utils.py", "models.py"]
        result = detect_language(files)
        assert result == "Python"
    
    def test_mixed_files_most_common(self):
        """Test that most common language is detected."""
        files = ["app.py", "utils.py", "test.js", "config.py"]
        result = detect_language(files)
        assert result == "Python"
    
    def test_react_jsx_detection(self):
        """Test React detection from .jsx files."""
        files = ["App.jsx", "Component.jsx"]
        result = detect_language(files)
        assert result == "JavaScript/React"
    
    def test_unknown_language(self):
        """Test unknown language for non-code files."""
        files = ["README.md", "config.json", "data.txt"]
        result = detect_language(files)
        assert result == "Unknown"


class TestDetectFramework:
    """Tests for detect_framework function."""
    
    def test_nextjs_detection(self):
        """Test Next.js detection."""
        files = ["next.config.js", "pages/_app.js", "pages/index.js"]
        result = detect_framework(files)
        assert result == "Next.js"
    
    def test_react_detection(self):
        """Test React detection."""
        files = ["src/App.jsx", "src/components/Button.jsx"]
        result = detect_framework(files)
        assert result == "React"
    
    def test_fastapi_detection(self):
        """Test FastAPI detection."""
        files = ["main.py", "routes/api.py"]
        result = detect_framework(files)
        # Should detect FastAPI if file contains fastapi patterns
        assert result in ["FastAPI", "Unknown"]
    
    def test_express_detection(self):
        """Test Express detection."""
        files = ["server.js", "routes/api.js", "app.js"]
        result = detect_framework(files)
        # Should detect Express if file contains express patterns
        assert result in ["Express", "Unknown"]
    
    def test_django_detection(self):
        """Test Django detection."""
        files = ["settings.py", "urls.py", "manage.py"]
        result = detect_framework(files)
        assert result == "Django"
    
    def test_unknown_framework(self):
        """Test unknown framework."""
        files = ["main.py", "utils.py"]
        result = detect_framework(files)
        assert result == "Unknown"


class TestDetectRepoType:
    """Tests for detect_repo_type function."""
    
    def test_frontend_detection(self):
        """Test frontend project detection."""
        files = ["src/App.jsx", "src/components/Button.tsx", "public/index.html"]
        result = detect_repo_type(files)
        assert result['has_frontend'] is True
        assert result['language'] in ["JavaScript/React", "TypeScript/React"]
    
    def test_backend_detection(self):
        """Test backend project detection."""
        files = ["main.py", "routes/api.py", "models/user.py"]
        result = detect_repo_type(files)
        assert result['has_backend'] is True
        assert result['language'] == "Python"
    
    def test_database_detection(self):
        """Test database detection."""
        files = ["models/user.py", "migrations/001_initial.py", "schema.sql"]
        result = detect_repo_type(files)
        assert result['has_database'] is True
    
    def test_auth_detection(self):
        """Test authentication detection."""
        files = ["auth/login.py", "middleware/jwt.js", "guards/auth.guard.ts"]
        result = detect_repo_type(files)
        assert result['has_auth'] is True
    
    def test_tests_detection(self):
        """Test tests detection."""
        files = ["tests/test_api.py", "__tests__/App.test.js", "spec/user.spec.js"]
        result = detect_repo_type(files)
        assert result['has_tests'] is True
    
    def test_fullstack_detection(self):
        """Test fullstack project detection."""
        files = [
            "frontend/src/App.jsx",
            "backend/main.py",
            "backend/models/user.py",
            "backend/auth/login.py"
        ]
        result = detect_repo_type(files)
        assert result['has_frontend'] is True
        assert result['has_backend'] is True
        assert result['has_database'] is True
        assert result['has_auth'] is True


class TestFetchRepoData:
    """Tests for fetch_repo_data function - main integration function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful repository data fetch."""
        with patch('github_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock repository metadata
            repo_response = Mock()
            repo_response.status_code = 200
            repo_response.json.return_value = {
                "description": "Test repo",
                "stargazers_count": 100,
                "language": "Python",
                "default_branch": "main"
            }
            
            # Mock tree with files
            tree_response = Mock()
            tree_response.status_code = 200
            tree_response.json.return_value = {
                "tree": [
                    {"path": "README.md", "type": "blob", "size": 100, "sha": "abc123"},
                    {"path": "main.py", "type": "blob", "size": 500, "sha": "def456"},
                ]
            }
            
            # Mock file content responses
            import base64
            readme_content = "# Test Project"
            main_content = "def main(): pass"
            
            readme_response = Mock()
            readme_response.status_code = 200
            readme_response.json.return_value = {
                "content": base64.b64encode(readme_content.encode()).decode(),
                "size": len(readme_content)
            }
            
            main_response = Mock()
            main_response.status_code = 200
            main_response.json.return_value = {
                "content": base64.b64encode(main_content.encode()).decode(),
                "size": len(main_content)
            }
            
            # Set up mock responses in order
            mock_client.get.side_effect = [
                repo_response,
                tree_response,
                readme_response,
                main_response,
            ]
            
            result = await fetch_repo_data("https://github.com/owner/repo")
            
            # Verify result structure
            assert result['owner'] == 'owner'
            assert result['repo'] == 'repo'
            assert result['description'] == 'Test repo'
            assert result['stars'] == 100
            assert result['language'] == 'Python'
            assert len(result['files']) >= 1
            assert 'repo_type' in result
            assert result['file_count'] == 2
    
    @pytest.mark.asyncio
    async def test_invalid_url_raises_error(self):
        """Test that invalid GitHub URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            await fetch_repo_data("https://gitlab.com/owner/repo")
    
    @pytest.mark.asyncio
    async def test_repository_not_found(self):
        """Test error handling when repository is not found."""
        with patch('github_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock 404 response
            repo_response = Mock()
            repo_response.status_code = 404
            mock_client.get.return_value = repo_response
            
            with pytest.raises(ValueError, match="Repository not found"):
                await fetch_repo_data("https://github.com/owner/nonexistent")
    


# Made with Bob
