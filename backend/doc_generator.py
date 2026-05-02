"""
Documentation generator for creating onboarding documents from repository data.
"""
import os
import re
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def extract_project_overview(files: List[Dict[str, Any]]) -> str:
    """
    Extract project overview from README and package files.
    
    Args:
        files: List of file dictionaries with path and content
        
    Returns:
        Markdown string with project overview
    """
    overview_parts = []
    
    # Find and parse README
    readme_file = next(
        (f for f in files if f["path"].lower() in ["readme.md", "readme.txt", "readme"]),
        None
    )
    
    if readme_file and readme_file.get("content"):
        content = readme_file["content"]
        # Extract first paragraph or first 500 characters
        lines = content.split("\n")
        description = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                description.append(line)
                if len(" ".join(description)) > 500:
                    break
        
        if description:
            overview_parts.append("### Project Description\n")
            overview_parts.append(" ".join(description[:3]))
            overview_parts.append("\n\n")
    
    # Check for package.json (Node.js project)
    package_json = next(
        (f for f in files if f["path"] == "package.json"),
        None
    )
    
    if package_json and package_json.get("content"):
        try:
            import json
            data = json.loads(package_json["content"])
            overview_parts.append("### Technology Stack\n")
            overview_parts.append(f"- **Type**: Node.js/JavaScript Project\n")
            if data.get("description"):
                overview_parts.append(f"- **Description**: {data['description']}\n")
            if data.get("dependencies"):
                deps = list(data["dependencies"].keys())[:5]
                overview_parts.append(f"- **Key Dependencies**: {', '.join(deps)}\n")
            overview_parts.append("\n")
        except Exception as e:
            logger.warning(f"Failed to parse package.json: {e}")
    
    # Check for requirements.txt (Python project)
    requirements = next(
        (f for f in files if f["path"] in ["requirements.txt", "pyproject.toml"]),
        None
    )
    
    if requirements and requirements.get("content"):
        overview_parts.append("### Technology Stack\n")
        overview_parts.append(f"- **Type**: Python Project\n")
        lines = requirements["content"].split("\n")[:5]
        deps = [line.split("==")[0].split(">=")[0].strip() for line in lines if line.strip() and not line.startswith("#")]
        if deps:
            overview_parts.append(f"- **Key Dependencies**: {', '.join(deps)}\n")
        overview_parts.append("\n")
    
    if not overview_parts:
        overview_parts.append("### Project Overview\n")
        overview_parts.append("No README or package configuration found. This appears to be a code repository.\n\n")
    
    return "".join(overview_parts)


