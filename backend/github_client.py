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
import asyncio

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

# Maximum number of files to fetch (prevent memory exhaustion)
MAX_FILES = 100

# Request timeout in seconds
REQUEST_TIMEOUT = 60.0

# Maximum retries for transient errors
MAX_RETRIES = 3


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
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
    
    # Strip whitespace
    url = url.strip()
    
    if not url:
        raise ValueError("URL cannot be empty or whitespace")
    
    # Check if it's a GitHub URL
    if "github.com" not in url.lower():
        raise ValueError("URL must be a GitHub repository URL")
    
    # Remove trailing slashes and .git extension
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    
    # Match GitHub URL patterns (support various formats)
    patterns = [
        r"(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s]+)",
        r"git@github\.com:([^/\s]+)/([^/\s]+)",
    ]
    
    for pattern in patterns:
        try:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                owner = match.group(1).strip()
                repo = match.group(2).strip()
                
                # Validate owner and repo names
                if not owner or not repo:
                    continue
                
                # Check for invalid characters
                if not re.match(r'^[\w\-\.]+$', owner) or not re.match(r'^[\w\-\.]+$', repo):
                    raise ValueError(f"Invalid characters in owner or repository name")
                
                return owner, repo
        except re.error as e:
            logger.warning(f"Regex error parsing URL: {e}")
            continue
    
    raise ValueError(f"Invalid GitHub URL format: {url}")


def should_skip_file(path: str) -> bool:
    """
    Check if a file should be skipped based on patterns.
    
    Args:
        path: File path to check
        
    Returns:
        True if file should be skipped, False otherwise
    """
    if not path or not isinstance(path, str):
        return True
    
    # Normalize path separators
    path = path.replace("\\", "/")
    
    # Check for symlinks or circular references (basic check)
    if ".." in path or path.startswith("/"):
        logger.warning(f"Suspicious path detected: {path}")
        return True
    
    # Check skip patterns with error handling
    try:
        for pattern in SKIP_PATTERNS:
            if re.search(pattern, path):
                return True
    except re.error as e:
        logger.warning(f"Regex error checking path {path}: {e}")
        return True
    
    # Check binary extensions
    try:
        _, ext = os.path.splitext(path)
        if ext.lower() in BINARY_EXTENSIONS:
            return True
    except Exception as e:
        logger.warning(f"Error checking file extension for {path}: {e}")
        return True
    
    return False


