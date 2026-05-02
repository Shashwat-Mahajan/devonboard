"""
Unit tests for doc_generator module.
Tests document generation, file analysis, and markdown output.
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from doc_generator import (
    normalize_path,
    safe_get_content,
    extract_project_overview,
    identify_key_files,
    analyze_folder_structure,
    generate_feature_guide,
    generate_onboarding_doc,
)


class TestNormalizePath:
    """Tests for normalize_path function."""
    
    def test_normalize_backslashes(self):
        """Test that backslashes are converted to forward slashes."""
        assert normalize_path("src\\app\\main.py") == "src/app/main.py"
    
    def test_remove_duplicate_slashes(self):
        """Test that duplicate slashes are removed."""
        assert normalize_path("src//app///main.py") == "src/app/main.py"
    
    def test_empty_path(self):
        """Test that empty path returns empty string."""
        assert normalize_path("") == ""
        assert normalize_path(None) == ""
    
    def test_normal_path(self):
        """Test that normal paths are unchanged."""
        assert normalize_path("src/app/main.py") == "src/app/main.py"


class TestSafeGetContent:
    """Tests for safe_get_content function."""
    
    def test_valid_content(self):
        """Test extracting valid content from file dict."""
        file_dict = {"path": "test.py", "content": "print('hello')"}
        assert safe_get_content(file_dict) == "print('hello')"
    
    def test_empty_content(self):
        """Test that empty content returns None."""
        file_dict = {"path": "test.py", "content": ""}
        assert safe_get_content(file_dict) is None
    
    def test_none_content(self):
        """Test that None content returns None."""
        file_dict = {"path": "test.py", "content": None}
        assert safe_get_content(file_dict) is None
    
    def test_invalid_dict(self):
        """Test that invalid input returns None."""
        assert safe_get_content(None) is None
        assert safe_get_content("not a dict") is None
        assert safe_get_content({}) is None
    
    def test_binary_content(self):
        """Test that binary content (with null bytes) returns None."""
        file_dict = {"path": "test.bin", "content": "text\x00binary"}
        assert safe_get_content(file_dict) is None


class TestExtractProjectOverview:
    """Tests for extract_project_overview function."""
    
    def test_with_readme(self):
        """Test overview extraction with README file."""
        files = [
            {"path": "README.md", "content": "# My Project\n\nThis is a test project."}
        ]
        result = extract_project_overview(files)
        assert "Project Description" in result
        assert "This is a test project" in result
    
    def test_with_package_json(self):
        """Test overview extraction with package.json."""
        files = [
            {
                "path": "package.json",
                "content": '{"description": "Test app", "dependencies": {"react": "^18.0.0"}}'
            }
        ]
        result = extract_project_overview(files)
        assert "Technology Stack" in result
        assert "Node.js/JavaScript Project" in result
        assert "react" in result
    
    def test_with_requirements_txt(self):
        """Test overview extraction with requirements.txt."""
        files = [
            {"path": "requirements.txt", "content": "fastapi==0.109.0\nhttpx==0.26.0"}
        ]
        result = extract_project_overview(files)
        assert "Technology Stack" in result
        assert "Python Project" in result
        assert "fastapi" in result
    
    def test_empty_files(self):
        """Test with empty file list."""
        result = extract_project_overview([])
        assert "No files available" in result
    
    def test_no_overview_files(self):
        """Test with files that don't provide overview."""
        files = [{"path": "test.py", "content": "print('hello')"}]
        result = extract_project_overview(files)
        assert "Project Overview" in result


class TestIdentifyKeyFiles:
    """Tests for identify_key_files function."""
    
    def test_priority_files(self):
        """Test that priority files are identified correctly."""
        files = [
            {"path": "README.md", "content": "docs"},
            {"path": "package.json", "content": "{}"},
            {"path": "main.py", "content": "code"},
            {"path": "test.py", "content": "code"},
        ]
        result = identify_key_files(files)
        
        # Should return list of dicts with path and description
        assert len(result) > 0
        assert all("path" in f and "description" in f for f in result)
        
        # Priority files should be first
        paths = [f["path"] for f in result]
        assert "README.md" in paths
        assert "package.json" in paths
    
    def test_empty_files(self):
        """Test with empty file list."""
        result = identify_key_files([])
        assert result == []
    
    def test_max_10_files(self):
        """Test that only top 10 files are returned."""
        files = [{"path": f"file{i}.py", "content": "code"} for i in range(20)]
        result = identify_key_files(files)
        assert len(result) <= 10


