"""
GitHub API client for fetching repository contents.
Complete rewrite with repo type detection and smart file selection.
"""
import os
import re
import base64
import asyncio
from typing import Dict, Any, Optional, List
import httpx
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables from .env file in the same directory
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Initialize logger
logger = logging.getLogger(__name__)

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Request timeout in seconds
REQUEST_TIMEOUT = 30.0

# Module-level cache for repository data
_repo_cache: Dict[str, Dict[str, Any]] = {}


def parse_github_url(url: str) -> tuple[str, str]:
    """
    Parse GitHub URL to extract owner and repository name.
    
    Supports formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/tree/main
    - github.com/owner/repo
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo)
        
    Raises:
        ValueError: If URL format is invalid
    """
    if not url or not isinstance(url, str):
        raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
    
    url = url.strip()
    
    if not url:
        raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
    
    # Remove trailing slashes
    url = url.rstrip("/")
    
    # Remove .git extension if present
    if url.endswith(".git"):
        url = url[:-4]
    
    # Remove tree/branch paths (e.g., /tree/main)
    url = re.sub(r'/tree/[^/]+.*$', '', url)
    
    # Pattern to match GitHub URLs
    pattern = r'(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s]+)'
    
    match = re.search(pattern, url, re.IGNORECASE)
    
    if not match:
        raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
    
    owner = match.group(1).strip()
    repo = match.group(2).strip()
    
    if not owner or not repo:
        raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
    
    return owner, repo


def detect_language(file_paths: List[str]) -> str:
    """Detect primary programming language from file extensions."""
    extensions = {}
    for p in file_paths:
        ext = p.rsplit('.', 1)[-1].lower() if '.' in p else ''
        if ext in ['js', 'ts', 'jsx', 'tsx', 'py', 'java',
                   'go', 'rs', 'rb', 'php', 'cs', 'cpp', 'c']:
            extensions[ext] = extensions.get(ext, 0) + 1
    
    if not extensions:
        return 'Unknown'
    
    primary = max(extensions, key=extensions.get)
    mapping = {
        'js': 'JavaScript', 'ts': 'TypeScript',
        'jsx': 'JavaScript/React', 'tsx': 'TypeScript/React',
        'py': 'Python', 'java': 'Java', 'go': 'Go',
        'rs': 'Rust', 'rb': 'Ruby', 'php': 'PHP',
        'cs': 'C#', 'cpp': 'C++', 'c': 'C'
    }
    return mapping.get(primary, primary.upper())


def detect_framework(file_paths: List[str]) -> str:
    """Detect framework from file paths and names."""
    paths_str = ' '.join(file_paths).lower()
    
    frameworks = {
        'Next.js': ['next.config', 'pages/_app', 'app/page'],
        'React': ['react', '.jsx', '.tsx'],
        'Vue': ['vue.config', '.vue'],
        'Angular': ['angular.json', 'ng-'],
        'Express': ['express', 'router'],
        'FastAPI': ['fastapi', '@app.get', '@router'],
        'Django': ['django', 'settings.py', 'urls.py'],
        'Flask': ['flask', '@app.route'],
        'Spring': ['spring', 'application.properties'],
        'Rails': ['gemfile', 'routes.rb'],
        'Laravel': ['artisan', 'composer.json']
    }
    
    for fw, indicators in frameworks.items():
        if any(ind in paths_str for ind in indicators):
            return fw
    
    return 'Unknown'


def detect_repo_type(file_paths: List[str]) -> Dict[str, Any]:
    """
    Detect repository type by scanning all file paths.
    Returns dict with has_frontend, has_backend, has_database, has_auth, has_tests, language, framework.
    """
    paths_str = ' '.join(file_paths).lower()
    
    return {
        'has_frontend': any(x in paths_str for x in [
            'react', 'vue', 'angular', 'next', 'nuxt',
            'jsx', 'tsx', 'html', 'css', 'component'
        ]),
        'has_backend': any(x in paths_str for x in [
            'server', 'app.py', 'main.py', 'index.js',
            'app.js', 'django', 'flask', 'fastapi',
            'express', 'spring', 'rails', 'api', 'route'
        ]),
        'has_database': any(x in paths_str for x in [
            'model', 'schema', 'migration', 'mongoose',
            'sequelize', 'prisma', 'sqlalchemy', 'entity',
            'database', 'db'
        ]),
        'has_auth': any(x in paths_str for x in [
            'auth', 'login', 'jwt', 'passport', 'oauth',
            'session', 'middleware', 'guard', 'token'
        ]),
        'has_tests': any(x in paths_str for x in [
            'test', 'spec', '__test__', 'jest', 'pytest'
        ]),
        'language': detect_language(file_paths),
        'framework': detect_framework(file_paths)
    }