async def fetch_repo_tree(
    owner: str,
    repo: str,
    client: httpx.AsyncClient
) -> List[Dict[str, Any]]:
    """
    Fetch repository tree from GitHub API with retry logic.
    
    Args:
        owner: Repository owner
        repo: Repository name
        client: HTTP client
        
    Returns:
        List of file objects from GitHub tree API
        
    Raises:
        ValueError: If repository not found
        PermissionError: If access denied or rate limited
        TimeoutError: If request times out
        ConnectionError: If network error occurs
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    # Retry logic for transient errors
    for attempt in range(MAX_RETRIES):
        try:
            # Get default branch
            repo_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
            
            try:
                response = await client.get(repo_url, headers=headers, timeout=REQUEST_TIMEOUT)
            except httpx.TimeoutException:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise TimeoutError(f"Request timed out after {REQUEST_TIMEOUT} seconds")
            except httpx.ConnectError as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise ConnectionError(f"Failed to connect to GitHub API: {str(e)}")
            
            if response.status_code == 404:
                raise ValueError(f"Repository not found: {owner}/{repo}")
            elif response.status_code == 403:
                error_msg = "GitHub API rate limit exceeded or access denied"
                try:
                    error_data = response.json()
                    if "rate limit" in str(error_data).lower():
                        error_msg = "GitHub API rate limit exceeded. Please provide a GitHub token or try again later."
                except:
                    pass
                raise PermissionError(error_msg)
            elif response.status_code == 429:
                raise PermissionError("GitHub API rate limit exceeded. Please try again later.")
            
            response.raise_for_status()
            repo_data = response.json()
            default_branch = repo_data.get("default_branch", "main")
            
            # Get repository tree
            tree_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
            
            try:
                response = await client.get(tree_url, headers=headers, timeout=REQUEST_TIMEOUT)
            except httpx.TimeoutException:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise TimeoutError(f"Request timed out after {REQUEST_TIMEOUT} seconds")
            except httpx.ConnectError as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise ConnectionError(f"Failed to connect to GitHub API: {str(e)}")
            
            if response.status_code == 429:
                raise PermissionError("GitHub API rate limit exceeded. Please try again later.")
            
            response.raise_for_status()
            tree_data = response.json()
            
            return tree_data.get("tree", [])
            
        except (TimeoutError, ValueError, PermissionError, ConnectionError):
            # Don't retry these errors
            raise
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}, retrying...")
                await asyncio.sleep(2 ** attempt)
                continue
            raise
    
    raise ConnectionError("Failed to fetch repository tree after multiple attempts")


async def fetch_file_content(
    owner: str,
    repo: str,
    path: str,
    client: httpx.AsyncClient
) -> Optional[str]:
    """
    Fetch content of a single file from GitHub with error handling.
    
    Args:
        owner: Repository owner
        repo: Repository name
        path: File path in repository
        client: HTTP client
        
    Returns:
        File content as string, or None if content cannot be fetched
    """
    if not path or not isinstance(path, str):
        logger.warning("Invalid file path")
        return None
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    # URL encode the path to handle special characters
    try:
        from urllib.parse import quote
        encoded_path = quote(path, safe='/')
    except Exception as e:
        logger.warning(f"Failed to encode path {path}: {e}")
        return None
    
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{encoded_path}"
    
    try:
        response = await client.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        
        # Handle rate limiting
        if response.status_code == 429:
            logger.warning(f"Rate limited while fetching {path}")
            return None
        
        response.raise_for_status()
        
        data = response.json()
        
        # Validate response structure
        if not isinstance(data, dict):
            logger.warning(f"Unexpected response format for {path}")
            return None
        
        # Check file size
        file_size = data.get("size", 0)
        if not isinstance(file_size, (int, float)) or file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large ({file_size} bytes), skipping: {path}")
            return None
        
        # Decode base64 content
        content = data.get("content", "")
        if not content:
            return None
        
        try:
            # Decode base64
            decoded = base64.b64decode(content)
            
            # Try UTF-8 decoding with error handling
            try:
                text_content = decoded.decode("utf-8")
            except UnicodeDecodeError:
                # Try with errors='ignore' for binary-like files
                text_content = decoded.decode("utf-8", errors="ignore")
            
            # Check for binary content (null bytes)
            if '\x00' in text_content:
                logger.warning(f"Binary content detected in {path}")
                return None
            
            return text_content
            
        except Exception as e:
            logger.warning(f"Failed to decode content for {path}: {str(e)}")
            return None
        
    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching content for {path}")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error fetching {path}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.warning(f"Failed to fetch content for {path}: {str(e)}")
        return None


async def fetch_repo_contents(url: str) -> List[Dict[str, Any]]:
    """
    Fetch repository contents from GitHub with comprehensive error handling.
    
    Args:
        url: GitHub repository URL
        
    Returns:
        List of dictionaries containing file paths and contents
        
    Raises:
        ValueError: If URL is invalid or repository is empty
        PermissionError: If access is denied or rate limited
        TimeoutError: If request times out
        ConnectionError: If network error occurs
    """
    # Parse GitHub URL with validation
    try:
        owner, repo = parse_github_url(url)
    except ValueError as e:
        logger.error(f"Invalid GitHub URL: {str(e)}")
        raise
    
    logger.info(f"Fetching contents for {owner}/{repo}")
    
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            # Fetch repository tree
            try:
                tree = await fetch_repo_tree(owner, repo, client)
            except (ValueError, PermissionError, TimeoutError, ConnectionError) as e:
                logger.error(f"Failed to fetch repository tree: {str(e)}")
                raise
            
            if not tree or not isinstance(tree, list):
                raise ValueError(f"Repository {owner}/{repo} appears to be empty or inaccessible")
            
            # Filter files with validation
            files = []
            seen_paths = set()  # Track duplicates
            
            for item in tree:
                if not item or not isinstance(item, dict):
                    continue
                
                # Only process blob (file) types, skip trees (directories)
                if item.get("type") != "blob":
                    continue
                
                path = item.get("path", "")
                if not path or not isinstance(path, str):
                    continue
                
                # Skip duplicates
                if path in seen_paths:
                    logger.warning(f"Duplicate path in tree: {path}")
                    continue
                seen_paths.add(path)
                
                # Apply skip filters
                if should_skip_file(path):
                    continue
                
                # Validate size
                size = item.get("size", 0)
                if not isinstance(size, (int, float)) or size < 0:
                    logger.warning(f"Invalid size for {path}: {size}")
                    continue
                
                if size > MAX_FILE_SIZE:
                    logger.info(f"Skipping large file: {path} ({size} bytes)")
                    continue
                
                files.append({
                    "path": path,
                    "size": size,
                    "sha": item.get("sha", "")
                })
            
            if not files:
                raise ValueError(f"No valid files found in repository {owner}/{repo}")
            
            # Check for very large repositories
            if len(files) > MAX_FILES:
                logger.warning(f"Repository has {len(files)} files, limiting to {MAX_FILES}")
                # Sort by path and limit
                files.sort(key=lambda x: x["path"])
                files = files[:MAX_FILES]
            else:
                # Sort by path
                files.sort(key=lambda x: x["path"])
            
            logger.info(f"Processing {len(files)} files from {owner}/{repo}")
            
            # Fetch content for each file with progress tracking
            result = []
            failed_count = 0
            
            for i, file_info in enumerate(files):
                try:
                    content = await fetch_file_content(owner, repo, file_info["path"], client)
                    
                    result.append({
                        "path": file_info["path"],
                        "content": content if content is not None else "",
                        "size": file_info["size"],
                        "sha": file_info["sha"]
                    })
                    
                    # Log progress for large repos
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(files)} files")
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch content for {file_info['path']}: {str(e)}")
                    failed_count += 1
                    # Add file with empty content rather than failing completely
                    result.append({
                        "path": file_info["path"],
                        "content": "",
                        "size": file_info["size"],
                        "sha": file_info["sha"]
                    })
            
            if failed_count > 0:
                logger.warning(f"Failed to fetch content for {failed_count} files")
            
            if not result:
                raise ValueError(f"Failed to fetch any file contents from {owner}/{repo}")
            
            logger.info(f"Successfully fetched {len(result)} files from {owner}/{repo}")
            return result
            
    except httpx.TimeoutException:
        raise TimeoutError(f"Request timed out while fetching repository contents")
    except httpx.ConnectError as e:
        raise ConnectionError(f"Failed to connect to GitHub API: {str(e)}")
    except (ValueError, PermissionError, TimeoutError, ConnectionError):
        # Re-raise these as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching repository contents: {str(e)}", exc_info=True)
        raise ConnectionError(f"Failed to fetch repository contents: {str(e)}")

# Made with Bob
