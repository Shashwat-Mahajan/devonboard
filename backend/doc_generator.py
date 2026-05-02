"""
Documentation generator for creating onboarding documents from repository data.
"""
import os
import re
from typing import Dict, Any, List, Optional
import logging
import json

# Initialize logger for tracking documentation generation process
logger = logging.getLogger(__name__)

# Maximum path length to prevent filesystem issues and path traversal attacks
MAX_PATH_LENGTH = 4096


def normalize_path(path: str) -> str:
    """
    Normalize file path to use forward slashes and handle edge cases.
    
    Args:
        path: File path to normalize
        
    Returns:
        Normalized path with forward slashes
    """
    # Handle empty or None paths
    if not path:
        return ""
    
    # Replace backslashes with forward slashes for cross-platform consistency
    # Windows uses backslashes, but forward slashes work universally
    normalized = path.replace("\\", "/")
    
    # Remove duplicate slashes (e.g., "path//to///file" -> "path/to/file")
    normalized = re.sub(r'/+', '/', normalized)
    
    # Validate path length to prevent buffer overflow and filesystem issues
    if len(normalized) > MAX_PATH_LENGTH:
        logger.warning(f"Path exceeds maximum length: {normalized[:100]}...")
        # Truncate to maximum allowed length
        normalized = normalized[:MAX_PATH_LENGTH]
    
    return normalized


def safe_get_content(file_dict: Dict[str, Any]) -> Optional[str]:
    """
    Safely extract content from file dictionary with validation.
    
    Args:
        file_dict: File dictionary that may contain content
        
    Returns:
        File content as string or None if invalid
    """
    # Validate input is a dictionary
    if not file_dict or not isinstance(file_dict, dict):
        return None
    
    # Extract content field from dictionary
    content = file_dict.get("content")
    
    # Handle None or empty content (file might be empty or content not fetched)
    if content is None or content == "":
        return None
    
    # Ensure content is a string (handle edge cases where content might be other types)
    if not isinstance(content, str):
        try:
            # Attempt to convert to string
            content = str(content)
        except Exception as e:
            logger.warning(f"Failed to convert content to string: {e}")
            return None
    
    # Check for binary content indicators (null bytes indicate binary data)
    if '\x00' in content:
        logger.warning("Binary content detected, skipping")
        return None
    
    return content