class TestAnalyzeFolderStructure:
    """Tests for analyze_folder_structure function."""
    
    def test_common_directories(self):
        """Test that common directories are recognized."""
        files = [
            {"path": "src/app.py", "content": "code"},
            {"path": "tests/test_app.py", "content": "tests"},
            {"path": "docs/README.md", "content": "docs"},
        ]
        result = analyze_folder_structure(files)
        assert "Key Directories" in result or "Folder Structure" in result
        assert "src" in result.lower() or "tests" in result.lower()
    
    def test_empty_files(self):
        """Test with empty file list."""
        result = analyze_folder_structure([])
        assert "No files available" in result
    
    def test_flat_structure(self):
        """Test with flat file structure."""
        files = [
            {"path": "app.py", "content": "code"},
            {"path": "test.py", "content": "tests"},
        ]
        result = analyze_folder_structure(files)
        assert "Folder Structure" in result


class TestGenerateFeatureGuide:
    """Tests for generate_feature_guide function."""
    
    def test_api_project(self):
        """Test guide generation for API project."""
        files = [
            {"path": "api/routes.py", "content": "code"},
            {"path": "backend/main.py", "content": "code"},
        ]
        result = generate_feature_guide(files)
        assert "How to Add a New Feature" in result
        assert "API" in result or "Backend" in result
    
    def test_frontend_project(self):
        """Test guide generation for frontend project."""
        files = [
            {"path": "src/App.jsx", "content": "code"},
            {"path": "src/components/Button.tsx", "content": "code"},
        ]
        result = generate_feature_guide(files)
        assert "How to Add a New Feature" in result
        assert "Frontend" in result or "Component" in result
    
    def test_python_project(self):
        """Test guide generation for Python project."""
        files = [
            {"path": "main.py", "content": "code"},
            {"path": "utils.py", "content": "code"},
        ]
        result = generate_feature_guide(files)
        assert "How to Add a New Feature" in result
    
    def test_empty_files(self):
        """Test with empty file list."""
        result = generate_feature_guide([])
        assert "No files available" in result


class TestGenerateOnboardingDoc:
    """Tests for generate_onboarding_doc function - main function."""
    
    def test_valid_markdown_output(self):
        """Test that valid markdown is generated."""
        files = [
            {"path": "README.md", "content": "# Test Project\n\nA test project."},
            {"path": "main.py", "content": "print('hello')"},
            {"path": "src/app.py", "content": "def main(): pass"},
        ]
        result = generate_onboarding_doc(files)
        
        # Check markdown structure
        assert result.startswith("# Repository Onboarding Guide")
        assert "## 📋 Project Overview" in result
        assert "## 🔑 Top 10 Key Files" in result
        assert "## 📁 Folder Structure" in result
        assert "## 🚀 Adding New Features" in result
        assert "## 💡 Next Steps" in result
        
        # Check it's valid markdown (has headers and content)
        assert result.count("#") >= 5
        assert len(result) > 100
    
    def test_with_package_json(self):
        """Test with Node.js project."""
        files = [
            {
                "path": "package.json",
                "content": '{"name": "test", "description": "Test app", "dependencies": {"react": "^18.0.0"}}'
            },
            {"path": "src/index.js", "content": "console.log('hello');"},
        ]
        result = generate_onboarding_doc(files)
        
        assert "Repository Onboarding Guide" in result
        assert "Node.js" in result or "JavaScript" in result
    
    def test_with_python_project(self):
        """Test with Python project."""
        files = [
            {"path": "requirements.txt", "content": "fastapi==0.109.0\npytest==7.4.0"},
            {"path": "main.py", "content": "def main(): pass"},
        ]
        result = generate_onboarding_doc(files)
        
        assert "Repository Onboarding Guide" in result
        assert "Python" in result
    
    def test_invalid_input_empty_list(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            generate_onboarding_doc([])
    
    def test_invalid_input_none(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="Invalid repository data"):
            generate_onboarding_doc(None)
    
    def test_invalid_input_not_list(self):
        """Test that non-list raises ValueError."""
        with pytest.raises(ValueError, match="Invalid repository data"):
            generate_onboarding_doc("not a list")
    
    def test_minimal_valid_input(self):
        """Test with minimal valid input."""
        files = [{"path": "test.py", "content": "print('hello')"}]
        result = generate_onboarding_doc(files)
        
        # Should still generate valid markdown
        assert "Repository Onboarding Guide" in result
        assert len(result) > 50

# Made with Bob
