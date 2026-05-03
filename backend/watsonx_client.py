from dotenv import load_dotenv
from pathlib import Path
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
import os

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

_model = None
_cache = {}

def _get_config():
    """Read config fresh every time to ensure .env is loaded"""
    api_key = os.getenv("WATSONX_API_KEY")
    project_id = os.getenv("WATSONX_PROJECT_ID")
    url = os.getenv("WATSONX_URL", 
                    "https://us-south.ml.cloud.ibm.com")
    model_id = os.getenv("WATSONX_MODEL_ID",
                         "meta-llama/llama-3-3-70b-instruct")
    print(f"[watsonx] Config check:")
    print(f"  API_KEY loaded: {bool(api_key)}")
    print(f"  PROJECT_ID loaded: {bool(project_id)}")
    print(f"  URL: {url}")
    print(f"  MODEL: {model_id}")
    return api_key, project_id, url, model_id

def is_configured() -> bool:
    api_key, project_id, url, _ = _get_config()
    result = bool(api_key and project_id and url)
    print(f"[watsonx] is_configured: {result}")
    return result

def get_model():
    global _model
    if _model is None:
        api_key, project_id, url, model_id = _get_config()
        if not api_key or not project_id:
            raise Exception(
                "WATSONX_API_KEY or WATSONX_PROJECT_ID "
                "not set in .env file"
            )
        credentials = Credentials(
            url=url,
            api_key=api_key
        )
        _model = ModelInference(
            model_id=model_id,
            credentials=credentials,
            project_id=project_id
        )
        print(f"[watsonx] Model initialized: {model_id}")
    return _model

def generate_text(prompt: str, cache_key: str = None,
                  max_tokens: int = 600) -> str:
    if cache_key and cache_key in _cache:
        print(f"[watsonx] Cache hit: {cache_key}")
        return _cache[cache_key]
    try:
        model = get_model()
        response = model.generate_text(
            prompt=prompt,
            params={
                "max_new_tokens": max_tokens,
                "min_new_tokens": 30,
                "temperature": 0.3,
                "top_p": 0.9,
                "repetition_penalty": 1.1
            }
        )
        result = (response if isinstance(response, str) 
                  else str(response))
        if cache_key:
            _cache[cache_key] = result
        print(f"[watsonx] Response length: {len(result)}")
        return result
    except Exception as e:
        print(f"[watsonx] Generation error: {str(e)}")
        raise

def clear_cache():
    _cache.clear()
    print("[watsonx] Cache cleared")

def get_cache_size() -> int:
    return len(_cache)

def get_model_id() -> str:
    _, _, _, model_id = _get_config()
    return model_id

def get_url() -> str:
    _, _, url, _ = _get_config()
    return url

def get_project_id_preview() -> str:
    _, project_id, _, _ = _get_config()
    if not project_id:
        return "not set"
    return project_id[:8] + "..."

# Made with Bob