def extract_project_overview(files: List[Dict[str, Any]]) -> str:
    """
    Extract project overview from README and package files.
    
    Args:
        files: List of file dictionaries with path and content
        
    Returns:
        Markdown string with project overview
    """
    # Validate input is a non-empty list
    if not files or not isinstance(files, list) or len(files) == 0:
        return "### Project Overview\n\nNo files available for analysis.\n\n"
    
    # List to accumulate overview sections
    overview_parts = []
    
    # Find and parse README file for project description
    readme_file = None
    for f in files:
        # Skip invalid file entries
        if not f or not isinstance(f, dict):
            continue
        path = normalize_path(f.get("path", ""))
        # Check for common README file names (case-insensitive)
        if path.lower() in ["readme.md", "readme.txt", "readme"]:
            readme_file = f
            break
    
    # Extract description from README if found
    if readme_file:
        content = safe_get_content(readme_file)
        if content:
            try:
                # Extract first paragraph or first 500 characters for overview
                lines = content.split("\n")
                description = []
                for line in lines:
                    line = line.strip()
                    # Skip empty lines and markdown headers
                    if line and not line.startswith("#"):
                        description.append(line)
                        # Stop after accumulating ~500 characters
                        if len(" ".join(description)) > 500:
                            break
                
                # Add description to overview if found
                if description:
                    overview_parts.append("### Project Description\n")
                    # Use first 3 lines of description
                    overview_parts.append(" ".join(description[:3]))
                    overview_parts.append("\n\n")
            except Exception as e:
                logger.warning(f"Error parsing README: {e}")
    
    # Check for package.json (indicates Node.js/JavaScript project)
    package_json = None
    for f in files:
        if not f or not isinstance(f, dict):
            continue
        if normalize_path(f.get("path", "")) == "package.json":
            package_json = f
            break
    
    # Extract technology stack from package.json
    if package_json:
        content = safe_get_content(package_json)
        if content:
            try:
                # Parse JSON content
                data = json.loads(content)
                if isinstance(data, dict):
                    overview_parts.append("### Technology Stack\n")
                    overview_parts.append(f"- **Type**: Node.js/JavaScript Project\n")
                    # Add project description if available
                    if data.get("description"):
                        desc = str(data["description"])[:200]  # Limit description length
                        overview_parts.append(f"- **Description**: {desc}\n")
                    # List key dependencies (first 5)
                    if data.get("dependencies") and isinstance(data["dependencies"], dict):
                        deps = list(data["dependencies"].keys())[:5]
                        overview_parts.append(f"- **Key Dependencies**: {', '.join(deps)}\n")
                    overview_parts.append("\n")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse package.json: Invalid JSON - {e}")
            except Exception as e:
                logger.warning(f"Failed to parse package.json: {e}")
    
    # Check for requirements.txt or pyproject.toml (indicates Python project)
    requirements = None
    for f in files:
        if not f or not isinstance(f, dict):
            continue
        path = normalize_path(f.get("path", ""))
        if path in ["requirements.txt", "pyproject.toml"]:
            requirements = f
            break
    
    # Extract technology stack from Python dependency files
    if requirements:
        content = safe_get_content(requirements)
        if content:
            try:
                overview_parts.append("### Technology Stack\n")
                overview_parts.append(f"- **Type**: Python Project\n")
                # Parse first 5 lines for dependencies
                lines = content.split("\n")[:5]
                deps = []
                for line in lines:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith("#"):
                        # Safely extract package name (remove version specifiers)
                        pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                        if pkg:
                            deps.append(pkg)
                if deps:
                    overview_parts.append(f"- **Key Dependencies**: {', '.join(deps)}\n")
                overview_parts.append("\n")
            except Exception as e:
                logger.warning(f"Error parsing requirements: {e}")
    
    # Fallback message if no overview information found
    if not overview_parts:
        overview_parts.append("### Project Overview\n")
        overview_parts.append("No README or package configuration found. This appears to be a code repository.\n\n")
    
    # Combine all parts into single string
    return "".join(overview_parts)


