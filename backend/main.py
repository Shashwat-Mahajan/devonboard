"""
FastAPI application for GitHub repository analysis.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Dict, Any, Optional
import logging
import os
import re

# Import custom modules for GitHub API interaction and documentation generation
from github_client import fetch_repo_contents
from doc_generator import generate_onboarding_doc
from orchestrate_agent import answer_question

# Configure logging to track application behavior and errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Module-level variable to store the last generated onboarding document
_last_onboarding_doc: Optional[str] = None

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
    """
    onboarding_doc: str
    file_count: int


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
        confidence: Confidence score of the answer (0-1)
        sources: List of sources used for the answer
    """
    answer: str
    confidence: float
    sources: list[str]


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


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        Dict[str, str]: Status indicating the API is healthy and operational
    """
    return {"status": "healthy"}


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
    global _last_onboarding_doc
    
    try:
        # Log the start of repository analysis
        logger.info(f"Analyzing repository: {request.github_url}")
        
        # Fetch repository contents with timeout handling
        try:
            # Call GitHub client to fetch all repository files
            files = await fetch_repo_contents(request.github_url)
        except TimeoutError:
            # Handle timeout errors specifically (GitHub API took too long)
            logger.error("Request timeout while fetching repository")
            raise HTTPException(
                status_code=504,
                detail="Request timeout: GitHub API took too long to respond. Please try again."
            )
        
        # Validate files list is not empty
        if not files or len(files) == 0:
            # Repository exists but has no accessible files
            raise HTTPException(
                status_code=404,
                detail="No files found or repository is empty"
            )
        
        logger.info(f"Successfully fetched {len(files)} files")
        
        # Generate onboarding documentation with error handling
        try:
            # Call documentation generator to create markdown documentation
            onboarding_doc = generate_onboarding_doc(files)
            
            # Validate generated documentation is not empty
            if not onboarding_doc or not onboarding_doc.strip():
                raise ValueError("Generated documentation is empty")
            
            # Store the generated documentation for use by /ask endpoint
            _last_onboarding_doc = onboarding_doc
                
        except Exception as doc_error:
            # Handle any errors during documentation generation
            logger.error(f"Error generating documentation: {str(doc_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate documentation: {str(doc_error)}"
            )
        
        logger.info("Generated onboarding documentation")
        
        # Return successful response with documentation and file count
        return AnalyzeResponse(
            onboarding_doc=onboarding_doc,
            file_count=len(files)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is (already properly formatted)
        raise
    except ValueError as e:
        # Handle invalid URL format errors
        logger.error(f"Invalid URL: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid GitHub URL: {str(e)}"
        )
    except PermissionError as e:
        # Handle permission and rate limit errors
        logger.error(f"Permission denied: {str(e)}")
        # Check if it's a rate limit error (GitHub API has usage limits)
        error_msg = str(e).lower()
        if "rate limit" in error_msg or "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="GitHub API rate limit exceeded. Please try again later or provide a GitHub token."
            )
        # Generic permission error (private repo, etc.)
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: {str(e)}"
        )
    except ConnectionError as e:
        # Handle network connectivity errors
        logger.error(f"Network error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Network error: Unable to connect to GitHub. Please check your connection and try again."
        )
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Error analyzing repository: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze repository: {str(e)}"
        )


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
    global _last_onboarding_doc
    
    try:
        logger.info(f"Processing question: {request.question[:100]}...")
        
        # Check if we have a stored onboarding document
        if not _last_onboarding_doc:
            raise HTTPException(
                status_code=400,
                detail="No repository has been analyzed yet. Please analyze a repository first using the /analyze endpoint."
            )
        
        # Call the orchestrate agent to answer the question using stored context
        result = answer_question(request.question, _last_onboarding_doc)
        
        logger.info("Question answered successfully")
        
        return AskResponse(
            answer=result["answer"],
            confidence=result["confidence"],
            sources=result["sources"]
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
