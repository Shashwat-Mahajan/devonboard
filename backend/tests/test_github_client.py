"""
Unit tests for github_client module.
Tests GitHub API interactions with mocked responses.
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
    should_skip_file,
    fetch_repo_tree,
    fetch_file_content,
    fetch_repo_contents,
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
    
    def test_ssh_url(self):
        """Test parsing SSH GitHub URL."""
        owner, repo = parse_github_url("git@github.com:owner/repo")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_invalid_url_empty(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            parse_github_url("")
    
    def test_invalid_url_whitespace(self):
        """Test that whitespace-only URL raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            parse_github_url("   ")
    
    def test_invalid_url_not_github(self):
        """Test that non-GitHub URL raises ValueError."""
        with pytest.raises(ValueError, match="GitHub repository URL"):
            parse_github_url("https://gitlab.com/owner/repo")
    
    def test_invalid_url_format(self):
        """Test that malformed GitHub URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid GitHub URL format"):
            parse_github_url("https://github.com/owner")
    
    def test_invalid_url_none(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            parse_github_url(None)


class TestShouldSkipFile:
    """Tests for should_skip_file function."""
    
    def test_skip_node_modules(self):
        """Test that node_modules files are skipped."""
        assert should_skip_file("node_modules/package/index.js") is True
    
    def test_skip_git_directory(self):
        """Test that .git files are skipped."""
        assert should_skip_file(".git/config") is True
    
    def test_skip_pycache(self):
        """Test that __pycache__ files are skipped."""
        assert should_skip_file("__pycache__/module.pyc") is True
    
    def test_skip_binary_extensions(self):
        """Test that binary files are skipped."""
        assert should_skip_file("image.png") is True
        assert should_skip_file("document.pdf") is True
        assert should_skip_file("archive.zip") is True
    
    def test_skip_lock_files(self):
        """Test that lock files are skipped."""
        assert should_skip_file("package-lock.json") is True
        assert should_skip_file("yarn.lock") is True
    
    def test_allow_source_files(self):
        """Test that source files are not skipped."""
        assert should_skip_file("src/app.py") is False
        assert should_skip_file("index.js") is False
        assert should_skip_file("README.md") is False
    
    def test_skip_path_traversal(self):
        """Test that path traversal attempts are skipped."""
        assert should_skip_file("../etc/passwd") is True
        assert should_skip_file("/etc/passwd") is True
    
    def test_skip_invalid_input(self):
        """Test that invalid input is skipped."""
        assert should_skip_file("") is True
        assert should_skip_file(None) is True


class TestFetchRepoTree:
    """Tests for fetch_repo_tree function with mocked API calls."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful repository tree fetch."""
        # Mock HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Mock repository metadata response
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.json.return_value = {"default_branch": "main"}
        
        # Mock tree response
        tree_response = Mock()
        tree_response.status_code = 200
        tree_response.json.return_value = {
            "tree": [
                {"path": "README.md", "type": "blob", "size": 100},
                {"path": "src/app.py", "type": "blob", "size": 500},
            ]
        }
        
        # Set up mock to return different responses for different calls
        mock_client.get.side_effect = [repo_response, tree_response]
        
        result = await fetch_repo_tree("owner", "repo", mock_client)
        
        assert len(result) == 2
        assert result[0]["path"] == "README.md"
        assert result[1]["path"] == "src/app.py"
    
    @pytest.mark.asyncio
    async def test_repository_not_found(self):
        """Test error handling when repository is not found."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Mock 404 response
        repo_response = Mock()
        repo_response.status_code = 404
        mock_client.get.return_value = repo_response
        
        with pytest.raises(ValueError, match="Repository not found"):
            await fetch_repo_tree("owner", "nonexistent", mock_client)
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test error handling when rate limit is exceeded."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Mock 403 response (rate limit)
        repo_response = Mock()
        repo_response.status_code = 403
        repo_response.json.return_value = {"message": "rate limit exceeded"}
        mock_client.get.return_value = repo_response
        
        with pytest.raises(PermissionError, match="rate limit"):
            await fetch_repo_tree("owner", "repo", mock_client)
    
    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test error handling on timeout."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        
        with pytest.raises(TimeoutError):
            await fetch_repo_tree("owner", "repo", mock_client)


class TestFetchFileContent:
    """Tests for fetch_file_content function with mocked API calls."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful file content fetch."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Mock successful response with base64 content
        import base64
        content = "print('hello world')"
        encoded = base64.b64encode(content.encode()).decode()
        
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "content": encoded,
            "size": len(content)
        }
        mock_client.get.return_value = response
        
        result = await fetch_file_content("owner", "repo", "test.py", mock_client)
        
        assert result == content
    
    @pytest.mark.asyncio
    async def test_file_too_large(self):
        """Test that large files return None."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "content": "dGVzdA==",
            "size": 2 * 1024 * 1024  # 2MB (exceeds MAX_FILE_SIZE)
        }
        mock_client.get.return_value = response
        
        result = await fetch_file_content("owner", "repo", "large.bin", mock_client)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_binary_content_filtered(self):
        """Test that binary content is filtered out."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Create content with null bytes (binary indicator)
        import base64
        binary_content = b"text\x00binary"
        encoded = base64.b64encode(binary_content).decode()
        
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "content": encoded,
            "size": len(binary_content)
        }
        mock_client.get.return_value = response
        
        result = await fetch_file_content("owner", "repo", "binary.bin", mock_client)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_rate_limit_returns_none(self):
        """Test that rate limit returns None instead of raising."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        response = Mock()
        response.status_code = 429
        mock_client.get.return_value = response
        
        result = await fetch_file_content("owner", "repo", "test.py", mock_client)
        
        assert result is None


class TestFetchRepoContents:
    """Tests for fetch_repo_contents function - main integration function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch_filters_binary(self):
        """Test that binary files are filtered out from results."""
        with patch('github_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock repository metadata
            repo_response = Mock()
            repo_response.status_code = 200
            repo_response.json.return_value = {"default_branch": "main"}
            
            # Mock tree with mixed file types
            tree_response = Mock()
            tree_response.status_code = 200
            tree_response.json.return_value = {
                "tree": [
                    {"path": "README.md", "type": "blob", "size": 100, "sha": "abc123"},
                    {"path": "image.png", "type": "blob", "size": 5000, "sha": "def456"},
                    {"path": "src/app.py", "type": "blob", "size": 500, "sha": "ghi789"},
                    {"path": "node_modules/pkg/index.js", "type": "blob", "size": 200, "sha": "jkl012"},
                ]
            }
            
            # Mock file content responses
            import base64
            readme_content = "# Test Project"
            app_content = "def main(): pass"
            
            readme_response = Mock()
            readme_response.status_code = 200
            readme_response.json.return_value = {
                "content": base64.b64encode(readme_content.encode()).decode(),
                "size": len(readme_content)
            }
            
            app_response = Mock()
            app_response.status_code = 200
            app_response.json.return_value = {
                "content": base64.b64encode(app_content.encode()).decode(),
                "size": len(app_content)
            }
            
            # Set up mock responses in order
            mock_client.get.side_effect = [
                repo_response,
                tree_response,
                readme_response,
                app_response,
            ]
            
            result = await fetch_repo_contents("https://github.com/owner/repo")
            
            # Should only include non-binary, non-skipped files
            assert len(result) == 2
            paths = [f["path"] for f in result]
            assert "README.md" in paths
            assert "src/app.py" in paths
            assert "image.png" not in paths  # Binary file filtered
            assert "node_modules/pkg/index.js" not in paths  # Skipped pattern
    
    @pytest.mark.asyncio
    async def test_invalid_url_raises_error(self):
        """Test that invalid GitHub URL raises ValueError."""
        with pytest.raises(ValueError, match="GitHub repository URL"):
            await fetch_repo_contents("https://gitlab.com/owner/repo")
    
    @pytest.mark.asyncio
    async def test_empty_repository_raises_error(self):
        """Test that empty repository raises ValueError."""
        with patch('github_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock repository metadata
            repo_response = Mock()
            repo_response.status_code = 200
            repo_response.json.return_value = {"default_branch": "main"}
            
            # Mock empty tree
            tree_response = Mock()
            tree_response.status_code = 200
            tree_response.json.return_value = {"tree": []}
            
            mock_client.get.side_effect = [repo_response, tree_response]
            
            with pytest.raises(ValueError, match="empty"):
                await fetch_repo_contents("https://github.com/owner/repo")
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Test that connection errors are properly raised."""
        with patch('github_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(ConnectionError, match="Failed to connect"):
                await fetch_repo_contents("https://github.com/owner/repo")

# Made with Bob