def identify_key_files(files: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Identify top 10 key files with descriptions.
    
    Args:
        files: List of file dictionaries
        
    Returns:
        List of dictionaries with path and description
    """
    # Validate input is a non-empty list
    if not files or not isinstance(files, list) or len(files) == 0:
        return []
    
    key_files = []
    
    # Priority patterns for important files with their descriptions
    # These patterns identify critical project files that developers should know about
    priority_patterns = [
        (r"^readme\.md$", "Project documentation and overview"),
        (r"^package\.json$", "Node.js project configuration and dependencies"),
        (r"^requirements\.txt$", "Python project dependencies"),
        (r"^pyproject\.toml$", "Python project configuration"),
        (r"^setup\.py$", "Python package setup configuration"),
        (r"^main\.py$", "Main application entry point"),
        (r"^app\.py$", "Application entry point"),
        (r"^index\.(js|ts|tsx)$", "Application entry point"),
        (r"^server\.(js|ts|py)$", "Server configuration"),
        (r"^config\.(js|ts|py|json|yaml|yml)$", "Application configuration"),
        (r"^\.env\.example$", "Environment variables template"),
        (r"^docker-compose\.yml$", "Docker services configuration"),
        (r"^dockerfile$", "Docker container configuration"),
        (r"^makefile$", "Build automation scripts"),
        (r"^\.github/workflows/.*\.yml$", "CI/CD workflow configuration"),
    ]
    
    # Score files based on patterns and characteristics
    scored_files = []
    seen_paths = set()  # Track duplicate paths to avoid processing same file twice
    
    for file_info in files:
        # Validate file_info is a dictionary
        if not file_info or not isinstance(file_info, dict):
            continue
        
        # Get and normalize path
        raw_path = file_info.get("path")
        if not raw_path:
            continue
        
        path = normalize_path(raw_path)
        
        # Skip duplicates (shouldn't happen but defensive programming)
        if path in seen_paths:
            logger.warning(f"Duplicate path detected: {path}")
            continue
        seen_paths.add(path)
        
        path_lower = path.lower()
        score = 0
        description = None
        
        # Check priority patterns with error handling
        try:
            for pattern, desc in priority_patterns:
                # If path matches a priority pattern, give it highest score
                if re.search(pattern, path_lower, re.IGNORECASE):
                    score = 100
                    description = desc
                    break
        except re.error as e:
            logger.warning(f"Regex error for path {path}: {e}")
            continue
        
        # Score by file type and location if not a priority file
        if score == 0:
            # Source code files get medium priority
            if path_lower.endswith((".py", ".js", ".ts", ".tsx", ".jsx")):
                score = 50
            # Configuration files get slightly lower priority
            if path_lower.endswith((".json", ".yaml", ".yml", ".toml")):
                score = 40
            # Root level files are more important (easier to find)
            if "/" not in path:
                score += 20
            # Files in src/ or app/ directories are typically important
            if path.startswith("src/") or path.startswith("app/"):
                score += 10
        
        # Generate description if not set by priority patterns
        if not description:
            try:
                filename = os.path.basename(path)
                dirname = os.path.dirname(path)
                
                # Generate description based on file extension
                if path_lower.endswith(".py"):
                    description = f"Python module in {dirname or 'root'}"
                elif path_lower.endswith((".js", ".ts", ".tsx", ".jsx")):
                    description = f"JavaScript/TypeScript module in {dirname or 'root'}"
                elif path_lower.endswith((".json", ".yaml", ".yml")):
                    description = f"Configuration file in {dirname or 'root'}"
                else:
                    description = f"Source file in {dirname or 'root'}"
            except Exception as e:
                logger.warning(f"Error generating description for {path}: {e}")
                description = "Source file"
        
        # Add file with its score and description
        scored_files.append({
            "path": path,
            "score": score,
            "description": description
        })
    
    # Handle edge case where all files score 0 (unusual but possible)
    if scored_files and all(f["score"] == 0 for f in scored_files):
        logger.info("All files scored 0, using alphabetical order")
    
    # Sort by score (descending) and then by path (ascending) for ties
    try:
        scored_files.sort(key=lambda x: (-x["score"], x["path"]))
    except Exception as e:
        logger.warning(f"Error sorting files: {e}")
        # Fallback to simple alphabetical sort
        scored_files.sort(key=lambda x: x.get("path", ""))
    
    # Extract top 10 files with path and description
    key_files = [
        {"path": f["path"], "description": f["description"]}
        for f in scored_files[:10]
    ]
    
    return key_files


def analyze_folder_structure(files: List[Dict[str, Any]]) -> str:
    """
    Analyze and explain folder structure.
    
    Args:
        files: List of file dictionaries
        
    Returns:
        Markdown string explaining folder structure
    """
    # Validate input is a non-empty list
    if not files or not isinstance(files, list) or len(files) == 0:
        return "### Folder Structure\n\nNo files available for analysis.\n\n"
    
    # Extract unique directories with validation
    directories = set()
    for file_info in files:
        # Skip invalid file entries
        if not file_info or not isinstance(file_info, dict):
            continue
        
        raw_path = file_info.get("path")
        if not raw_path:
            continue
        
        path = normalize_path(raw_path)
        
        # Split path into parts (handles both forward and backward slashes after normalization)
        path_parts = path.split("/")
        
        # Avoid circular references and excessive depth (limit to 10 levels)
        max_depth = 10
        for i in range(min(len(path_parts) - 1, max_depth)):
            # Build directory path from parts (e.g., "src", "src/components", etc.)
            dir_path = "/".join(path_parts[:i+1])
            if dir_path:  # Skip empty strings
                directories.add(dir_path)
    
    # Categorize directories based on common patterns
    structure_explanation = []
    
    # Common directory patterns and their purposes
    # Maps regex patterns to human-readable explanations
    dir_patterns = {
        r"^src/?$": "Source code directory - contains main application code",
        r"^app/?$": "Application directory - contains main application logic",
        r"^backend/?$": "Backend directory - contains server-side code",
        r"^frontend/?$": "Frontend directory - contains client-side code",
        r"^api/?$": "API directory - contains API endpoints and routes",
        r"^components/?$": "Components directory - contains reusable UI components",
        r"^utils/?$": "Utilities directory - contains helper functions and utilities",
        r"^lib/?$": "Library directory - contains shared libraries and modules",
        r"^config/?$": "Configuration directory - contains configuration files",
        r"^tests?/?$": "Tests directory - contains test files and test suites",
        r"^docs?/?$": "Documentation directory - contains project documentation",
        r"^public/?$": "Public directory - contains static assets served directly",
        r"^static/?$": "Static directory - contains static files (CSS, images, etc.)",
        r"^assets/?$": "Assets directory - contains media and resource files",
        r"^models/?$": "Models directory - contains data models and schemas",
        r"^routes/?$": "Routes directory - contains routing logic",
        r"^controllers/?$": "Controllers directory - contains business logic handlers",
        r"^services/?$": "Services directory - contains business logic services",
        r"^middleware/?$": "Middleware directory - contains middleware functions",
        r"^scripts/?$": "Scripts directory - contains utility and build scripts",
    }
    
    # Match directories against patterns and generate explanations
    explained_dirs = []
    for directory in sorted(directories):
        dir_lower = directory.lower()
        try:
            # Check if directory matches any known pattern
            for pattern, explanation in dir_patterns.items():
                if re.match(pattern, dir_lower):
                    explained_dirs.append(f"- **`{directory}/`**: {explanation}")
                    break
        except re.error as e:
            logger.warning(f"Regex error for directory {directory}: {e}")
            continue
    
    # Build final structure explanation
    if explained_dirs:
        structure_explanation.append("### Key Directories\n\n")
        # Limit to top 10 directories to keep documentation concise
        structure_explanation.extend([f"{d}\n" for d in explained_dirs[:10]])
    else:
        # Fallback message if no recognized directories found
        structure_explanation.append("### Folder Structure\n\n")
        structure_explanation.append("The repository has a flat structure with files primarily in the root directory.\n")
    
    return "".join(structure_explanation)


def generate_feature_guide(files: List[Dict[str, Any]]) -> str:
    """
    Generate a generic guide for adding new features.
    
    Args:
        files: List of file dictionaries
        
    Returns:
        Markdown string with feature addition guide
    """
    # Validate input is a non-empty list
    if not files or not isinstance(files, list) or len(files) == 0:
        return "### How to Add a New Feature\n\nNo files available for analysis.\n\n"
    
    # Detect project type by analyzing file extensions and directory structure
    has_python = False  # Python project indicator
    has_js = False  # JavaScript/TypeScript project indicator
    has_tests = False  # Test files present indicator
    has_api = False  # API/backend structure indicator
    
    # Scan files to determine project characteristics
    for f in files:
        if not f or not isinstance(f, dict):
            continue
        path = normalize_path(f.get("path", ""))
        if not path:
            continue
        
        path_lower = path.lower()
        # Check for Python files
        if path_lower.endswith(".py"):
            has_python = True
        # Check for JavaScript/TypeScript files
        if path_lower.endswith((".js", ".ts", ".jsx", ".tsx")):
            has_js = True
        # Check for test files (any file with "test" in name)
        if "test" in path_lower:
            has_tests = True
        # Check for API/backend directory structure
        if path.startswith(("api/", "backend/", "src/api/")):
            has_api = True
    
    # Start building the feature guide
    guide = ["### How to Add a New Feature\n\n"]
    
    # Generate guide based on detected project type
    if has_api:
        # API/Backend-specific feature development guide
        guide.append("#### For API/Backend Features:\n\n")
        guide.append("1. **Define the Feature Requirements**\n")
        guide.append("   - Identify the endpoint(s) needed\n")
        guide.append("   - Define request/response models\n")
        guide.append("   - Document expected behavior\n\n")
        
        guide.append("2. **Create/Update Data Models**\n")
        if has_python:
            # Python-specific model guidance
            guide.append("   - Add new models in the models directory\n")
            guide.append("   - Update database schemas if needed\n")
        else:
            # Generic model guidance for other languages
            guide.append("   - Define data structures and types\n")
        guide.append("   - Ensure proper validation\n\n")
        
        guide.append("3. **Implement Business Logic**\n")
        guide.append("   - Create service functions for the feature\n")
        guide.append("   - Add necessary helper utilities\n")
        guide.append("   - Handle error cases appropriately\n\n")
        
        guide.append("4. **Add API Endpoints**\n")
        guide.append("   - Create new route handlers\n")
        guide.append("   - Integrate with existing middleware\n")
        guide.append("   - Add proper authentication/authorization\n\n")
        
        guide.append("5. **Test and Document**\n")
        if has_tests:
            # Include testing guidance if test files exist
            guide.append("   - Write unit tests for new functions\n")
            guide.append("   - Add integration tests for endpoints\n")
        guide.append("   - Update API documentation\n")
        guide.append("   - Test edge cases and error scenarios\n\n")
    
    elif has_js:
        # Frontend-specific feature development guide
        guide.append("#### For Frontend Features:\n\n")
        guide.append("1. **Plan the Component Structure**\n")
        guide.append("   - Identify required components\n")
        guide.append("   - Define component hierarchy\n")
        guide.append("   - Plan state management needs\n\n")
        
        guide.append("2. **Create Components**\n")
        guide.append("   - Build reusable UI components\n")
        guide.append("   - Implement proper prop types/interfaces\n")
        guide.append("   - Add necessary styling\n\n")
        
        guide.append("3. **Implement Feature Logic**\n")
        guide.append("   - Add state management (hooks, context, etc.)\n")
        guide.append("   - Integrate with API endpoints\n")
        guide.append("   - Handle loading and error states\n\n")
        
        guide.append("4. **Add Routing (if needed)**\n")
        guide.append("   - Update routing configuration\n")
        guide.append("   - Add navigation links\n")
        guide.append("   - Ensure proper route guards\n\n")
        
        guide.append("5. **Test and Polish**\n")
        guide.append("   - Test user interactions\n")
        guide.append("   - Verify responsive design\n")
        guide.append("   - Add accessibility features\n")
        guide.append("   - Update documentation\n\n")
    
    else:
        # Generic feature development guide for unknown project types
        guide.append("#### General Feature Development Process:\n\n")
        guide.append("1. **Understand Requirements**\n")
        guide.append("   - Review feature specifications\n")
        guide.append("   - Identify affected components\n")
        guide.append("   - Plan implementation approach\n\n")
        
        guide.append("2. **Set Up Development Environment**\n")
        guide.append("   - Create a feature branch\n")
        guide.append("   - Install any new dependencies\n")
        guide.append("   - Review existing code patterns\n\n")
        
        guide.append("3. **Implement Core Functionality**\n")
        guide.append("   - Write clean, maintainable code\n")
        guide.append("   - Follow project coding standards\n")
        guide.append("   - Add appropriate comments\n\n")
        
        guide.append("4. **Add Tests**\n")
        guide.append("   - Write unit tests for new code\n")
        guide.append("   - Ensure existing tests still pass\n")
        guide.append("   - Test edge cases\n\n")
        
        guide.append("5. **Review and Deploy**\n")
        guide.append("   - Run all tests and linters\n")
        guide.append("   - Update documentation\n")
        guide.append("   - Submit for code review\n")
        guide.append("   - Deploy following project procedures\n\n")
    
    # Combine all guide parts into single string
    return "".join(guide)


def generate_onboarding_doc(repo_data: List[Dict[str, Any]]) -> str:
    """
    Generate a structured onboarding document from repository data.
    
    Args:
        repo_data: List of file dictionaries from fetch_repo_contents()
        
    Returns:
        Markdown string containing onboarding documentation
        
    Raises:
        ValueError: If repo_data is invalid or empty
    """
    # Validate input is a non-empty list
    if not repo_data or not isinstance(repo_data, list):
        raise ValueError("Invalid repository data: must be a non-empty list")
    
    if len(repo_data) == 0:
        raise ValueError("Repository data is empty")
    
    logger.info(f"Generating onboarding document for {len(repo_data)} files")
    
    # List to accumulate documentation sections
    doc_parts = []
    
    try:
        # Header section
        doc_parts.append("# Repository Onboarding Guide\n\n")
        doc_parts.append("*Auto-generated documentation to help you get started with this repository*\n\n")
        doc_parts.append("---\n\n")
        
        # 1. Project Overview section
        doc_parts.append("## 📋 Project Overview\n\n")
        try:
            # Extract overview from README and package files
            overview = extract_project_overview(repo_data)
            doc_parts.append(overview)
        except Exception as e:
            logger.error(f"Error extracting project overview: {e}")
            doc_parts.append("Unable to extract project overview.\n")
        doc_parts.append("\n---\n\n")
        
        # 2. Key Files section
        doc_parts.append("## 🔑 Top 10 Key Files\n\n")
        try:
            # Identify and list the most important files
            key_files = identify_key_files(repo_data)
            if key_files:
                for i, file_info in enumerate(key_files, 1):
                    path = file_info.get('path', 'Unknown')
                    desc = file_info.get('description', 'No description')
                    doc_parts.append(f"{i}. **`{path}`** - {desc}\n")
            else:
                doc_parts.append("No key files identified.\n")
        except Exception as e:
            logger.error(f"Error identifying key files: {e}")
            doc_parts.append("Unable to identify key files.\n")
        doc_parts.append("\n---\n\n")
        
        # 3. Folder Structure section
        doc_parts.append("## 📁 Folder Structure\n\n")
        try:
            # Analyze and explain directory structure
            structure = analyze_folder_structure(repo_data)
            doc_parts.append(structure)
        except Exception as e:
            logger.error(f"Error analyzing folder structure: {e}")
            doc_parts.append("Unable to analyze folder structure.\n")
        doc_parts.append("\n---\n\n")
        
        # 4. Feature Addition Guide section
        doc_parts.append("## 🚀 Adding New Features\n\n")
        try:
            # Generate project-specific feature development guide
            guide = generate_feature_guide(repo_data)
            doc_parts.append(guide)
        except Exception as e:
            logger.error(f"Error generating feature guide: {e}")
            doc_parts.append("Unable to generate feature guide.\n")
        doc_parts.append("\n---\n\n")
        
        # Footer section with next steps
        doc_parts.append("## 💡 Next Steps\n\n")
        doc_parts.append("1. Read through the key files to understand the codebase\n")
        doc_parts.append("2. Set up your development environment\n")
        doc_parts.append("3. Review existing features and code patterns\n")
        doc_parts.append("4. Start with small changes to familiarize yourself\n")
        doc_parts.append("5. Reach out to the team for guidance\n\n")
        doc_parts.append("*Happy coding! 🎉*\n")
        
        # Use efficient string building by joining all parts
        result = "".join(doc_parts)
        
        # Validate result is not empty (sanity check)
        if not result or not result.strip():
            raise ValueError("Generated documentation is empty")
        
        logger.info("Onboarding document generated successfully")
        
        return result
        
    except Exception as e:
        # Log and re-raise any errors during generation
        logger.error(f"Error generating onboarding document: {e}")
        raise

# Made with Bob