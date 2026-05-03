"""
FastAPI application for GitHub repository analysis.
"""
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Dict, Any, Optional
import logging
import re

# Import custom modules for GitHub API interaction and documentation generation
from github_client import fetch_repo_data
from doc_generator import generate_onboarding_doc
from orchestrate_agent import answer_question
import watsonx_client

# Configure logging to track application behavior and errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Module-level variables to store the last generated onboarding document, raw files, and metadata
last_onboarding_doc: str = ""
last_repo_files: list = []
last_repo_metadata: dict = {}
last_repo_owner: str = ""
last_repo_name: str = ""

# Initialize FastAPI application with metadata
app = FastAPI(
    title="DevOnboard API",
    description="API for analyzing GitHub repositories",
    version="1.0.0"
)

# Configure CORS (Cross-Origin Resource Sharing) to allow frontend access
# Reads allowed origins from environment variable, defaults to common development ports
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

# Add CORS middleware to handle cross-origin requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Configurable via environment variable
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["GET", "POST", "OPTIONS"],  # Allowed HTTP methods
    allow_headers=["Content-Type", "Authorization"],  # Allowed request headers
)


class AnalyzeRequest(BaseModel):
    """
    Request model for repository analysis endpoint.
    
    Attributes:
        github_url: GitHub repository URL to analyze
    """
    github_url: str

    @field_validator('github_url')
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        """
        Validate GitHub URL format and content.
        
        Performs multiple validation checks:
        - Removes leading/trailing whitespace
        - Ensures URL is not empty
        - Validates GitHub URL pattern (supports http/https, with/without www)
        - Checks for potentially dangerous special characters
        
        Args:
            cls: Class reference (required for classmethod)
            v: GitHub URL string to validate
            
        Returns:
            str: Validated and cleaned GitHub URL
            
        Raises:
            ValueError: If URL is empty, has invalid format, or contains dangerous characters
        """
        # Strip whitespace from both ends of the URL
        v = v.strip()
        
        # Check for empty or whitespace-only strings
        if not v:
            raise ValueError("GitHub URL cannot be empty")
        
        # Check for valid GitHub URL pattern using regex
        # Supports: http/https, with/without www, with/without .git extension
        github_pattern = r'^https?://(?:www\.)?github\.com/[\w\-\.]+/[\w\-\.]+/?(?:\.git)?$'
        if not re.match(github_pattern, v, re.IGNORECASE):
            raise ValueError(
                "Invalid GitHub URL format. Expected format: https://github.com/owner/repo"
            )
        
        # Check for special characters that might cause security issues or parsing errors
        if any(char in v for char in ['<', '>', '"', '{', '}', '|', '\\', '^', '`']):
            raise ValueError("GitHub URL contains invalid characters")
        
        return v

    class Config:
        """Pydantic model configuration with example for API documentation."""
        json_schema_extra = {
            "example": {
                "github_url": "https://github.com/owner/repo"
            }
        }


class AnalyzeResponse(BaseModel):
    """
    Response model for repository analysis endpoint.
    
    Attributes:
        onboarding_doc: Generated markdown documentation for the repository
        file_count: Total number of files analyzed in the repository
        metadata: Structured metadata about the analyzed repository
    """
    onboarding_doc: str
    file_count: int
    metadata: Optional[Dict[str, Any]] = None


class AskRequest(BaseModel):
    """
    Request model for Q&A endpoint.
    
    Attributes:
        question: User's question about the repository
    """
    question: str

    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        """
        Validate question is not empty.
        
        Args:
            cls: Class reference (required for classmethod)
            v: Question string to validate
            
        Returns:
            str: Validated question
            
        Raises:
            ValueError: If question is empty
        """
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")
        if len(v) > 500:
            raise ValueError("Question is too long (max 500 characters)")
        return v

    class Config:
        """Pydantic model configuration with example for API documentation."""
        json_schema_extra = {
            "example": {
                "question": "What are the key files in this repository?"
            }
        }


