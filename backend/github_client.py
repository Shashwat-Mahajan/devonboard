"""
GitHub API client for fetching repository contents.
"""
import os
import re
import base64
from typing import List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# File patterns to skip
SKIP_PATTERNS = [
    r"node_modules/",
    r"\.git/",
    r"__pycache__/",
    r"\.pyc$",
    r"dist/",
    r"build/",
    r"\.env$",
    r"package-lock\.json$",
    r"yarn\.lock$",
]

# Binary file extensions to skip
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".exe", ".dll",
    ".so", ".dylib", ".bin", ".dat", ".db", ".sqlite",
    ".woff", ".woff2", ".ttf", ".eot", ".otf"
}

# Maximum file size (1MB)
MAX_FILE_SIZE = 1024 * 1024


def parse_github_url(url: str) -> tuple[str, str]:
    """
    Parse GitHub URL to extract owner and repository name.
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo)
        
    Raises:
        ValueError: If URL format is invalid
    """
    # Remove trailing slashes and .git extension
    url = url.rstrip("/").replace(".git", "")
    
    # Match GitHub URL patterns
    patterns = [
        r"github\.com/([^/]+)/([^/]+)",
        r"github\.com:([^/]+)/([^/]+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
    
    raise ValueError(f"Invalid GitHub URL format: {url}")


def should_skip_file(path: str) -> bool:
    """
    Check if a file should be skipped based on patterns.
    
    Args:
        path: File path to check
        
    Returns:
        True if file should be skipped, False otherwise
    """
    # Check skip patterns
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, path):
            return True
    
    # Check binary extensions
    _, ext = os.path.splitext(path)
    if ext.lower() in BINARY_EXTENSIONS:
        return True
    
    return False


async def fetch_repo_tree(
    owner: str,
    repo: str,
    client: httpx.AsyncClient
) -> List[Dict[str, Any]]:
    """
    Fetch repository tree from GitHub API.
    
    Args:
        owner: Repository owner
        repo: Repository name
        client: HTTP client
        
    Returns:
        List of file objects from GitHub tree API
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    # Get default branch
    repo_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    response = await client.get(repo_url, headers=headers)
    
    if response.status_code == 404:
        raise ValueError(f"Repository not found: {owner}/{repo}")
    elif response.status_code == 403:
        raise PermissionError("GitHub API rate limit exceeded or access denied")
    
    response.raise_for_status()
    default_branch = response.json().get("default_branch", "main")
    
    # Get repository tree
    tree_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
    response = await client.get(tree_url, headers=headers)
    response.raise_for_status()
    
    return response.json().get("tree", [])


async def fetch_file_content(
    owner: str,
    repo: str,
    path: str,
    client: httpx.AsyncClient
) -> Optional[str]:
    """
    Fetch content of a single file from GitHub.
    
    Args:
        owner: Repository owner
        repo: Repository name
        path: File path in repository
        client: HTTP client
        
    Returns:
        File content as string, or None if content cannot be fetched
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
    
    try:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Check file size
        if data.get("size", 0) > MAX_FILE_SIZE:
            logger.warning(f"File too large, skipping: {path}")
            return None
        
        # Decode base64 content
        content = data.get("content", "")
        if content:
            return base64.b64decode(content).decode("utf-8", errors="ignore")
        
    except Exception as e:
        logger.warning(f"Failed to fetch content for {path}: {str(e)}")
    
    return None


async def fetch_repo_contents(url: str) -> List[Dict[str, Any]]:
    """
    Fetch repository contents from GitHub.
    
    Args:
        url: GitHub repository URL
        
    Returns:
        List of dictionaries containing file paths and contents (top 50 files)
        
    Raises:
        ValueError: If URL is invalid
        PermissionError: If access is denied
    """
    # Parse GitHub URL
    owner, repo = parse_github_url(url)
    logger.info(f"Fetching contents for {owner}/{repo}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch repository tree
        tree = await fetch_repo_tree(owner, repo, client)
        
        # Filter files
        files = []
        for item in tree:
            if item.get("type") != "blob":
                continue
            
            path = item.get("path", "")
            if should_skip_file(path):
                continue
            
            files.append({
                "path": path,
                "size": item.get("size", 0),
                "sha": item.get("sha", "")
            })
        
        # Sort by path and limit to top 50
        files.sort(key=lambda x: x["path"])
        files = files[:50]
        
        # Fetch content for each file
        result = []
        for file_info in files:
            content = await fetch_file_content(owner, repo, file_info["path"], client)
            
            result.append({
                "path": file_info["path"],
                "content": content or "",
                "size": file_info["size"],
                "sha": file_info["sha"]
            })
        
        logger.info(f"Fetched {len(result)} files from {owner}/{repo}")
        return result

# Made with Bob