def identify_key_files(files: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Identify top 10 key files with descriptions.
    
    Args:
        files: List of file dictionaries
        
    Returns:
        List of dictionaries with path and description
    """
    key_files = []
    
    # Priority patterns for important files
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
    
    # Score files based on patterns
    scored_files = []
    for file_info in files:
        path = file_info["path"].lower()
        score = 0
        description = None
        
        # Check priority patterns
        for pattern, desc in priority_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                score = 100
                description = desc
                break
        
        # Score by file type and location
        if score == 0:
            if path.endswith((".py", ".js", ".ts", ".tsx", ".jsx")):
                score = 50
            if path.endswith((".json", ".yaml", ".yml", ".toml")):
                score = 40
            if "/" not in path:  # Root level files
                score += 20
            if path.startswith("src/") or path.startswith("app/"):
                score += 10
        
        # Generate description if not set
        if not description:
            filename = os.path.basename(file_info["path"])
            dirname = os.path.dirname(file_info["path"])
            
            if path.endswith(".py"):
                description = f"Python module in {dirname or 'root'}"
            elif path.endswith((".js", ".ts", ".tsx", ".jsx")):
                description = f"JavaScript/TypeScript module in {dirname or 'root'}"
            elif path.endswith((".json", ".yaml", ".yml")):
                description = f"Configuration file in {dirname or 'root'}"
            else:
                description = f"Source file in {dirname or 'root'}"
        
        scored_files.append({
            "path": file_info["path"],
            "score": score,
            "description": description
        })
    
    # Sort by score and take top 10
    scored_files.sort(key=lambda x: (-x["score"], x["path"]))
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
    # Extract unique directories
    directories = set()
    for file_info in files:
        path_parts = file_info["path"].split("/")
        for i in range(len(path_parts) - 1):
            directories.add("/".join(path_parts[:i+1]))
    
    # Categorize directories
    structure_explanation = []
    
    # Common directory patterns and their purposes
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
    
    explained_dirs = []
    for directory in sorted(directories):
        dir_lower = directory.lower()
        for pattern, explanation in dir_patterns.items():
            if re.match(pattern, dir_lower):
                explained_dirs.append(f"- **`{directory}/`**: {explanation}")
                break
    
    if explained_dirs:
        structure_explanation.append("### Key Directories\n\n")
        structure_explanation.extend([f"{d}\n" for d in explained_dirs[:10]])
    else:
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
    # Detect project type
    has_python = any(f["path"].endswith(".py") for f in files)
    has_js = any(f["path"].endswith((".js", ".ts", ".jsx", ".tsx")) for f in files)
    has_tests = any("test" in f["path"].lower() for f in files)
    has_api = any(f["path"].startswith(("api/", "backend/", "src/api/")) for f in files)
    
    guide = ["### How to Add a New Feature\n\n"]
    
    if has_api:
        guide.append("#### For API/Backend Features:\n\n")
        guide.append("1. **Define the Feature Requirements**\n")
        guide.append("   - Identify the endpoint(s) needed\n")
        guide.append("   - Define request/response models\n")
        guide.append("   - Document expected behavior\n\n")
        
        guide.append("2. **Create/Update Data Models**\n")
        if has_python:
            guide.append("   - Add new models in the models directory\n")
            guide.append("   - Update database schemas if needed\n")
        else:
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
            guide.append("   - Write unit tests for new functions\n")
            guide.append("   - Add integration tests for endpoints\n")
        guide.append("   - Update API documentation\n")
        guide.append("   - Test edge cases and error scenarios\n\n")
    
    elif has_js:
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
    
    return "".join(guide)


def generate_onboarding_doc(repo_data: List[Dict[str, Any]]) -> str:
    """
    Generate a structured onboarding document from repository data.
    
    Args:
        repo_data: List of file dictionaries from fetch_repo_contents()
        
    Returns:
        Markdown string containing onboarding documentation
    """
    logger.info(f"Generating onboarding document for {len(repo_data)} files")
    
    doc_parts = []
    
    # Header
    doc_parts.append("# Repository Onboarding Guide\n\n")
    doc_parts.append("*Auto-generated documentation to help you get started with this repository*\n\n")
    doc_parts.append("---\n\n")
    
    # 1. Project Overview
    doc_parts.append("## 📋 Project Overview\n\n")
    doc_parts.append(extract_project_overview(repo_data))
    doc_parts.append("\n---\n\n")
    
    # 2. Key Files
    doc_parts.append("## 🔑 Top 10 Key Files\n\n")
    key_files = identify_key_files(repo_data)
    for i, file_info in enumerate(key_files, 1):
        doc_parts.append(f"{i}. **`{file_info['path']}`** - {file_info['description']}\n")
    doc_parts.append("\n---\n\n")
    
    # 3. Folder Structure
    doc_parts.append("## 📁 Folder Structure\n\n")
    doc_parts.append(analyze_folder_structure(repo_data))
    doc_parts.append("\n---\n\n")
    
    # 4. Feature Addition Guide
    doc_parts.append("## 🚀 Adding New Features\n\n")
    doc_parts.append(generate_feature_guide(repo_data))
    doc_parts.append("\n---\n\n")
    
    # Footer
    doc_parts.append("## 💡 Next Steps\n\n")
    doc_parts.append("1. Read through the key files to understand the codebase\n")
    doc_parts.append("2. Set up your development environment\n")
    doc_parts.append("3. Review existing features and code patterns\n")
    doc_parts.append("4. Start with small changes to familiarize yourself\n")
    doc_parts.append("5. Reach out to the team for guidance\n\n")
    doc_parts.append("*Happy coding! 🎉*\n")
    
    result = "".join(doc_parts)
    logger.info("Onboarding document generated successfully")
    
    return result

# Made with Bob