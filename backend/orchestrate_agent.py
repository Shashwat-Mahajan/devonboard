"""
Groq AI agent for Q&A functionality.
Provides intelligent answers to user questions about repository onboarding documentation.
"""
import os
import logging
from typing import Dict, Any
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Groq client
groq_client = None

def get_groq_client() -> Groq:
    """
    Get or initialize the Groq client.
    
    Returns:
        Groq client instance
        
    Raises:
        ValueError: If GROQ_API_KEY is not set
    """
    global groq_client
    
    if groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        groq_client = Groq(api_key=api_key)
    
    return groq_client


def answer_question(question: str, repo_context: str) -> Dict[str, Any]:
    """
    Answer a user question using the repository context with Groq AI.
    
    This function uses the Groq API with llama3-8b-8192 model to provide intelligent
    answers about the repository based on the onboarding documentation.
    
    Args:
        question: The user's question about the repository
        repo_context: The generated onboarding documentation as context
        
    Returns:
        Dictionary containing the answer and metadata
        
    Raises:
        ValueError: If question or context is empty, or if GROQ_API_KEY is not set
    """
    # Validate inputs
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    
    if not repo_context or not repo_context.strip():
        raise ValueError("Repository context cannot be empty")
    
    logger.info(f"Processing question: {question[:100]}...")
    
    try:
        # Get Groq client
        client = get_groq_client()
        
        # Build the user message with context and question
        user_message = f"Documentation:\n{repo_context}\n\nQuestion: {question}"
        
        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions about a software repository. Answer based only on the provided documentation. Be specific and direct."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=500
        )
        
        # Extract the answer from the response
        answer = chat_completion.choices[0].message.content
        
        logger.info("Question answered successfully using Groq AI")
        
        return {
            "answer": answer,
            "confidence": 0.85,
            "sources": ["onboarding_documentation"]
        }
        
    except ValueError as e:
        # Re-raise validation errors
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error answering question with Groq: {e}")
        raise


# Made with Bob