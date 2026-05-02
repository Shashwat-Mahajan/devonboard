"""
FastAPI application for GitHub repository analysis.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any
import logging

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    """Request model for repository analysis."""
    github_url: str

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
        
        # Fetch repository contents
        files = await fetch_repo_contents(request.github_url)
        
        if not files:
            raise HTTPException(
                status_code=404,
                detail="No files found or repository is empty"
            )
        
        logger.info(f"Successfully fetched {len(files)} files")
        
        # Generate onboarding documentation
        onboarding_doc = generate_onboarding_doc(files)
        logger.info("Generated onboarding documentation")
        
        return AnalyzeResponse(
            onboarding_doc=onboarding_doc,
            file_count=len(files)
        )
        
    except ValueError as e:
        logger.error(f"Invalid URL: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid GitHub URL: {str(e)}"
        )
    except PermissionError as e:
        logger.error(f"Permission denied: {str(e)}")
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error analyzing repository: {str(e)}")
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