class AskResponse(BaseModel):
    """
    Response model for Q&A endpoint.
    
    Attributes:
        answer: AI-generated answer to the question
        sources: List of sources used for the answer
        powered_by: AI model information
        files_searched: Number of files searched
        files_matched: Number of files matched
    """
    answer: str
    sources: list[str]
    powered_by: Optional[str] = None
    files_searched: Optional[int] = None
    files_matched: Optional[int] = None


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint providing API information.
    
    Returns:
        Dict[str, str]: API name, version, and documentation URL
    """
    return {
        "message": "DevOnboard API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/watsonx-status")
async def watsonx_status():
    configured = watsonx_client.is_configured()
    return {
        "watsonx_connected": configured,
        "model": watsonx_client.get_model_id(),
        "region": watsonx_client.get_url(),
        "project_id": watsonx_client.get_project_id_preview(),
        "cache_entries": watsonx_client.get_cache_size(),
        "ibm_bob_built": True,
        "status": "ready" if configured else "not configured"
    }


@app.get("/health")
async def health():
    configured = watsonx_client.is_configured()
    return {
        "status": "running",
        "watsonx_orchestrate_compatible": True,
        "ibm_bob_built": True,
        "version": "1.0.0",
        "services": {
            "github_api": True,
            "watsonx_ai": configured,
            "model": watsonx_client.get_model_id()
        }
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repository(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze a GitHub repository.
    
    Args:
        request: AnalyzeRequest containing the GitHub repository URL
        
    Returns:
        AnalyzeResponse with repository analysis results
        
    Raises:
        HTTPException: If the repository cannot be accessed or analyzed
    """
    global last_onboarding_doc, last_repo_files, last_repo_metadata, last_repo_owner, last_repo_name
    
    # Clear watsonx cache for fresh analysis
    watsonx_client.clear_cache()
    
    try:
        # Log the start of repository analysis
        logger.info(f"Analyzing repository: {request.github_url}")
        
        # Fetch repository data from GitHub
        try:
            repo_data = await fetch_repo_data(request.github_url)
        except ValueError as e:
            # Invalid URL or repository not found
            error_msg = str(e)
            logger.error(f"ValueError: {error_msg}")
            print(f"ERROR: {error_msg}")  # Print to terminal for debugging
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                raise HTTPException(status_code=400, detail=error_msg)
        except PermissionError as e:
            # Rate limit or authentication issues
            error_msg = str(e)
            logger.error(f"PermissionError: {error_msg}")
            print(f"ERROR: {error_msg}")  # Print to terminal for debugging
            if "rate limit" in error_msg.lower():
                raise HTTPException(status_code=429, detail=error_msg)
            else:
                raise HTTPException(status_code=403, detail=error_msg)
        except ConnectionError as e:
            # Network connectivity issues
            error_msg = str(e)
            logger.error(f"ConnectionError: {error_msg}")
            print(f"ERROR: {error_msg}")  # Print to terminal for debugging
            raise HTTPException(status_code=503, detail=error_msg)
        
        # Extract files from repo_data
        files = repo_data.get("files", [])
        file_count = repo_data.get("file_count", 0)
        
        logger.info(f"Successfully fetched repository data: {file_count} total files, {len(files)} priority files")
        
        # Generate onboarding documentation
        try:
            # Pass the full repo_data dict to the doc generator
            onboarding_doc, metadata = generate_onboarding_doc(repo_data)
            
            # Validate generated documentation is not empty
            if not onboarding_doc or not onboarding_doc.strip():
                raise ValueError("Generated documentation is empty")
            
            # Store the generated documentation, raw files, and metadata for use by /ask endpoint
            last_onboarding_doc = onboarding_doc
            last_repo_files = files
            last_repo_metadata = metadata
            last_repo_owner = repo_data.get('owner', '')
            last_repo_name = repo_data.get('repo', '')
                
        except Exception as doc_error:
            # Handle any errors during documentation generation
            error_msg = f"Failed to generate documentation: {str(doc_error)}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")  # Print to terminal for debugging
            raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info("Generated onboarding documentation with metadata")
        
        # Return successful response with documentation, file count, and metadata
        return AnalyzeResponse(
            onboarding_doc=onboarding_doc,
            file_count=file_count,
            metadata=metadata
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is (already properly formatted)
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"ERROR: {error_msg}")  # Print to terminal for debugging
        raise HTTPException(status_code=500, detail=f"Failed to analyze repository: {str(e)}")


@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest) -> AskResponse:
    """
    Answer a question about the repository using AI.
    
    Args:
        request: AskRequest containing the question
        
    Returns:
        AskResponse with the AI-generated answer
        
    Raises:
        HTTPException: If the question cannot be answered or no repository has been analyzed
    """
    global last_onboarding_doc, last_repo_files, last_repo_metadata
    
    try:
        logger.info(f"Processing question: {request.question[:100]}...")
        
        # Check if we have a stored onboarding document
        if not last_onboarding_doc:
            raise HTTPException(
                status_code=400,
                detail="No repository has been analyzed yet. Please analyze a repository first using the /analyze endpoint."
            )
        
        # Call the orchestrate agent to answer the question using stored context and raw files
        result = answer_question(request.question, last_onboarding_doc, last_repo_files)
        
        logger.info("Question answered successfully")
        
        return AskResponse(
            answer=result["answer"],
            sources=result["sources"],
            powered_by=result.get("powered_by"),
            files_searched=result.get("files_searched"),
            files_matched=result.get("files_matched")
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Handle validation errors
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Error answering question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )


if __name__ == "__main__":
    """
    Run the FastAPI application using Uvicorn server.
    
    This block only executes when the script is run directly (not imported).
    Starts the server on all network interfaces (0.0.0.0) on port 8000
    with auto-reload enabled for development.
    """
    import uvicorn
    uvicorn.run(
        "main:app",  # Application instance to run
        host="0.0.0.0",  # Listen on all network interfaces
        port=8000,  # Port to bind to
        reload=True  # Auto-reload on code changes (development only)
    )

# Made with Bob
