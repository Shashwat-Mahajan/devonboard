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

# Load environment variables from .env file (for GITHUB_TOKEN)
load_dotenv()

# Initialize logger for tracking GitHub API interactions
logger = logging.getLogger(__name__)

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"  # Base URL for GitHub REST API
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Optional token for higher rate limits

# File patterns to skip (common directories and files that shouldn't be analyzed)
SKIP_PATTERNS = [
    r"node_modules/",  # Node.js dependencies
    r"\.git/",  # Git metadata
    r"__pycache__/",  # Python bytecode cache
    r"\.pyc$",  # Python compiled files
    r"dist/",  # Distribution/build output
    r"build/",  # Build artifacts
    r"\.env$",  # Environment variables (sensitive)
    r"package-lock\.json$",  # Node.js lock file (too large)
    r"yarn\.lock$",  # Yarn lock file (too large)
]

# Binary file extensions to skip (cannot be analyzed as text)
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",  # Images
    ".pdf", ".zip", ".tar", ".gz", ".exe", ".dll",  # Archives and executables
    ".so", ".dylib", ".bin", ".dat", ".db", ".sqlite",  # Binary data
    ".woff", ".woff2", ".ttf", ".eot", ".otf"  # Fonts
}

# Maximum file size (1MB) - larger files are skipped to prevent memory issues
MAX_FILE_SIZE = 1024 * 1024

# Maximum number of files to fetch (prevent memory exhaustion on large repos)
MAX_FILES = 100

# Request timeout in seconds (prevent hanging on slow connections)
REQUEST_TIMEOUT = 60.0

# Maximum retries for transient errors (network issues, temporary API failures)
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
    # Validate input is a non-empty string
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
    
    # Strip whitespace from both ends
    url = url.strip()
    
    # Check for empty string after stripping
    if not url:
        raise ValueError("URL cannot be empty or whitespace")
    
    # Check if it's a GitHub URL (basic validation)
    if "github.com" not in url.lower():
        raise ValueError("URL must be a GitHub repository URL")
    
    # Remove trailing slashes and .git extension for normalization
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    
    # Match GitHub URL patterns (support various formats)
    # Pattern 1: HTTPS URLs (with or without www)
    # Pattern 2: SSH URLs (git@github.com:owner/repo)
    patterns = [
        r"(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s]+)",
        r"git@github\.com:([^/\s]+)/([^/\s]+)",
    ]
    
    # Try each pattern to extract owner and repo
    for pattern in patterns:
        try:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                owner = match.group(1).strip()
                repo = match.group(2).strip()
                
                # Validate owner and repo names are not empty
                if not owner or not repo:
                    continue
                
                # Check for invalid characters (only allow word chars, hyphens, dots)
                if not re.match(r'^[\w\-\.]+$', owner) or not re.match(r'^[\w\-\.]+$', repo):
                    raise ValueError(f"Invalid characters in owner or repository name")
                
                return owner, repo
        except re.error as e:
            logger.warning(f"Regex error parsing URL: {e}")
            continue
    
    # No pattern matched
    raise ValueError(f"Invalid GitHub URL format: {url}")


