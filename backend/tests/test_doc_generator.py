"""
Unit tests for doc_generator module.
Tests document generation with the new implementation.
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from doc_generator import generate_onboarding_doc


class TestGenerateOnboardingDoc:
    """Tests for generate_onboarding_doc function - main function."""
    
    def test_valid_markdown_output(self):
        """Test that valid markdown is generated."""
        repo_data = {
            'owner': 'testowner',
            'repo': 'testrepo',
            'files': [
                {"path": "README.md", "content": "# Test Project\n\nA test project.", "priority": 1, "category": "config"},
                {"path": "main.py", "content": "print('hello')", "priority": 2, "category": "entry"},
                {"path": "src/app.py", "content": "def main(): pass", "priority": 3, "category": "route"},
            ],
            'repo_type': {
                'language': 'Python',
                'framework': 'FastAPI',
                'has_auth': False,
                'has_database': False,
                'has_frontend': False,
                'has_backend': True,
                'has_tests': False
            }
        }
        
        result, metadata = generate_onboarding_doc(repo_data)
        
        # Check markdown structure
        assert "## 📋 Project Overview" in result
        assert "## 📁 Repository Structure" in result
        assert "## 🔑 Key Files" in result
        assert "## 🛣️ API Routes" in result
        assert "## 🗄️ Data Models" in result
        assert "## 🚀 Getting Started" in result
        assert "## ➕ How to Add a New Feature" in result
        
        # Check metadata
        assert metadata['language'] == 'Python'
        assert metadata['framework'] == 'FastAPI'
        assert metadata['owner'] == 'testowner'
        assert metadata['repo'] == 'testrepo'
        assert metadata['total_files_analyzed'] == 3
    
    def test_with_package_json(self):
        """Test with Node.js project."""
        repo_data = {
            'owner': 'testowner',
            'repo': 'testrepo',
            'files': [
                {
                    "path": "package.json",
                    "content": '{"name": "test", "description": "Test app", "dependencies": {"react": "^18.0.0"}}',
                    "priority": 1,
                    "category": "config"
                },
                {"path": "src/index.js", "content": "console.log('hello');", "priority": 2, "category": "entry"},
            ],
            'repo_type': {
                'language': 'JavaScript',
                'framework': 'React',
                'has_auth': False,
                'has_database': False,
                'has_frontend': True,
                'has_backend': False,
                'has_tests': False
            }
        }
        
        result, metadata = generate_onboarding_doc(repo_data)
        
        assert "## 📋 Project Overview" in result
        assert "JavaScript" in result or "React" in result
        assert metadata['language'] == 'JavaScript'
        assert metadata['framework'] == 'React'
    
    def test_with_python_project(self):
        """Test with Python project."""
        repo_data = {
            'owner': 'testowner',
            'repo': 'testrepo',
            'files': [
                {"path": "requirements.txt", "content": "fastapi==0.109.0\npytest==7.4.0", "priority": 1, "category": "config"},
                {"path": "main.py", "content": "def main(): pass", "priority": 2, "category": "entry"},
            ],
            'repo_type': {
                'language': 'Python',
                'framework': 'FastAPI',
                'has_auth': False,
                'has_database': False,
                'has_frontend': False,
                'has_backend': True,
                'has_tests': False
            }
        }
        
        result, metadata = generate_onboarding_doc(repo_data)
        
        assert "## 📋 Project Overview" in result
        assert "Python" in result
        assert metadata['language'] == 'Python'
    
    def test_with_auth_detection(self):
        """Test that auth section appears when auth is detected."""
        repo_data = {
            'owner': 'testowner',
            'repo': 'testrepo',
            'files': [
                {"path": "auth/login.py", "content": "def login(): pass", "priority": 3, "category": "auth"},
                {"path": "main.py", "content": "def main(): pass", "priority": 2, "category": "entry"},
            ],
            'repo_type': {
                'language': 'Python',
                'framework': 'FastAPI',
                'has_auth': True,
                'has_database': False,
                'has_frontend': False,
                'has_backend': True,
                'has_tests': False
            }
        }
        
        result, metadata = generate_onboarding_doc(repo_data)
        
        assert "## 🔐 Authentication" in result
        assert metadata['has_auth'] is True
    
    def test_route_extraction(self):
        """Test that API routes are extracted from code."""
        repo_data = {
            'owner': 'testowner',
            'repo': 'testrepo',
            'files': [
                {
                    "path": "routes/api.py",
                    "content": '@app.get("/users")\ndef get_users(): pass\n\n@app.post("/users")\ndef create_user(): pass',
                    "priority": 3,
                    "category": "route"
                },
            ],
            'repo_type': {
                'language': 'Python',
                'framework': 'FastAPI',
                'has_auth': False,
                'has_database': False,
                'has_frontend': False,
                'has_backend': True,
                'has_tests': False
            }
        }
        
        result, metadata = generate_onboarding_doc(repo_data)
        
        assert "## 🛣️ API Routes" in result
        assert "/users" in result
        assert metadata['endpoint_count'] >= 2
    
    def test_model_extraction(self):
        """Test that data models are extracted from code."""
        repo_data = {
            'owner': 'testowner',
            'repo': 'testrepo',
            'files': [
                {
                    "path": "models/user.py",
                    "content": 'class User(BaseModel):\n    name: str\n    email: str',
                    "priority": 3,
                    "category": "database"
                },
            ],
            'repo_type': {
                'language': 'Python',
                'framework': 'FastAPI',
                'has_auth': False,
                'has_database': True,
                'has_frontend': False,
                'has_backend': True,
                'has_tests': False
            }
        }
        
        result, metadata = generate_onboarding_doc(repo_data)
        
        assert "## 🗄️ Data Models" in result
        assert metadata['model_count'] >= 1
    
    def test_minimal_valid_input(self):
        """Test with minimal valid input."""
        repo_data = {
            'owner': 'testowner',
            'repo': 'testrepo',
            'files': [
                {"path": "test.py", "content": "print('hello')", "priority": 4, "category": "other"}
            ],
            'repo_type': {
                'language': 'Python',
                'framework': 'Unknown',
                'has_auth': False,
                'has_database': False,
                'has_frontend': False,
                'has_backend': False,
                'has_tests': False
            }
        }
        
        result, metadata = generate_onboarding_doc(repo_data)
        
        # Should still generate valid markdown
        assert "## 📋 Project Overview" in result
        assert len(result) > 50
        assert metadata['total_files_analyzed'] == 1
    
    def test_empty_files_list(self):
        """Test with empty files list."""
        repo_data = {
            'owner': 'testowner',
            'repo': 'testrepo',
            'files': [],
            'repo_type': {
                'language': 'Unknown',
                'framework': 'Unknown',
                'has_auth': False,
                'has_database': False,
                'has_frontend': False,
                'has_backend': False,
                'has_tests': False
            }
        }
        
        result, metadata = generate_onboarding_doc(repo_data)
        
        # Should still generate markdown even with no files
        assert "## 📋 Project Overview" in result
        assert metadata['total_files_analyzed'] == 0
    
    def test_framework_specific_instructions(self):
        """Test that framework-specific instructions are included."""
        # Test FastAPI
        repo_data = {
            'owner': 'testowner',
            'repo': 'testrepo',
            'files': [{"path": "main.py", "content": "from fastapi import FastAPI", "priority": 2, "category": "entry"}],
            'repo_type': {
                'language': 'Python',
                'framework': 'FastAPI',
                'has_auth': False,
                'has_database': False,
                'has_frontend': False,
                'has_backend': True,
                'has_tests': False
            }
        }
        
        result, metadata = generate_onboarding_doc(repo_data)
        # Just check that instructions section exists
        assert "## ➕ How to Add a New Feature" in result
        assert len(result) > 100


# Made with Bob