async def _fetch_single_file(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    path: str,
    headers: Dict[str, str],
    size: int = 0,
    priority: int = 4,
    category: str = "other"
) -> Optional[Dict[str, Any]]:
    """
    Fetch a single file's content from GitHub API with metadata.
    
    Returns:
        Dictionary with path, content (up to 8000 chars), size, priority, category
    """
    content_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
    
    try:
        content_response = await client.get(content_url, headers=headers)
        
        if content_response.status_code == 200:
            content_data = content_response.json()
            encoded_content = content_data.get("content", "")
            
            if encoded_content:
                try:
                    # Decode base64 content
                    decoded = base64.b64decode(encoded_content)
                    text_content = decoded.decode("utf-8", errors="ignore")
                    
                    # Limit to 8000 chars
                    text_content = text_content[:8000]
                    
                    logger.info(f"Fetched {path} (priority={priority}, category={category})")
                    return {
                        "path": path,
                        "content": text_content,
                        "size": size,
                        "priority": priority,
                        "category": category
                    }
                except Exception as e:
                    logger.warning(f"Failed to decode {path}: {e}")
    except Exception as e:
        logger.warning(f"Failed to fetch {path}: {e}")
    
    return None


async def fetch_repo_data(url: str) -> Dict[str, Any]:
    """
    Fetch repository data with smart file selection based on repo type detection.
    
    Returns:
        {
            "owner": str,
            "repo": str,
            "description": str,
            "stars": int,
            "language": str,
            "files": [{"path": str, "content": str, "priority": int, "category": str}],
            "file_count": int,
            "repo_type": dict  # Detection results
        }
    """
    # Parse GitHub URL
    try:
        owner, repo = parse_github_url(url)
    except ValueError as e:
        raise ValueError(str(e))
    
    # Check cache first
    cache_key = f"{owner}/{repo}"
    if cache_key in _repo_cache:
        logger.info(f"Returning cached data for {cache_key}")
        return _repo_cache[cache_key]
    
    logger.info(f"Fetching repository data for {owner}/{repo}")
    
    # Set up headers
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DevOnboard-App"
    }
    
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
        logger.info("Using GitHub token for authentication")
    else:
        logger.warning("No GitHub token found - rate limits will be lower")
    
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            # Step 1: Get repository metadata
            repo_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
            
            try:
                response = await client.get(repo_url, headers=headers)
            except (httpx.ConnectError, httpx.TimeoutException):
                raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
            
            # Handle HTTP errors
            if response.status_code == 401:
                raise PermissionError("Invalid GitHub token. Check your GITHUB_TOKEN in .env")
            elif response.status_code == 403:
                raise PermissionError("GitHub API rate limit exceeded. Add a GITHUB_TOKEN to .env")
            elif response.status_code == 404:
                raise ValueError("Repository not found. Check the URL and make sure it is public")
            
            response.raise_for_status()
            repo_data = response.json()
            
            # Extract repository metadata
            description = repo_data.get("description", "")
            stars = repo_data.get("stargazers_count", 0)
            language = repo_data.get("language", "")
            default_branch = repo_data.get("default_branch", "main")
            
            # Step 2: Get repository file tree
            tree_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
            
            try:
                response = await client.get(tree_url, headers=headers)
            except (httpx.ConnectError, httpx.TimeoutException):
                raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
            
            if response.status_code == 401:
                raise PermissionError("Invalid GitHub token. Check your GITHUB_TOKEN in .env")
            elif response.status_code == 403:
                raise PermissionError("GitHub API rate limit exceeded. Add a GITHUB_TOKEN to .env")
            elif response.status_code == 404:
                raise ValueError("Repository not found. Check the URL and make sure it is public")
            
            response.raise_for_status()
            tree_data = response.json()
            
            tree = tree_data.get("tree", [])
            
            if not tree:
                raise ValueError("Repository appears to be empty")
            
            # Step 3: Detect repo type
            all_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
            repo_type = detect_repo_type(all_paths)
            
            logger.info(f"Detected: {repo_type['language']}, {repo_type['framework']}, "
                       f"auth={repo_type['has_auth']}, db={repo_type['has_database']}")
            
            # Step 4: Smart file selection
            files_to_fetch = []
            file_count = 0
            
            # Priority 1 - Config files (always fetch)
            config_files = [
                "README.md", "README.rst", "package.json", "requirements.txt",
                "setup.py", "setup.cfg", "pyproject.toml", "pom.xml",
                "build.gradle", "Cargo.toml", "go.mod", "composer.json",
                "Gemfile", ".env.example", "docker-compose.yml", "Dockerfile"
            ]
            
            for item in tree:
                if item.get("type") != "blob":
                    continue
                
                file_count += 1
                path = item.get("path", "")
                size = item.get("size", 0)
                filename = path.split("/")[-1]
                path_lower = path.lower()
                
                if filename in config_files:
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 1, "category": "config"
                    })
            
            # Priority 2 - Entry points
            entry_points = {
                "index.js": "entry", "index.ts": "entry", "app.js": "entry",
                "app.ts": "entry", "server.js": "entry", "server.ts": "entry",
                "main.js": "entry", "main.ts": "entry", "main.py": "entry",
                "app.py": "entry", "server.py": "entry", "wsgi.py": "entry",
                "asgi.py": "entry", "Main.java": "entry", "Application.java": "entry",
                "main.go": "entry"
            }
            
            for item in tree:
                if item.get("type") != "blob":
                    continue
                path = item.get("path", "")
                size = item.get("size", 0)
                filename = path.split("/")[-1]
                
                if filename in entry_points and not any(f["path"] == path for f in files_to_fetch):
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 2, "category": entry_points[filename]
                    })
                    break  # Only first match
            
            # Priority 3 - Based on detected repo type
            for item in tree:
                if item.get("type") != "blob":
                    continue
                path = item.get("path", "")
                size = item.get("size", 0)
                path_lower = path.lower()
                
                if any(f["path"] == path for f in files_to_fetch):
                    continue
                
                # Auth files
                if repo_type['has_auth'] and any(kw in path_lower for kw in [
                    'auth', 'login', 'jwt', 'passport', 'middleware',
                    'guard', 'permission', 'session', 'oauth', 'token'
                ]):
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 3, "category": "auth"
                    })
                
                # Database/Model files
                elif repo_type['has_database'] and any(kw in path_lower for kw in [
                    'model', 'schema', 'entity', 'migration', 'repository', 'dao'
                ]):
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 3, "category": "database"
                    })
                
                # Route files
                elif repo_type['has_backend'] and any(kw in path_lower for kw in [
                    'route', 'router', 'controller', 'handler', 'endpoint', 'api', 'view'
                ]):
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 3, "category": "route"
                    })
                
                # Component files
                elif repo_type['has_frontend'] and any(kw in path_lower for kw in [
                    'page', 'component', 'screen', 'layout', 'store', 'context', 'hook'
                ]):
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 3, "category": "component"
                    })
            
            # Priority 4 - Fill remaining slots (up to 40 total)
            exclude_patterns = ['test', 'spec', '__test__', '.test.', 'dist/', 
                              'build/', 'node_modules', '__pycache__', '.git']
            
            for item in tree:
                if len(files_to_fetch) >= 40:
                    break
                
                if item.get("type") != "blob":
                    continue
                
                path = item.get("path", "")
                size = item.get("size", 0)
                path_lower = path.lower()
                
                if any(f["path"] == path for f in files_to_fetch):
                    continue
                
                # Skip excluded patterns
                if any(ex in path_lower for ex in exclude_patterns):
                    continue
                
                # Prefer files in root, src/, app/, lib/
                folder = path.split("/")[0] if "/" in path else ""
                if folder in ["", "src", "app", "lib"] or "/" not in path:
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 4, "category": "other"
                    })
            
            logger.info(f"Selected {len(files_to_fetch)} files to fetch (out of {file_count} total)")
            
            # Step 5: Fetch all files in parallel
            fetch_tasks = [
                _fetch_single_file(
                    client, owner, repo,
                    f["path"], headers, f["size"], f["priority"], f["category"]
                )
                for f in files_to_fetch
            ]
            
            results = await asyncio.gather(*fetch_tasks, return_exceptions=False)
            files = [r for r in results if r is not None]
            
            logger.info(f"Successfully fetched {len(files)} files with full content")
            
            # Prepare result
            result = {
                "owner": owner,
                "repo": repo,
                "description": description,
                "stars": stars,
                "language": language,
                "files": files,
                "file_count": file_count,
                "repo_type": repo_type
            }
            
            # Cache the result
            _repo_cache[cache_key] = result
            
            return result
            
    except (httpx.ConnectError, httpx.TimeoutException):
        raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
    except (ValueError, PermissionError, ConnectionError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise ConnectionError(f"Failed to fetch repository data: {str(e)}")


# Made with Bob