def should_skip_file(path: str) -> bool:
    """
    Check if a file should be skipped based on patterns.
    
    Args:
        path: File path to check
        
    Returns:
        True if file should be skipped, False otherwise
    """
    # Validate path is a non-empty string
    if not path or not isinstance(path, str):
        return True
    
    # Normalize path separators to forward slashes
    path = path.replace("\\", "/")
    
    # Check for symlinks or circular references (basic security check)
    # Paths with ".." could traverse outside repository
    if ".." in path or path.startswith("/"):
        logger.warning(f"Suspicious path detected: {path}")
        return True
    
    # Check skip patterns with error handling
    try:
        for pattern in SKIP_PATTERNS:
            # If path matches any skip pattern, skip it
            if re.search(pattern, path):
                return True
    except re.error as e:
        logger.warning(f"Regex error checking path {path}: {e}")
        return True  # Skip on error to be safe
    
    # Check binary extensions (files we can't analyze as text)
    try:
        _, ext = os.path.splitext(path)
        if ext.lower() in BINARY_EXTENSIONS:
            return True
    except Exception as e:
        logger.warning(f"Error checking file extension for {path}: {e}")
        return True  # Skip on error to be safe
    
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
    # Set up headers for GitHub API request
    headers = {
        "Accept": "application/vnd.github.v3+json",  # Request GitHub API v3 format
    }
    # Add authentication token if available (increases rate limits)
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    # Retry logic for transient errors (network issues, temporary API failures)
    for attempt in range(MAX_RETRIES):
        try:
            # Step 1: Get repository metadata to find default branch
            repo_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
            
            try:
                response = await client.get(repo_url, headers=headers, timeout=REQUEST_TIMEOUT)
            except httpx.TimeoutException:
                # Retry with exponential backoff on timeout
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                    continue
                raise TimeoutError(f"Request timed out after {REQUEST_TIMEOUT} seconds")
            except httpx.ConnectError as e:
                # Retry on connection errors
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise ConnectionError(f"Failed to connect to GitHub API: {str(e)}")
            
            # Handle specific HTTP status codes
            if response.status_code == 404:
                # Repository doesn't exist or is private
                raise ValueError(f"Repository not found: {owner}/{repo}")
            elif response.status_code == 403:
                # Rate limit or access denied
                error_msg = "GitHub API rate limit exceeded or access denied"
                try:
                    error_data = response.json()
                    if "rate limit" in str(error_data).lower():
                        error_msg = "GitHub API rate limit exceeded. Please provide a GitHub token or try again later."
                except:
                    pass
                raise PermissionError(error_msg)
            elif response.status_code == 429:
                # Too many requests
                raise PermissionError("GitHub API rate limit exceeded. Please try again later.")
            
            # Raise exception for other HTTP errors
            response.raise_for_status()
            repo_data = response.json()
            # Extract default branch (usually "main" or "master")
            default_branch = repo_data.get("default_branch", "main")
            
            # Step 2: Get repository tree (all files recursively)
            tree_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
            
            try:
                response = await client.get(tree_url, headers=headers, timeout=REQUEST_TIMEOUT)
            except httpx.TimeoutException:
                # Retry with exponential backoff on timeout
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise TimeoutError(f"Request timed out after {REQUEST_TIMEOUT} seconds")
            except httpx.ConnectError as e:
                # Retry on connection errors
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise ConnectionError(f"Failed to connect to GitHub API: {str(e)}")
            
            # Handle rate limiting
            if response.status_code == 429:
                raise PermissionError("GitHub API rate limit exceeded. Please try again later.")
            
            # Raise exception for other HTTP errors
            response.raise_for_status()
            tree_data = response.json()
            
            # Return list of files from tree
            return tree_data.get("tree", [])
            
        except (TimeoutError, ValueError, PermissionError, ConnectionError):
            # Don't retry these errors (they're not transient)
            raise
        except Exception as e:
            # Retry on unexpected errors
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}, retrying...")
                await asyncio.sleep(2 ** attempt)
                continue
            raise
    
    # All retries exhausted
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
    # Validate path is a non-empty string
    if not path or not isinstance(path, str):
        logger.warning("Invalid file path")
        return None
    
    # Set up headers for GitHub API request
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    # URL encode the path to handle special characters (spaces, etc.)
    try:
        from urllib.parse import quote
        encoded_path = quote(path, safe='/')  # Keep forward slashes unencoded
    except Exception as e:
        logger.warning(f"Failed to encode path {path}: {e}")
        return None
    
    # Build URL for file contents endpoint
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{encoded_path}"
    
    try:
        # Fetch file content from GitHub
        response = await client.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        
        # Handle rate limiting gracefully (don't fail entire operation)
        if response.status_code == 429:
            logger.warning(f"Rate limited while fetching {path}")
            return None
        
        # Raise exception for other HTTP errors
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # Validate response structure is a dictionary
        if not isinstance(data, dict):
            logger.warning(f"Unexpected response format for {path}")
            return None
        
        # Check file size to prevent memory issues
        file_size = data.get("size", 0)
        if not isinstance(file_size, (int, float)) or file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large ({file_size} bytes), skipping: {path}")
            return None
        
        # Extract base64-encoded content from response
        content = data.get("content", "")
        if not content:
            return None
        
        try:
            # Decode base64 content to bytes
            decoded = base64.b64decode(content)
            
            # Try UTF-8 decoding with error handling
            try:
                # Attempt strict UTF-8 decoding
                text_content = decoded.decode("utf-8")
            except UnicodeDecodeError:
                # Fallback: ignore invalid UTF-8 characters for binary-like files
                text_content = decoded.decode("utf-8", errors="ignore")
            
            # Check for binary content (null bytes indicate binary data)
            if '\x00' in text_content:
                logger.warning(f"Binary content detected in {path}")
                return None
            
            return text_content
            
        except Exception as e:
            logger.warning(f"Failed to decode content for {path}: {str(e)}")
            return None
        
    except httpx.TimeoutException:
        # Timeout is not fatal, just skip this file
        logger.warning(f"Timeout fetching content for {path}")
        return None
    except httpx.HTTPStatusError as e:
        # HTTP errors are not fatal, just skip this file
        logger.warning(f"HTTP error fetching {path}: {e.response.status_code}")
        return None
    except Exception as e:
        # Catch-all for unexpected errors
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
        # Create async HTTP client with timeout
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            # Step 1: Fetch repository tree (list of all files)
            try:
                tree = await fetch_repo_tree(owner, repo, client)
            except (ValueError, PermissionError, TimeoutError, ConnectionError) as e:
                logger.error(f"Failed to fetch repository tree: {str(e)}")
                raise
            
            # Validate tree is a non-empty list
            if not tree or not isinstance(tree, list):
                raise ValueError(f"Repository {owner}/{repo} appears to be empty or inaccessible")
            
            # Step 2: Filter files with validation
            files = []
            seen_paths = set()  # Track duplicates (shouldn't happen but defensive)
            
            for item in tree:
                # Skip invalid items
                if not item or not isinstance(item, dict):
                    continue
                
                # Only process blob (file) types, skip trees (directories)
                if item.get("type") != "blob":
                    continue
                
                # Extract and validate path
                path = item.get("path", "")
                if not path or not isinstance(path, str):
                    continue
                
                # Skip duplicates (defensive programming)
                if path in seen_paths:
                    logger.warning(f"Duplicate path in tree: {path}")
                    continue
                seen_paths.add(path)
                
                # Apply skip filters (node_modules, .git, binaries, etc.)
                if should_skip_file(path):
                    continue
                
                # Validate size is a valid number
                size = item.get("size", 0)
                if not isinstance(size, (int, float)) or size < 0:
                    logger.warning(f"Invalid size for {path}: {size}")
                    continue
                
                # Skip files that are too large
                if size > MAX_FILE_SIZE:
                    logger.info(f"Skipping large file: {path} ({size} bytes)")
                    continue
                
                # Add file to list
                files.append({
                    "path": path,
                    "size": size,
                    "sha": item.get("sha", "")  # Git SHA hash
                })
            
            # Validate we have at least some files
            if not files:
                raise ValueError(f"No valid files found in repository {owner}/{repo}")
            
            # Check for very large repositories and limit if needed
            if len(files) > MAX_FILES:
                logger.warning(f"Repository has {len(files)} files, limiting to {MAX_FILES}")
                # Sort by path and limit to prevent memory exhaustion
                files.sort(key=lambda x: x["path"])
                files = files[:MAX_FILES]
            else:
                # Sort by path for consistent ordering
                files.sort(key=lambda x: x["path"])
            
            logger.info(f"Processing {len(files)} files from {owner}/{repo}")
            
            # Step 3: Fetch content for each file with progress tracking
            result = []
            failed_count = 0
            
            for i, file_info in enumerate(files):
                try:
                    # Fetch individual file content
                    content = await fetch_file_content(owner, repo, file_info["path"], client)
                    
                    # Add file with content to result
                    result.append({
                        "path": file_info["path"],
                        "content": content if content is not None else "",  # Empty string if fetch failed
                        "size": file_info["size"],
                        "sha": file_info["sha"]
                    })
                    
                    # Log progress for large repos (every 10 files)
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(files)} files")
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch content for {file_info['path']}: {str(e)}")
                    failed_count += 1
                    # Add file with empty content rather than failing completely
                    # This allows partial success for large repos
                    result.append({
                        "path": file_info["path"],
                        "content": "",
                        "size": file_info["size"],
                        "sha": file_info["sha"]
                    })
            
            # Log warning if some files failed
            if failed_count > 0:
                logger.warning(f"Failed to fetch content for {failed_count} files")
            
            # Validate we got at least some results
            if not result:
                raise ValueError(f"Failed to fetch any file contents from {owner}/{repo}")
            
            logger.info(f"Successfully fetched {len(result)} files from {owner}/{repo}")
            return result
            
    except httpx.TimeoutException:
        # Handle timeout errors
        raise TimeoutError(f"Request timed out while fetching repository contents")
    except httpx.ConnectError as e:
        # Handle connection errors
        raise ConnectionError(f"Failed to connect to GitHub API: {str(e)}")
    except (ValueError, PermissionError, TimeoutError, ConnectionError):
        # Re-raise these as-is (already properly formatted)
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error fetching repository contents: {str(e)}", exc_info=True)
        raise ConnectionError(f"Failed to fetch repository contents: {str(e)}")

# Made with Bob
