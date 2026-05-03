"""
Documentation generator - Complete rewrite with actual code extraction.
"""
import re
import json
from typing import Dict, Any, List, Tuple, Optional
import logging
import watsonx_client

logger = logging.getLogger(__name__)


def generate_onboarding_doc(repo_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Generate onboarding doc with actual code content extraction.
    Returns (markdown_string, metadata_dict)
    """
    files = repo_data.get('files', [])
    repo_type = repo_data.get('repo_type', {})
    owner = repo_data.get('owner', '')
    repo = repo_data.get('repo', '')
    
    # Index files by category for fast lookup
    by_category = {}
    for f in files:
        cat = f.get('category', 'other')
        by_category.setdefault(cat, []).append(f)
    
    # Helper to find file by path pattern
    def find_file(*patterns):
        for f in files:
            path = f['path'].lower()
            if any(p.lower() in path for p in patterns):
                return f
        return None
    
    # Helper to extract content section
    def get_content(f, max_chars=2000):
        if not f:
            return None
        return f.get('content', '')[:max_chars]
    
    doc = []
    meta = {
        'language': repo_type.get('language', 'Unknown'),
        'framework': repo_type.get('framework', 'Unknown'),
        'has_auth': repo_type.get('has_auth', False),
        'has_database': repo_type.get('has_database', False),
        'endpoint_count': 0,
        'model_count': 0,
        'total_files_analyzed': len(files),
        'owner': owner,
        'repo': repo
    }
    
    # SECTION 1: Project Overview
    doc.append("## 📋 Project Overview\n")
    readme = find_file('readme')
    pkg = find_file('package.json')
    req = find_file('requirements.txt', 'setup.py', 'pyproject.toml')
    
    if readme:
        first_200 = get_content(readme, 500)
        doc.append(f"**From README:**\n{first_200}\n")
    
    doc.append(f"- **Language:** {meta['language']}")
    doc.append(f"- **Framework:** {meta['framework']}")
    
    if pkg:
        try:
            pkg_data = json.loads(pkg.get('content', '{}'))
            desc = pkg_data.get('description', '')
            if desc:
                doc.append(f"- **Description:** {desc}")
            scripts = pkg_data.get('scripts', {})
            if scripts:
                doc.append(f"- **Scripts:** {', '.join(scripts.keys())}")
            deps = list(pkg_data.get('dependencies', {}).keys())[:10]
            if deps:
                doc.append(f"- **Key Dependencies:** {', '.join(deps)}")
        except:
            pass
    
    # SECTION 2: File Structure
    doc.append("\n## 📁 Repository Structure\n")
    all_paths = [f['path'] for f in files]
    top_folders = list(dict.fromkeys([
        p.split('/')[0] for p in all_paths if '/' in p
    ]))[:15]
    for folder in top_folders:
        folder_files = [p for p in all_paths if p.startswith(folder + '/')]
        doc.append(f"- **{folder}/** ({len(folder_files)} files analyzed)")
    
    # SECTION 3: Key Files
    doc.append("\n## 🔑 Key Files\n")
    priority_files = [f for f in files if f.get('priority', 4) <= 2]
    for f in priority_files[:12]:
        first_line = f.get('content', '').split('\n')[0][:100]
        doc.append(f"- **`{f['path']}`** — {first_line}")
    
    # SECTION 4: Authentication (only if detected)
    if repo_type.get('has_auth'):
        doc.append("\n## 🔐 Authentication\n")
        auth_files = by_category.get('auth', [])
        if auth_files:
            doc.append(f"Authentication is handled in {len(auth_files)} file(s):\n")
            for f in auth_files[:4]:
                content_preview = get_content(f, 800)
                doc.append(f"**`{f['path']}`:**\n```\n{content_preview}\n```\n")
        else:
            doc.append("Auth-related patterns detected in file names but content unavailable.")
    
    # SECTION 5: API Routes (extract actual routes)
    doc.append("\n## 🛣️ API Routes\n")
    route_files = by_category.get('route', [])
    all_routes = []
    
    route_patterns = [
        # Express
        r"(router|app)\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]",
        # FastAPI
        r"@(app|router)\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]",
        # Django urls
        r"path\(['\"]([^'\"]+)['\"]",
        # Flask
        r"@app\.route\(['\"]([^'\"]+)['\"]",
    ]
    
    for f in route_files + by_category.get('entry', []):
        content = f.get('content', '')
        for pattern in route_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    route = match[-1]
                else:
                    route = match
                if route and route not in all_routes:
                    all_routes.append(f"`{f['path']}` → `{route}`")
    
    meta['endpoint_count'] = len(all_routes)
    
    if all_routes:
        doc.append(f"Found {len(all_routes)} route(s):\n")
        for r in all_routes[:20]:
            doc.append(f"- {r}")
    else:
        doc.append("No routes detected in analyzed files.")
    
    # SECTION 6: Data Models
    doc.append("\n## 🗄️ Data Models\n")
    model_files = by_category.get('database', [])
    model_patterns = [
        r"class\s+(\w+)\s*\([^)]*Model[^)]*\)",
        r"const\s+(\w+)\s*=\s*mongoose\.model",
        r"@Entity\(\)",
        r"model\s+(\w+)\s*\{",
    ]
    models_found = []
    for f in model_files:
        content = f.get('content', '')
        for pattern in model_patterns:
            matches = re.findall(pattern, content)
            for m in matches:
                if m and m not in models_found:
                    models_found.append(f"`{m}` in `{f['path']}`")
    
    meta['model_count'] = len(models_found)
    if models_found:
        for m in models_found[:10]:
            doc.append(f"- {m}")
    else:
        doc.append("No ORM models detected in analyzed files.")
    
    # SECTION 7: Getting Started
    doc.append("\n## 🚀 Getting Started\n")
    env_example = find_file('.env.example', '.env.sample')
    docker = find_file('dockerfile', 'docker-compose')
    
    if pkg:
        try:
            pkg_data = json.loads(pkg.get('content', '{}'))
            scripts = pkg_data.get('scripts', {})
            if 'install' in scripts or True:
                doc.append("```bash\nnpm install")
                if 'dev' in scripts:
                    doc.append("npm run dev")
                elif 'start' in scripts:
                    doc.append("npm start")
                doc.append("```\n")
        except:
            pass
    elif req:
        doc.append("```bash\npip install -r requirements.txt\npython main.py\n```\n")
    
    if env_example:
        doc.append(f"**Environment variables** (see `.env.example`):\n```\n{get_content(env_example, 400)}\n```\n")
    
    # SECTION 8: How to Add a Feature
    doc.append("\n## ➕ How to Add a New Feature\n")
    fw = meta['framework']
    lang = meta['language']
    
    if 'Express' in fw or 'JavaScript' in lang:
        doc.append(
            "1. Add route in `routes/` folder\n"
            "2. Create controller in `controllers/`\n"
            "3. Add model in `models/` if needed\n"
            "4. Add middleware if auth required\n"
            "5. Write tests in `tests/` or `__tests__/`"
        )
    elif 'FastAPI' in fw or 'Flask' in fw:
        doc.append(
            "1. Add endpoint in `main.py` or `routes/`\n"
            "2. Create Pydantic model if needed\n"
            "3. Add database model in `models/`\n"
            "4. Add service logic in `services/`\n"
            "5. Write tests with pytest"
        )
    elif 'Django' in fw:
        doc.append(
            "1. Create view in `views.py`\n"
            "2. Register URL in `urls.py`\n"
            "3. Add model in `models.py` + migrate\n"
            "4. Create serializer if using DRF\n"
            "5. Write tests in `tests.py`"
        )
    elif 'React' in fw or 'Next' in fw:
        doc.append(
            "1. Create component in `components/`\n"
            "2. Add page in `pages/` or `app/`\n"
            "3. Add state management if needed\n"
            "4. Connect to API in `services/` or hooks\n"
            "5. Add tests in `__tests__/`"
        )
    else:
        doc.append(
            "1. Identify the relevant module/folder\n"
            "2. Create new file following existing patterns\n"
            "3. Register/import in the main entry point\n"
            "4. Add tests following existing test patterns\n"
            "5. Update documentation"
        )
    
    full_doc = '\n'.join(doc)
    
    # Add AI insights if watsonx is configured
    if watsonx_client.is_configured():
        try:
            insights_prompt = f"""You are a senior software architect reviewing a code repository. Be concise and specific.

Repository details:
- Language: {meta['language']}
- Framework: {meta['framework']}
- Has Authentication: {meta['has_auth']}
- Has Database: {meta['has_database']}
- API Endpoints found: {meta['endpoint_count']}
- Total files analyzed: {meta['total_files_analyzed']}

Documentation excerpt:
{full_doc[:2500]}

Provide exactly these four things:
1. Architecture pattern (1 sentence): MVC / microservices / monolith / JAMstack / other
2. Top 3 files a new developer must read first and why
3. One potential risk or gotcha in this codebase
4. Complexity rating: Simple / Medium / Complex with one reason

Keep total response under 300 words."""
            
            cache_key = f"insights_{owner}_{repo}"
            insights = watsonx_client.generate_text(
                prompt=insights_prompt,
                cache_key=cache_key,
                max_tokens=400
            )
            full_doc += f"\n\n## 🤖 AI Insights (Powered by IBM watsonx.ai)\n\n{insights}"
        except Exception as e:
            logger.warning(f"Failed to generate AI insights: {e}")
    
    return full_doc, meta


# Made with Bob