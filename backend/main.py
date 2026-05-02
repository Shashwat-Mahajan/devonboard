"""
FastAPI application for GitHub repository analysis.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Dict, Any
import logging
import os
import re

from github_client import fetch_repo_contents
from doc_generator import generate_onboarding_doc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DevOnboard API",
    description="API for analyzing GitHub repositories",
    version="1.0.0"
)

# Configure CORS with environment-based origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Configurable via environment variable
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


class AnalyzeRequest(BaseModel):
    """Request model for repository analysis."""
    github_url: str

    @field_validator('github_url')
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        """Validate GitHub URL format and content."""
        # Strip whitespace
        v = v.strip()
        
        # Check for empty or whitespace-only strings
        if not v:
            raise ValueError("GitHub URL cannot be empty")
        
        # Check for valid GitHub URL pattern
        github_pattern = r'^https?://(?:www\.)?github\.com/[\w\-\.]+/[\w\-\.]+/?(?:\.git)?$'
        if not re.match(github_pattern, v, re.IGNORECASE):
            raise ValueError(
                "Invalid GitHub URL format. Expected format: https://github.com/owner/repo"
            )
        
        # Check for special characters that might cause issues
        if any(char in v for char in ['<', '>', '"', '{', '}', '|', '\\', '^', '`']):
            raise ValueError("GitHub URL contains invalid characters")
        
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "github_url": "https://github.com/owner/repo"
            }
        }


class AnalyzeResponse(BaseModel):
    """Response model for repository analysis."""
    onboarding_doc: str
    file_count: int


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "DevOnboard API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
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
    try:
        logger.info(f"Analyzing repository: {request.github_url}")
        
        # Fetch repository contents with timeout handling
        try:
            files = await fetch_repo_contents(request.github_url)
        except TimeoutError:
            logger.error("Request timeout while fetching repository")
            raise HTTPException(
                status_code=504,
                detail="Request timeout: GitHub API took too long to respond. Please try again."
            )
        
        # Validate files list is not empty
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=404,
                detail="No files found or repository is empty"
            )
        
        logger.info(f"Successfully fetched {len(files)} files")
        
        # Generate onboarding documentation with error handling
        try:
            onboarding_doc = generate_onboarding_doc(files)
            
            # Validate generated documentation is not empty
            if not onboarding_doc or not onboarding_doc.strip():
                raise ValueError("Generated documentation is empty")
                
        except Exception as doc_error:
            logger.error(f"Error generating documentation: {str(doc_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate documentation: {str(doc_error)}"
            )
        
        logger.info("Generated onboarding documentation")
        
        return AnalyzeResponse(
            onboarding_doc=onboarding_doc,
            file_count=len(files)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        logger.error(f"Invalid URL: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid GitHub URL: {str(e)}"
        )
    except PermissionError as e:
        logger.error(f"Permission denied: {str(e)}")
        # Check if it's a rate limit error
        error_msg = str(e).lower()
        if "rate limit" in error_msg or "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="GitHub API rate limit exceeded. Please try again later or provide a GitHub token."
            )
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: {str(e)}"
        )
    except ConnectionError as e:
        logger.error(f"Network error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Network error: Unable to connect to GitHub. Please check your connection and try again."
        )
    except Exception as e:
        logger.error(f"Error analyzing repository: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze repository: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

# Made with Bob
