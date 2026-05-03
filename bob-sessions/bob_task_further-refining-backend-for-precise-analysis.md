**User:**

<task>
'backend/github_client.py' (see below for file content) 'backend/doc_generator.py' (see below for file content) 
'backend/orchestrate_agent.py' (see below for file content) 'backend/main.py' (see below for file content)

The Q&A answers are still too generic. The root cause is that 
not enough actual code content is being extracted and stored 
during analysis. Fix everything end to end:

═══════════════════════════════════════════
PART 1 — github_client.py COMPLETE REWRITE
═══════════════════════════════════════════

Rewrite fetch_repo_contents() with this strategy:

STEP 1 - DETECT REPO TYPE FIRST:
After fetching the file tree, detect what kind of repo it is
by scanning all file paths:

def detect_repo_type(file_paths: list) -> dict:
    paths_str = ' '.join(file_paths).lower()
    
    return {
        'has_frontend': any(x in paths_str for x in [
            'react', 'vue', 'angular', 'next', 'nuxt',
            'jsx', 'tsx', 'html', 'css'
        ]),
        'has_backend': any(x in paths_str for x in [
            'server', 'app.py', 'main.py', 'index.js',
            'app.js', 'django', 'flask', 'fastapi',
            'express', 'spring', 'rails'
        ]),
        'has_database': any(x in paths_str for x in [
            'model', 'schema', 'migration', 'mongoose',
            'sequelize', 'prisma', 'sqlalchemy', 'entity'
        ]),
        'has_auth': any(x in paths_str for x in [
            'auth', 'login', 'jwt', 'passport', 'oauth',
            'session', 'middleware', 'guard', 'token'
        ]),
        'has_tests': any(x in paths_str for x in [
            'test', 'spec', '__test__', 'jest', 'pytest'
        ]),
        'language': detect_language(file_paths),
        'framework': detect_framework(file_paths)
    }

def detect_language(file_paths: list) -> str:
    extensions = {}
    for p in file_paths:
        ext = p.rsplit('.', 1)[-1].lower() if '.' in p else ''
        if ext in ['js', 'ts', 'jsx', 'tsx', 'py', 'java',
                   'go', 'rs', 'rb', 'php', 'cs', 'cpp']:
            extensions[ext] = extensions.get(ext, 0) + 1
    if not extensions:
        return 'Unknown'
    primary = max(extensions, key=extensions.get)
    mapping = {
        'js': 'JavaScript', 'ts': 'TypeScript',
        'jsx': 'JavaScript/React', 'tsx': 'TypeScript/React',
        'py': 'Python', 'java': 'Java', 'go': 'Go',
        'rs': 'Rust', 'rb': 'Ruby', 'php': 'PHP',
        'cs': 'C#', 'cpp': 'C++'
    }
    return mapping.get(primary, primary.upper())

def detect_framework(file_paths: list) -> str:
    paths_str = ' '.join(file_paths).lower()
    frameworks = {
        'Next.js': ['next.config', 'pages/_app', 'app/page'],
        'React': ['react', 'jsx', 'tsx'],
        'Vue': ['vue.config', '.vue'],
        'Angular': ['angular.json', 'ng-'],
        'Express': ['express', 'router'],
        'FastAPI': ['fastapi', '@app.get', '@router'],
        'Django': ['django', 'settings.py', 'urls.py'],
        'Flask': ['flask', '@app.route'],
        'Spring': ['spring', 'application.properties'],
        'Rails': ['gemfile', 'routes.rb'],
        'Laravel': ['artisan', 'composer.json']
    }
    for fw, indicators in frameworks.items():
        if any(ind in paths_str for ind in indicators):
            return fw
    return 'Unknown'

STEP 2 - SMART FILE SELECTION BASED ON REPO TYPE:
After detecting repo type, select files in this priority:

Priority 1 — Config files (always fetch all of these):
README.md, README.rst, package.json, requirements.txt,
setup.py, setup.cfg, pyproject.toml, pom.xml, 
build.gradle, Cargo.toml, go.mod, composer.json,
Gemfile, .env.example, docker-compose.yml, Dockerfile

Priority 2 — Entry points (fetch first match of each):
For JS/TS: index.js, index.ts, app.js, app.ts, 
           server.js, server.ts, main.js, main.ts
For Python: main.py, app.py, server.py, wsgi.py, asgi.py
For Java: Main.java, Application.java
For Go: main.go
For Ruby: application.rb, config.ru

Priority 3 — Based on detected repo type:
If has_auth=True: fetch ALL files matching these patterns:
  - path contains any of: auth, login, jwt, passport,
    middleware, guard, permission, session, oauth, token
If has_database=True: fetch ALL files matching:
  - path contains any of: model, schema, entity, 
    migration, repository, dao
If has_backend=True: fetch ALL files matching:
  - path contains any of: route, router, controller,
    handler, endpoint, api, view
If has_frontend=True: fetch ALL files matching:
  - path contains any of: page, component, screen,
    layout, store, context, hook

Priority 4 — Fill remaining slots up to 40 total files:
Pick files from root, src/, app/, lib/ folders
Skip: test files, build output, minified files,
      node_modules, __pycache__, dist, .git

STEP 3 - FETCH WITH FULL CONTENT:
Use asyncio.gather() for parallel fetching.
For each file store:
{
    "path": full file path,
    "content": full decoded content (up to 8000 chars),
    "size": file size in bytes,
    "priority": 1, 2, 3, or 4,
    "category": "config"|"entry"|"auth"|"database"|
                 "route"|"model"|"component"|"other"
}

STEP 4 - STORE EVERYTHING IN main.py:
Store these module-level variables after each analysis:
last_onboarding_doc = ""
last_repo_files = []      # full list with content
last_repo_metadata = {}   # repo_type detection results
last_repo_owner = ""
last_repo_name = ""

═══════════════════════════════════════════
PART 2 — doc_generator.py COMPLETE REWRITE  
═══════════════════════════════════════════

Rewrite generate_onboarding_doc(repo_data: dict) -> tuple:
Returns (markdown_string, metadata_dict)

Use this exact section structure:

def generate_onboarding_doc(repo_data: dict) -> tuple:
    files = repo_data.get('files', [])
    repo_type = repo_data.get('repo_type', {})
    
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
        'owner': repo_data.get('owner', ''),
        'repo': repo_data.get('repo', '')
    }
    
    # SECTION 1: Project Overview
    doc.append("## 📋 Project Overview\n")
    readme = find_file('readme')
    pkg = find_file('package.json')
    req = find_file('requirements.txt', 'setup.py',
                    'pyproject.toml')
    
    if readme:
        first_200 = get_content(readme, 500)
        doc.append(f"**From README:**\n{first_200}\n")
    
    doc.append(f"- **Language:** {meta['language']}")
    doc.append(f"- **Framework:** {meta['framework']}")
    
    if pkg:
        import json as _json
        try:
            pkg_data = _json.loads(
                pkg.get('content','{}')
            )
            desc = pkg_data.get('description','')
            if desc:
                doc.append(f"- **Description:** {desc}")
            scripts = pkg_data.get('scripts', {})
            if scripts:
                doc.append(f"- **Scripts:** "
                           f"{', '.join(scripts.keys())}")
            deps = list(pkg_data.get(
                'dependencies', {}).keys())[:10]
            if deps:
                doc.append(
                    f"- **Key Dependencies:** "
                    f"{', '.join(deps)}"
                )
        except:
            pass
    
    # SECTION 2: File Structure  
    doc.append("\n## 📁 Repository Structure\n")
    all_paths = [f['path'] for f in files]
    top_folders = list(dict.fromkeys([
        p.split('/')[0] for p in all_paths 
        if '/' in p
    ]))[:15]
    for folder in top_folders:
        folder_files = [
            p for p in all_paths 
            if p.startswith(folder + '/')
        ]
        doc.append(
            f"- **{folder}/** "
            f"({len(folder_files)} files analyzed)"
        )
    
    # SECTION 3: Key Files
    doc.append("\n## 🔑 Key Files\n")
    priority_files = [
        f for f in files 
        if f.get('priority', 4) <= 2
    ]
    for f in priority_files[:12]:
        first_line = (
            f.get('content','').split('\n')[0][:100]
        )
        doc.append(
            f"- **`{f['path']}`** — {first_line}"
        )
    
    # SECTION 4: Authentication (only if detected)
    if repo_type.get('has_auth'):
        doc.append("\n## 🔐 Authentication\n")
        auth_files = by_category.get('auth', [])
        if auth_files:
            doc.append(
                f"Authentication is handled in "
                f"{len(auth_files)} file(s):\n"
            )
            for f in auth_files[:4]:
                content_preview = get_content(f, 800)
                doc.append(
                    f"**`{f['path']}`:**\n"
                    f"```\n{content_preview}\n```\n"
                )
        else:
            doc.append(
                "Auth-related patterns detected in "
                "file names but content unavailable."
            )
    
    # SECTION 5: API Routes (extract actual routes)
    doc.append("\n## 🛣️ API Routes\n")
    route_files = by_category.get('route', [])
    all_routes = []
    
    import re
    route_patterns = [
        # Express
        r"(router|app)\.(get|post|put|delete|patch)"
        r"\(['\"]([^'\"]+)['\"]",
        # FastAPI
        r"@(app|router)\.(get|post|put|delete|patch)"
        r"\(['\"]([^'\"]+)['\"]",
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
                    all_routes.append(
                        f"`{f['path']}` → `{route}`"
                    )
    
    meta['endpoint_count'] = len(all_routes)
    
    if all_routes:
        doc.append(
            f"Found {len(all_routes)} route(s):\n"
        )
        for r in all_routes[:20]:
            doc.append(f"- {r}")
    else:
        doc.append(
            "No routes detected in analyzed files."
        )
    
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
                    models_found.append(
                        f"`{m}` in `{f['path']}`"
                    )
    
    meta['model_count'] = len(models_found)
    if models_found:
        for m in models_found[:10]:
            doc.append(f"- {m}")
    else:
        doc.append(
            "No ORM models detected in analyzed files."
        )
    
    # SECTION 7: Getting Started
    doc.append("\n## 🚀 Getting Started\n")
    env_example = find_file('.env.example', '.env.sample')
    docker = find_file('dockerfile', 'docker-compose')
    
    if pkg:
        try:
            pkg_data = _json.loads(
                pkg.get('content', '{}')
            )
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
        doc.append(
            "```bash\npip install -r requirements.txt\n"
            "python main.py\n```\n"
        )
    
    if env_example:
        doc.append(
            f"**Environment variables** "
            f"(see `.env.example`):\n"
            f"```\n"
            f"{get_content(env_example, 400)}\n```\n"
        )
    
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
    return full_doc, meta


═══════════════════════════════════════════
PART 3 — orchestrate_agent.py COMPLETE REWRITE
═══════════════════════════════════════════

Completely rewrite with this precise logic:

import re
import watsonx_client

def extract_keywords(question: str) -> list:
    stop_words = {
        'the','is','are','was','were','a','an','and',
        'or','but','in','on','at','to','for','of','with',
        'by','from','this','that','it','be','do','does',
        'did','have','has','had','will','would','could',
        'should','may','might','can','where','what','how',
        'when','which','who','why','me','my','your','their',
        'please','tell','show','give','find','get','list'
    }
    words = re.findall(r'\b\w+\b', question.lower())
    keywords = [
        w for w in words 
        if w not in stop_words and len(w) > 2
    ]
    
    # Semantic expansions for common dev questions
    expansions = {
        'auth': ['auth','authentication','login','logout',
                 'jwt','token','passport','middleware',
                 'session','cookie','oauth','bearer',
                 'guard','permission','role','user'],
        'authentication': ['auth','login','jwt','token',
                          'passport','session','cookie'],
        'database': ['database','db','model','schema',
                    'mongoose','sequelize','prisma',
                    'sqlalchemy','migration','query',
                    'repository','entity','orm'],
        'route': ['route','router','endpoint','controller',
                 'handler','api','path','url','rest'],
        'api': ['route','router','endpoint','controller',
               'handler','rest','graphql','api'],
        'model': ['model','schema','entity','database',
                 'migration','orm','repository'],
        'test': ['test','spec','jest','pytest','unittest',
                'testing','mock','fixture'],
        'config': ['config','configuration','settings',
                  'env','environment','setup','options'],
        'middleware': ['middleware','interceptor','guard',
                      'filter','pipe','hook'],
        'deploy': ['deploy','dockerfile','docker',
                  'kubernetes','ci','cd','pipeline',
                  'workflow','action','heroku','vercel'],
        'error': ['error','exception','catch','try',
                 'handle','handling','logging','logger'],
        'security': ['security','auth','jwt','bcrypt',
                    'hash','encrypt','ssl','cors','csrf']
    }
    
    expanded = list(keywords)
    for kw in keywords:
        if kw in expansions:
            expanded.extend(expansions[kw])
    
    return list(set(expanded))


def score_and_rank_files(keywords: list,
                         raw_files: list) -> list:
    scored = []
    
    for f in raw_files:
        score = 0
        path = f.get('path', '').lower()
        content = f.get('content', '')
        content_lower = content.lower()
        category = f.get('category', 'other')
        priority = f.get('priority', 4)
        
        # Base score from priority
        score += (5 - priority)
        
        for kw in keywords:
            # Strongest signal: keyword in file path
            if kw in path:
                score += 5
            # Strong: in first 300 chars (imports, class def)
            if kw in content_lower[:300]:
                score += 3
            # Medium: in first 1000 chars
            elif kw in content_lower[:1000]:
                score += 2
            # Weak: anywhere in file
            elif kw in content_lower:
                score += 1
        
        # Boost auth/route files for relevant questions
        if category in ['auth', 'route', 'database']:
            score += 2
            
        if score > 0:
            scored.append((score, f))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:6]]


def extract_relevant_section(content: str,
                              keywords: list,
                              max_lines: int = 80) -> str:
    if not content:
        return ""
    
    lines = content.split('\n')
    line_scores = []
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        score = sum(
            3 if kw in line_lower else 0 
            for kw in keywords
        )
        line_scores.append((i, score))
    
    # Get top scoring line indices
    hot_lines = sorted(
        [x for x in line_scores if x[1] > 0],
        key=lambda x: x[1], 
        reverse=True
    )[:8]
    
    if not hot_lines:
        # No keyword matches - return file start
        return '\n'.join(lines[:40])
    
    # Collect context windows around hot lines
    included = set()
    result_lines = []
    
    for idx, _ in sorted(hot_lines, key=lambda x: x[0]):
        start = max(0, idx - 4)
        end = min(len(lines), idx + 8)
        
        if start not in included:
            if included and min(included) < start - 2:
                result_lines.append('...')
            for i in range(start, end):
                if i not in included:
                    result_lines.append(lines[i])
                    included.add(i)
        
        if len(result_lines) >= max_lines:
            break
    
    return '\n'.join(result_lines)


def answer_question(question: str,
                    context: str,
                    raw_files: list = []) -> dict:
    
    keywords = extract_keywords(question)
    relevant_files = score_and_rank_files(
        keywords, raw_files
    )
    
    # Build rich file context
    files_context = ""
    for f in relevant_files:
        section = extract_relevant_section(
            f.get('content', ''), keywords
        )
        if section.strip():
            files_context += (
                f"\n\n{'='*50}\n"
                f"FILE: {f['path']}\n"
                f"CATEGORY: {f.get('category','other')}\n"
                f"{'='*50}\n"
                f"{section}"
            )
    
    # Count actual code lines provided
    code_lines = len(files_context.split('\n'))
    
    prompt = f"""You are a precise code analyst. 
A developer is asking about a specific codebase.

YOUR RULES:
1. Answer ONLY from the code provided below
2. Always cite the EXACT file path like: "In `path/to/file.js`"
3. Quote actual code snippets when relevant (max 5 lines)
4. If you find the answer: be direct and specific
5. If NOT found in provided code: say exactly
   "I could not find this in the {len(relevant_files)} 
   files analyzed. The most relevant files checked were: 
   {', '.join([f['path'] for f in relevant_files[:3]])}"
6. Never invent code or make assumptions
7. Keep answer under 250 words

REPOSITORY CONTEXT:
{context[:600]}

SOURCE CODE ({len(relevant_files)} most relevant files, 
{code_lines} lines of code):
{files_context[:4000] if files_context 
 else "No files matched this query."}

DEVELOPER QUESTION: {question}

PRECISE ANSWER:"""

    cache_key = (
        f"qa_{hash(question[:100])}_"
        f"{hash(context[:100])}"
    )
    
    try:
        answer = watsonx_client.generate_text(
            prompt=prompt,
            cache_key=cache_key,
            max_tokens=700
        )
        
        # Clean up any prompt leakage
        answer = answer.replace(
            "PRECISE ANSWER:", ""
        ).strip()
        
        return {
            "answer": answer,
            "sources": [
                f["path"] for f in relevant_files
            ],
            "keywords_matched": keywords[:8],
            "files_searched": len(raw_files),
            "files_matched": len(relevant_files),
            "powered_by": "IBM watsonx.ai"
        }
        
    except Exception as e:
        print(f"[qa] Error: {e}")
        fallback = ""
        for f in relevant_files[:2]:
            section = extract_relevant_section(
                f.get('content', ''), keywords, 30
            )
            fallback += (
                f"\n**{f['path']}:**\n"
                f"```\n{section}\n```\n"
            )
        return {
            "answer": (
                f"AI unavailable. "
                f"Most relevant code found:\n\n"
                f"{fallback if fallback else 'No matches.'}"
            ),
            "sources": [
                f["path"] for f in relevant_files
            ],
            "powered_by": "fallback_keyword_search"
        }


═══════════════════════════════════════════
PART 4 — main.py UPDATES
═══════════════════════════════════════════

Make sure these module-level variables exist:

last_onboarding_doc = ""
last_repo_files = []
last_repo_metadata = {}

In the /analyze endpoint:
1. Call repo_data = await fetch_repo_contents(github_url)
2. Call result = generate_onboarding_doc(repo_data)
   - If it returns a tuple: doc, meta = result
   - Store: last_onboarding_doc = doc
   - Store: last_repo_files = repo_data.get('files', [])
   - Store: last_repo_metadata = meta
3. Return both doc and meta to frontend:
   {
     "onboarding_doc": doc,
     "metadata": meta,
     "file_count": meta.get('total_files_analyzed', 0),
     "powered_by": "IBM Bob + IBM watsonx.ai"
   }

In the /ask endpoint:
Pass all three to answer_question:
result = answer_question(
    request.question,
    last_onboarding_doc,
    last_repo_files
)
Return the full result dict including sources 
and keywords_matched.
</task>

<file_content path="backend/github_client.py">
  1 | """
  2 | GitHub API client for fetching repository contents.
  3 | Production-ready implementation with robust error handling.
  4 | """
  5 | import os
  6 | import re
  7 | import base64
  8 | import asyncio
  9 | from typing import Dict, Any, Optional
 10 | import httpx
 11 | from pathlib import Path
 12 | from dotenv import load_dotenv
 13 | import logging
 14 | 
 15 | # Load environment variables from .env file in the same directory
 16 | load_dotenv(dotenv_path=Path(__file__).parent / ".env")
 17 | 
 18 | # Initialize logger
 19 | logger = logging.getLogger(__name__)
 20 | 
 21 | # GitHub API configuration
 22 | GITHUB_API_BASE = "https://api.github.com"
 23 | GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
 24 | 
 25 | # Request timeout in seconds
 26 | REQUEST_TIMEOUT = 30.0
 27 | 
 28 | # Maximum file size to fetch (40KB for TIER 3)
 29 | MAX_FILE_SIZE = 40 * 1024
 30 | 
 31 | # Module-level cache for repository data
 32 | _repo_cache: Dict[str, Dict[str, Any]] = {}
 33 | 
 34 | # TIER 1 - Critical config files (always fetch if they exist)
 35 | TIER1_FILES = [
 36 |     "README.md",
 37 |     "README.rst",
 38 |     "package.json",
 39 |     "requirements.txt",
 40 |     "setup.py",
 41 |     "setup.cfg",
 42 |     "pom.xml",
 43 |     "build.gradle",
 44 |     "Cargo.toml",
 45 |     "go.mod",
 46 |     "docker-compose.yml",
 47 |     "Dockerfile",
 48 |     ".env.example"
 49 | ]
 50 | 
 51 | # TIER 2 - Entry points and key patterns (fetch up to 8)
 52 | TIER2_PATTERNS = {
 53 |     "entry_points": [
 54 |         "main.py", "app.py", "server.py",
 55 |         "index.js", "app.js", "server.js", "main.js",
 56 |         "index.ts", "app.ts",
 57 |         "main.go", "main.rs"
 58 |     ],
 59 |     "path_keywords": [
 60 |         "route", "router",
 61 |         "auth", "login", "middleware",
 62 |         "model", "schema", "database", "db",
 63 |         "config",
 64 |         "controller"
 65 |     ]
 66 | }
 67 | 
 68 | # TIER 3 - Additional files (up to 10)
 69 | TIER3_CONFIG = {
 70 |     "max_files": 10,
 71 |     "min_size": 1024,  # 1KB
 72 |     "max_size": 40 * 1024,  # 40KB
 73 |     "preferred_folders": ["", "src", "app", "lib"],  # root or these folders
 74 |     "exclude_patterns": ["test", "spec", "__test__", ".test.", "dist/", "build/", ".next/", "__pycache__"]
 75 | }
 76 | 
 77 | 
 78 | def parse_github_url(url: str) -> tuple[str, str]:
 79 |     """
 80 |     Parse GitHub URL to extract owner and repository name.
 81 |     
 82 |     Supports formats:
 83 |     - https://github.com/owner/repo
 84 |     - https://github.com/owner/repo.git
 85 |     - https://github.com/owner/repo/tree/main
 86 |     - github.com/owner/repo
 87 |     
 88 |     Args:
 89 |         url: GitHub repository URL
 90 |         
 91 |     Returns:
 92 |         Tuple of (owner, repo)
 93 |         
 94 |     Raises:
 95 |         ValueError: If URL format is invalid
 96 |     """
 97 |     if not url or not isinstance(url, str):
 98 |         raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
 99 |     
100 |     url = url.strip()
101 |     
102 |     if not url:
103 |         raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
104 |     
105 |     # Remove trailing slashes
106 |     url = url.rstrip("/")
107 |     
108 |     # Remove .git extension if present
109 |     if url.endswith(".git"):
110 |         url = url[:-4]
111 |     
112 |     # Remove tree/branch paths (e.g., /tree/main)
113 |     url = re.sub(r'/tree/[^/]+.*$', '', url)
114 |     
115 |     # Pattern to match GitHub URLs
116 |     # Supports: http(s)://github.com/owner/repo or github.com/owner/repo
117 |     pattern = r'(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s]+)'
118 |     
119 |     match = re.search(pattern, url, re.IGNORECASE)
120 |     
121 |     if not match:
122 |         raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
123 |     
124 |     owner = match.group(1).strip()
125 |     repo = match.group(2).strip()
126 |     
127 |     if not owner or not repo:
128 |         raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
129 |     
130 |     return owner, repo
131 | 
132 | 
133 | async def _fetch_single_file(
134 |     client: httpx.AsyncClient,
135 |     owner: str,
136 |     repo: str,
137 |     path: str,
138 |     headers: Dict[str, str],
139 |     size: int = 0,
140 |     tier: str = "TIER3"
141 | ) -> Optional[Dict[str, Any]]:
142 |     """
143 |     Fetch a single file's content from GitHub API with metadata.
144 |     
145 |     Args:
146 |         client: httpx AsyncClient instance
147 |         owner: Repository owner
148 |         repo: Repository name
149 |         path: File path
150 |         headers: Request headers
151 |         size: File size in bytes
152 |         tier: Which tier this file belongs to (TIER1, TIER2, TIER3)
153 |         
154 |     Returns:
155 |         Dictionary with path, content, size, folder, and tier, or None if fetch fails
156 |     """
157 |     content_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
158 |     
159 |     try:
160 |         content_response = await client.get(content_url, headers=headers)
161 |         
162 |         if content_response.status_code == 200:
163 |             content_data = content_response.json()
164 |             encoded_content = content_data.get("content", "")
165 |             
166 |             if encoded_content:
167 |                 try:
168 |                     # Decode base64 content
169 |                     decoded = base64.b64decode(encoded_content)
170 |                     text_content = decoded.decode("utf-8", errors="ignore")
171 |                     
172 |                     # Extract folder from path
173 |                     folder = "/".join(path.split("/")[:-1]) if "/" in path else ""
174 |                     
175 |                     logger.info(f"Fetched content for {path} ({tier})")
176 |                     return {
177 |                         "path": path,
178 |                         "content": text_content,
179 |                         "size": size,
180 |                         "folder": folder,
181 |                         "tier": tier
182 |                     }
183 |                 except Exception as e:
184 |                     logger.warning(f"Failed to decode {path}: {e}")
185 |     except Exception as e:
186 |         logger.warning(f"Failed to fetch {path}: {e}")
187 |     
188 |     return None
189 | 
190 | 
191 | async def fetch_repo_data(url: str) -> Dict[str, Any]:
192 |     """
193 |     Fetch repository data from GitHub API.
194 |     
195 |     Args:
196 |         url: GitHub repository URL
197 |         
198 |     Returns:
199 |         Dictionary containing repository data:
200 |         {
201 |             "owner": str,
202 |             "repo": str,
203 |             "description": str,
204 |             "stars": int,
205 |             "language": str,
206 |             "files": [{"path": str, "content": str}],
207 |             "file_count": int
208 |         }
209 |         
210 |     Raises:
211 |         ValueError: For invalid URL or repository not found
212 |         PermissionError: For rate limit or authentication issues
213 |         ConnectionError: For network connectivity issues
214 |     """
215 |     # Parse GitHub URL
216 |     try:
217 |         owner, repo = parse_github_url(url)
218 |     except ValueError as e:
219 |         raise ValueError(str(e))
220 |     
221 |     # Check cache first
222 |     cache_key = f"{owner}/{repo}"
223 |     if cache_key in _repo_cache:
224 |         logger.info(f"Returning cached data for {cache_key}")
225 |         return _repo_cache[cache_key]
226 |     
227 |     logger.info(f"Fetching repository data for {owner}/{repo}")
228 |     
229 |     # Set up headers
230 |     headers = {
231 |         "Accept": "application/vnd.github.v3+json",
232 |         "User-Agent": "DevOnboard-App"
233 |     }
234 |     
235 |     # Add authorization header if token exists
236 |     if GITHUB_TOKEN:
237 |         headers["Authorization"] = f"token {GITHUB_TOKEN}"
238 |         logger.info("Using GitHub token for authentication")
239 |     else:
240 |         logger.warning("No GitHub token found - rate limits will be lower")
241 |     
242 |     try:
243 |         async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
244 |             # Step 1: Get repository metadata
245 |             repo_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
246 |             
247 |             try:
248 |                 response = await client.get(repo_url, headers=headers)
249 |             except httpx.ConnectError:
250 |                 raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
251 |             except httpx.TimeoutException:
252 |                 raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
253 |             
254 |             # Handle HTTP errors
255 |             if response.status_code == 401:
256 |                 raise PermissionError("Invalid GitHub token. Check your GITHUB_TOKEN in .env")
257 |             elif response.status_code == 403:
258 |                 # Check if it's a rate limit issue
259 |                 if "rate limit" in response.text.lower():
260 |                     raise PermissionError("GitHub API rate limit exceeded. Add a GITHUB_TOKEN to .env")
261 |                 raise PermissionError("GitHub API rate limit exceeded. Add a GITHUB_TOKEN to .env")
262 |             elif response.status_code == 404:
263 |                 raise ValueError("Repository not found. Check the URL and make sure it is public")
264 |             
265 |             response.raise_for_status()
266 |             repo_data = response.json()
267 |             
268 |             # Extract repository metadata
269 |             description = repo_data.get("description", "")
270 |             stars = repo_data.get("stargazers_count", 0)
271 |             language = repo_data.get("language", "")
272 |             default_branch = repo_data.get("default_branch", "main")
273 |             
274 |             # Step 2: Get repository file tree
275 |             tree_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
276 |             
277 |             try:
278 |                 response = await client.get(tree_url, headers=headers)
279 |             except httpx.ConnectError:
280 |                 raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
281 |             except httpx.TimeoutException:
282 |                 raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
283 |             
284 |             if response.status_code == 401:
285 |                 raise PermissionError("Invalid GitHub token. Check your GITHUB_TOKEN in .env")
286 |             elif response.status_code == 403:
287 |                 raise PermissionError("GitHub API rate limit exceeded. Add a GITHUB_TOKEN to .env")
288 |             elif response.status_code == 404:
289 |                 raise ValueError("Repository not found. Check the URL and make sure it is public")
290 |             
291 |             response.raise_for_status()
292 |             tree_data = response.json()
293 |             
294 |             tree = tree_data.get("tree", [])
295 |             
296 |             if not tree:
297 |                 raise ValueError("Repository appears to be empty")
298 |             
299 |             # Step 3: Smart file selection with tiered priority
300 |             file_count = 0
301 |             tier1_files = []
302 |             tier2_candidates = []
303 |             tier3_candidates = []
304 |             
305 |             for item in tree:
306 |                 if item.get("type") != "blob":
307 |                     continue
308 |                 
309 |                 file_count += 1
310 |                 path = item.get("path", "")
311 |                 size = item.get("size", 0)
312 |                 filename = path.split("/")[-1]
313 |                 path_lower = path.lower()
314 |                 
315 |                 # TIER 1: Critical config files (always fetch)
316 |                 if filename in TIER1_FILES:
317 |                     tier1_files.append({"path": path, "size": size, "tier": "TIER1"})
318 |                     continue
319 |                 
320 |                 # TIER 2: Entry points and key patterns (up to 8)
321 |                 tier2_match = False
322 |                 
323 |                 # Check entry point files
324 |                 if filename in TIER2_PATTERNS["entry_points"]:
325 |                     tier2_match = True
326 |                 
327 |                 # Check path keywords
328 |                 if not tier2_match:
329 |                     for keyword in TIER2_PATTERNS["path_keywords"]:
330 |                         if keyword in path_lower:
331 |                             tier2_match = True
332 |                             break
333 |                 
334 |                 if tier2_match:
335 |                     tier2_candidates.append({"path": path, "size": size, "tier": "TIER2"})
336 |                     continue
337 |                 
338 |                 # TIER 3: Additional files with filters
339 |                 # Check if file should be excluded
340 |                 should_exclude = False
341 |                 for exclude_pattern in TIER3_CONFIG["exclude_patterns"]:
342 |                     if exclude_pattern in path_lower:
343 |                         should_exclude = True
344 |                         break
345 |                 
346 |                 if should_exclude:
347 |                     continue
348 |                 
349 |                 # Check size constraints
350 |                 if size < TIER3_CONFIG["min_size"] or size > TIER3_CONFIG["max_size"]:
351 |                     continue
352 |                 
353 |                 # Check if in preferred folders
354 |                 folder = path.split("/")[0] if "/" in path else ""
355 |                 if folder in TIER3_CONFIG["preferred_folders"] or folder == "":
356 |                     tier3_candidates.append({"path": path, "size": size, "tier": "TIER3"})
357 |             
358 |             # Select files: All TIER1 + up to 8 TIER2 + up to 10 TIER3
359 |             files_to_fetch = []
360 |             files_to_fetch.extend(tier1_files)
361 |             files_to_fetch.extend(tier2_candidates[:8])
362 |             files_to_fetch.extend(tier3_candidates[:TIER3_CONFIG["max_files"]])
363 |             
364 |             logger.info(f"Selected {len(tier1_files)} TIER1, {min(8, len(tier2_candidates))} TIER2, "
365 |                        f"{min(TIER3_CONFIG['max_files'], len(tier3_candidates))} TIER3 files "
366 |                        f"(out of {file_count} total files)")
367 |             
368 |             # Step 4: Fetch all selected files in parallel using asyncio.gather()
369 |             fetch_tasks = [
370 |                 _fetch_single_file(
371 |                     client, owner, repo,
372 |                     file_info["path"],
373 |                     headers,
374 |                     file_info["size"],
375 |                     file_info["tier"]
376 |                 )
377 |                 for file_info in files_to_fetch
378 |             ]
379 |             
380 |             # Execute all fetches in parallel
381 |             results = await asyncio.gather(*fetch_tasks, return_exceptions=False)
382 |             
383 |             # Filter out None results (failed fetches)
384 |             files = [result for result in results if result is not None]
385 |             
386 |             logger.info(f"Successfully fetched {len(files)} files out of {file_count} total files")
387 |             
388 |             # Prepare result
389 |             result = {
390 |                 "owner": owner,
391 |                 "repo": repo,
392 |                 "description": description,
393 |                 "stars": stars,
394 |                 "language": language,
395 |                 "files": files,
396 |                 "file_count": file_count
397 |             }
398 |             
399 |             # Cache the result
400 |             _repo_cache[cache_key] = result
401 |             
402 |             return result
403 |             
404 |     except httpx.ConnectError:
405 |         raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
406 |     except httpx.TimeoutException:
407 |         raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
408 |     except (ValueError, PermissionError, ConnectionError):
409 |         # Re-raise these as-is
410 |         raise
411 |     except Exception as e:
412 |         logger.error(f"Unexpected error: {e}", exc_info=True)
413 |         raise ConnectionError(f"Failed to fetch repository data: {str(e)}")
414 | 
415 | 
416 | # Made with Bob

</file_content>

<file_content path="backend/doc_generator.py">
  1 | """
  2 | Documentation generator for creating onboarding documents from repository data.
  3 | Enhanced version with deeper analysis and structured sections.
  4 | """
  5 | import os
  6 | import re
  7 | from typing import Dict, Any, List, Optional, Tuple
  8 | import logging
  9 | import json
 10 | import watsonx_client
 11 | 
 12 | # Initialize logger for tracking documentation generation process
 13 | logger = logging.getLogger(__name__)
 14 | 
 15 | # Maximum path length to prevent filesystem issues and path traversal attacks
 16 | MAX_PATH_LENGTH = 4096
 17 | 
 18 | 
 19 | def normalize_path(path: str) -> str:
 20 |     """
 21 |     Normalize file path to use forward slashes and handle edge cases.
 22 |     
 23 |     Args:
 24 |         path: File path to normalize
 25 |         
 26 |     Returns:
 27 |         Normalized path with forward slashes
 28 |     """
 29 |     if not path:
 30 |         return ""
 31 |     
 32 |     normalized = path.replace("\\", "/")
 33 |     normalized = re.sub(r'/+', '/', normalized)
 34 |     
 35 |     if len(normalized) > MAX_PATH_LENGTH:
 36 |         logger.warning(f"Path exceeds maximum length: {normalized[:100]}...")
 37 |         normalized = normalized[:MAX_PATH_LENGTH]
 38 |     
 39 |     return normalized
 40 | 
 41 | 
 42 | def safe_get_content(file_dict: Dict[str, Any]) -> Optional[str]:
 43 |     """
 44 |     Safely extract content from file dictionary with validation.
 45 |     
 46 |     Args:
 47 |         file_dict: File dictionary that may contain content
 48 |         
 49 |     Returns:
 50 |         File content as string or None if invalid
 51 |     """
 52 |     if not file_dict or not isinstance(file_dict, dict):
 53 |         return None
 54 |     
 55 |     content = file_dict.get("content")
 56 |     
 57 |     if content is None or content == "":
 58 |         return None
 59 |     
 60 |     if not isinstance(content, str):
 61 |         try:
 62 |             content = str(content)
 63 |         except Exception as e:
 64 |             logger.warning(f"Failed to convert content to string: {e}")
 65 |             return None
 66 |     
 67 |     if '\x00' in content:
 68 |         logger.warning("Binary content detected, skipping")
 69 |         return None
 70 |     
 71 |     return content
 72 | 
 73 | 
 74 | def detect_language_and_framework(files: List[Dict[str, Any]]) -> Tuple[str, str]:
 75 |     """
 76 |     Detect primary programming language and framework from files.
 77 |     
 78 |     Args:
 79 |         files: List of file dictionaries
 80 |         
 81 |     Returns:
 82 |         Tuple of (language, framework)
 83 |     """
 84 |     language = "Unknown"
 85 |     framework = "Unknown"
 86 |     
 87 |     # Count file extensions
 88 |     extensions = {}
 89 |     for f in files:
 90 |         if not f or not isinstance(f, dict):
 91 |             continue
 92 |         path = normalize_path(f.get("path", ""))
 93 |         if "." in path:
 94 |             ext = path.split(".")[-1].lower()
 95 |             extensions[ext] = extensions.get(ext, 0) + 1
 96 |     
 97 |     # Determine primary language
 98 |     if extensions.get("py", 0) > 0:
 99 |         language = "Python"
100 |     elif extensions.get("js", 0) > 0 or extensions.get("ts", 0) > 0:
101 |         language = "JavaScript/TypeScript"
102 |     elif extensions.get("java", 0) > 0:
103 |         language = "Java"
104 |     elif extensions.get("go", 0) > 0:
105 |         language = "Go"
106 |     elif extensions.get("rs", 0) > 0:
107 |         language = "Rust"
108 |     
109 |     # Detect framework from package files
110 |     for f in files:
111 |         if not f or not isinstance(f, dict):
112 |             continue
113 |         path = normalize_path(f.get("path", ""))
114 |         content = safe_get_content(f)
115 |         
116 |         if path == "package.json" and content:
117 |             try:
118 |                 data = json.loads(content)
119 |                 deps = data.get("dependencies", {})
120 |                 if "express" in deps:
121 |                     framework = "Express.js"
122 |                 elif "next" in deps:
123 |                     framework = "Next.js"
124 |                 elif "react" in deps:
125 |                     framework = "React"
126 |                 elif "vue" in deps:
127 |                     framework = "Vue.js"
128 |                 elif "angular" in deps or "@angular/core" in deps:
129 |                     framework = "Angular"
130 |             except:
131 |                 pass
132 |         
133 |         elif path == "requirements.txt" and content:
134 |             if "fastapi" in content.lower():
135 |                 framework = "FastAPI"
136 |             elif "django" in content.lower():
137 |                 framework = "Django"
138 |             elif "flask" in content.lower():
139 |                 framework = "Flask"
140 |         
141 |         elif path == "go.mod" and content:
142 |             if "gin-gonic/gin" in content:
143 |                 framework = "Gin"
144 |             elif "gorilla/mux" in content:
145 |                 framework = "Gorilla Mux"
146 |         
147 |         elif path == "Cargo.toml" and content:
148 |             if "actix-web" in content:
149 |                 framework = "Actix Web"
150 |             elif "rocket" in content:
151 |                 framework = "Rocket"
152 |     
153 |     return language, framework
154 | 
155 | 
156 | def extract_project_overview(files: List[Dict[str, Any]]) -> Dict[str, Any]:
157 |     """
158 |     Extract comprehensive project overview.
159 |     
160 |     Returns dict with: description, language, framework, dependencies, project_type
161 |     """
162 |     overview = {
163 |         "description": "",
164 |         "language": "Unknown",
165 |         "framework": "Unknown",
166 |         "dependencies": [],
167 |         "project_type": "Other"
168 |     }
169 |     
170 |     # Detect language and framework
171 |     overview["language"], overview["framework"] = detect_language_and_framework(files)
172 |     
173 |     # Extract README description
174 |     for f in files:
175 |         if not f or not isinstance(f, dict):
176 |             continue
177 |         path = normalize_path(f.get("path", ""))
178 |         if path.lower() in ["readme.md", "readme.rst", "readme.txt", "readme"]:
179 |             content = safe_get_content(f)
180 |             if content:
181 |                 lines = content.split("\n")
182 |                 desc_lines = []
183 |                 for line in lines:
184 |                     line = line.strip()
185 |                     if line and not line.startswith("#") and not line.startswith("!"):
186 |                         desc_lines.append(line)
187 |                         if len(" ".join(desc_lines)) > 300:
188 |                             break
189 |                 overview["description"] = " ".join(desc_lines[:3])
190 |             break
191 |     
192 |     # Extract dependencies
193 |     for f in files:
194 |         if not f or not isinstance(f, dict):
195 |             continue
196 |         path = normalize_path(f.get("path", ""))
197 |         content = safe_get_content(f)
198 |         
199 |         if path == "package.json" and content:
200 |             try:
201 |                 data = json.loads(content)
202 |                 deps = data.get("dependencies", {})
203 |                 overview["dependencies"] = list(deps.keys())[:10]
204 |             except:
205 |                 pass
206 |         
207 |         elif path == "requirements.txt" and content:
208 |             lines = content.split("\n")[:10]
209 |             deps = []
210 |             for line in lines:
211 |                 line = line.strip()
212 |                 if line and not line.startswith("#"):
213 |                     pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
214 |                     if pkg:
215 |                         deps.append(pkg)
216 |             overview["dependencies"] = deps
217 |     
218 |     # Determine project type
219 |     has_api = any("api" in f.get("path", "").lower() or "route" in f.get("path", "").lower() 
220 |                   for f in files if f and isinstance(f, dict))
221 |     has_frontend = any(f.get("path", "").lower().endswith((".jsx", ".tsx", ".vue")) 
222 |                        for f in files if f and isinstance(f, dict))
223 |     has_cli = any("cli" in f.get("path", "").lower() or "command" in f.get("path", "").lower()
224 |                   for f in files if f and isinstance(f, dict))
225 |     
226 |     if has_api and has_frontend:
227 |         overview["project_type"] = "Full-stack"
228 |     elif has_api:
229 |         overview["project_type"] = "API"
230 |     elif has_frontend:
231 |         overview["project_type"] = "Frontend"
232 |     elif has_cli:
233 |         overview["project_type"] = "CLI"
234 |     elif any(path in ["setup.py", "pyproject.toml", "package.json"] 
235 |              for f in files if f and isinstance(f, dict) 
236 |              for path in [normalize_path(f.get("path", ""))]):
237 |         overview["project_type"] = "Library"
238 |     
239 |     return overview
240 | 
241 | 
242 | def analyze_architecture(files: List[Dict[str, Any]]) -> Dict[str, Any]:
243 |     """
244 |     Analyze architecture: folder structure, entry point, database, external services.
245 |     """
246 |     architecture = {
247 |         "folders": {},
248 |         "entry_point": None,
249 |         "database":  None,
250 |         "external_services": []
251 |     }
252 |     
253 |     # Analyze folder structure
254 |     folders = {}
255 |     for f in files:
256 |         if not f or not isinstance(f, dict):
257 |             continue
258 |         path = normalize_path(f.get("path", ""))
259 |         if "/" in path:
260 |             folder = path.split("/")[0]
261 |             if folder not in folders:
262 |                 folders[folder] = []
263 |             folders[folder].append(path)
264 |     
265 |     # Categorize folders
266 |     folder_descriptions = {
267 |         "src": "Source code directory",
268 |         "app": "Application logic",
269 |         "backend": "Server-side code",
270 |         "frontend": "Client-side code",
271 |         "api": "API endpoints",
272 |         "components": "UI components",
273 |         "utils": "Utility functions",
274 |         "lib": "Shared libraries",
275 |         "config": "Configuration files",
276 |         "tests": "Test files",
277 |         "docs": "Documentation",
278 |         "public": "Static assets",
279 |         "static": "Static files",
280 |         "assets": "Media files",
281 |         "models": "Data models",
282 |         "routes": "Routing logic",
283 |         "controllers": "Business logic",
284 |         "services": "Service layer",
285 |         "middleware": "Middleware functions"
286 |     }
287 |     
288 |     for folder, file_list in folders.items():
289 |         description = folder_descriptions.get(folder, f"Contains {len(file_list)} files")
290 |         architecture["folders"][folder] = description
291 |     
292 |     # Find entry point
293 |     entry_points = ["main.py", "app.py", "server.py", "index.js", "app.js", "server.js", "main.js", "index.ts", "app.ts"]
294 |     for f in files:
295 |         if not f or not isinstance(f, dict):
296 |             continue
297 |         path = normalize_path(f.get("path", ""))
298 |         filename = path.split("/")[-1]
299 |         if filename in entry_points:
300 |             architecture["entry_point"] = path
301 |             break
302 |     
303 |     # Detect database
304 |     db_indicators = ["sqlite", "postgres", "mysql", "mongodb", "redis", "prisma", "sequelize", "mongoose", "sqlalchemy"]
305 |     for f in files:
306 |         content = safe_get_content(f)
307 |         if content:
308 |             content_lower = content.lower()
309 |             for db in db_indicators:
310 |                 if db in content_lower:
311 |                     architecture["database"] = db.title()
312 |                     break
313 |             if architecture["database"]:
314 |                 break
315 |     
316 |     # Detect external services
317 |     service_indicators = ["aws", "stripe", "twilio", "sendgrid", "firebase", "auth0", "oauth", "jwt"]
318 |     for f in files:
319 |         content = safe_get_content(f)
320 |         if content:
321 |             content_lower = content.lower()
322 |             for service in service_indicators:
323 |                 if service in content_lower and service not in architecture["external_services"]:
324 |                     architecture["external_services"].append(service.upper())
325 |     
326 |     return architecture
327 | 
328 | 
329 | def find_key_files_map(files: List[Dict[str, Any]]) -> List[Dict[str, str]]:
330 |     """
331 |     Create a map of TIER 1 and TIER 2 files with descriptions.
332 |     """
333 |     key_files = []
334 |     
335 |     for f in files:
336 |         if not f or not isinstance(f, dict):
337 |             continue
338 |         
339 |         tier = f.get("tier", "")
340 |         if tier not in ["TIER1", "TIER2"]:
341 |             continue
342 |         
343 |         path = normalize_path(f.get("path", ""))
344 |         filename = path.split("/")[-1]
345 |         
346 |         # Generate description based on file type
347 |         description = ""
348 |         if filename == "README.md":
349 |             description = "Project documentation and setup instructions"
350 |         elif filename == "package.json":
351 |             description = "Node.js dependencies and scripts configuration"
352 |         elif filename == "requirements.txt":
353 |             description = "Python dependencies specification"
354 |         elif filename in ["main.py", "app.py", "server.py"]:
355 |             description = "Main application entry point"
356 |         elif filename in ["index.js", "app.js", "server.js", "main.js"]:
357 |             description = "JavaScript application entry point"
358 |         elif "route" in path.lower():
359 |             description = "API routing and endpoint definitions"
360 |         elif "auth" in path.lower():
361 |             description = "Authentication and authorization logic"
362 |         elif "model" in path.lower():
363 |             description = "Data models and database schemas"
364 |         elif "config" in path.lower():
365 |             description = "Application configuration settings"
366 |         elif "controller" in path.lower():
367 |             description = "Business logic and request handlers"
368 |         else:
369 |             description = f"Important {tier.lower()} file for the project"
370 |         
371 |         key_files.append({
372 |             "path": path,
373 |             "description": description,
374 |             "tier": tier
375 |         })
376 |     
377 |     return key_files
378 | 
379 | 
380 | def analyze_authentication(files: List[Dict[str, Any]]) -> Dict[str, Any]:
381 |     """
382 |     Analyze authentication and security implementation.
383 |     """
384 |     auth_info = {
385 |         "has_auth": False,
386 |         "auth_methods": [],
387 |         "auth_files": []
388 |     }
389 |     
390 |     auth_keywords = ["jwt", "oauth", "passport", "bcrypt", "session", "cookie", "token", "auth", "login", "middleware"]
391 |     
392 |     for f in files:
393 |         content = safe_get_content(f)
394 |         path = normalize_path(f.get("path", ""))
395 |         
396 |         if content:
397 |             content_lower = content.lower()
398 |             path_lower = path.lower()
399 |             
400 |             # Check for auth keywords in content or path
401 |             found_auth = False
402 |             for keyword in auth_keywords:
403 |                 if keyword in content_lower or keyword in path_lower:
404 |                     found_auth = True
405 |                     if keyword not in auth_info["auth_methods"]:
406 |                         auth_info["auth_methods"].append(keyword.upper())
407 |             
408 |             if found_auth:
409 |                 auth_info["has_auth"] = True
410 |                 auth_info["auth_files"].append(path)
411 |     
412 |     return auth_info
413 | 
414 | 
415 | def find_api_endpoints(files: List[Dict[str, Any]]) -> List[Dict[str, str]]:
416 |     """
417 |     Find API endpoints from route definitions.
418 |     """
419 |     endpoints = []
420 |     
421 |     # Patterns for different frameworks
422 |     patterns = {
423 |         "express": [
424 |             r"app\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
425 |             r"router\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"
426 |         ],
427 |         "fastapi": [
428 |             r"@app\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
429 |             r"@router\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"
430 |         ],
431 |         "flask": [
432 |             r"@app\.route\s*\(\s*['\"]([^'\"]+)['\"].*methods\s*=\s*\[['\"]([^'\"]+)['\"]",
433 |             r"@app\.route\s*\(\s*['\"]([^'\"]+)['\"]"
434 |         ],
435 |         "django": [
436 |             r"path\s*\(\s*['\"]([^'\"]+)['\"]"
437 |         ]
438 |     }
439 |     
440 |     for f in files:
441 |         content = safe_get_content(f)
442 |         if not content:
443 |             continue
444 |         
445 |         path = normalize_path(f.get("path", ""))
446 |         
447 |         # Try all patterns
448 |         for framework, pattern_list in patterns.items():
449 |             for pattern in pattern_list:
450 |                 matches = re.findall(pattern, content, re.IGNORECASE)
451 |                 for match in matches:
452 |                     if isinstance(match, tuple):
453 |                         if len(match) == 2:
454 |                             method, endpoint = match
455 |                             endpoints.append({"method": method.upper(), "path": endpoint, "file": path})
456 |                         else:
457 |                             endpoint = match[0] if match else ""
458 |                             endpoints.append({"method": "GET", "path": endpoint, "file": path})
459 |                     else:
460 |                         endpoints.append({"method": "GET", "path": match, "file": path})
461 |     
462 |     # Remove duplicates and limit to 15
463 |     seen = set()
464 |     unique_endpoints = []
465 |     for ep in endpoints:
466 |         key = f"{ep['method']} {ep['path']}"
467 |         if key not in seen:
468 |             seen.add(key)
469 |             unique_endpoints.append(ep)
470 |             if len(unique_endpoints) >= 15:
471 |                 break
472 |     
473 |     return unique_endpoints
474 | 
475 | 
476 | def find_data_models(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
477 |     """
478 |     Find data models and schemas.
479 |     """
480 |     models = []
481 |     
482 |     # Patterns for different ORMs/frameworks
483 |     model_patterns = {
484 |         "mongoose": r"const\s+(\w+)\s*=\s*mongoose\.model",
485 |         "sequelize": r"const\s+(\w+)\s*=\s*sequelize\.define",
486 |         "sqlalchemy": r"class\s+(\w+)\s*\([^)]*Model[^)]*\)",
487 |         "django": r"class\s+(\w+)\s*\([^)]*models\.Model[^)]*\)",
488 |         "prisma": r"model\s+(\w+)\s*{",
489 |         "typeorm": r"@Entity\s*\(\s*['\"]?(\w+)['\"]?\s*\)",
490 |         "pydantic": r"class\s+(\w+)\s*\([^)]*BaseModel[^)]*\)"
491 |     }
492 |     
493 |     for f in files:
494 |         content = safe_get_content(f)
495 |         if not content:
496 |             continue
497 |         
498 |         path = normalize_path(f.get("path", ""))
499 |         
500 |         for orm, pattern in model_patterns.items():
501 |             matches = re.findall(pattern, content, re.IGNORECASE)
502 |             for match in matches:
503 |                 model_name = match if isinstance(match, str) else match[0]
504 |                 
505 |                 # Extract fields (simplified)
506 |                 fields = []
507 |                 if orm == "prisma":
508 |                     field_pattern = r"(\w+)\s+(\w+)"
509 |                     field_matches = re.findall(field_pattern, content)
510 |                     fields = [f"{name}: {type_}" for name, type_ in field_matches[:5]]
511 |                 
512 |                 models.append({
513 |                     "name": model_name,
514 |                     "orm": orm,
515 |                     "file": path,
516 |                     "fields": fields
517 |                 })
518 |     
519 |     return models
520 | 
521 | 
522 | def generate_feature_guide_by_stack(language: str, framework: str, folders: Dict[str, str]) -> str:
523 |     """
524 |     Generate framework-specific feature addition guide.
525 |     """
526 |     guide = []
527 |     
528 |     if framework in ["Express.js", "Node.js"]:
529 |         guide.extend([
530 |             "#### For Express.js Features:\n\n",
531 |             "1. **Plan the Feature**\n",
532 |             "   - Define API endpoints needed\n",
533 |             "   - Identify data models required\n",
534 |             "   - Plan middleware integration\n\n",
535 |             
536 |             "2. **Create/Update Models**\n",
537 |             f"   - Add models in `{'models/' if 'models' in folders else 'src/models/'}`\n",
538 |             "   - Define Mongoose schemas or Sequelize models\n",
539 |             "   - Add validation rules\n\n",
540 |             
541 |             "3. **Add Routes**\n",
542 |             f"   - Create route files in `{'routes/' if 'routes' in folders else 'src/routes/'}`\n",
543 |             "   - Define GET, POST, PUT, DELETE endpoints\n",
544 |             "   - Add route validation middleware\n\n",
545 |             
546 |             "4. **Implement Controllers**\n",
547 |             f"   - Add business logic in `{'controllers/' if 'controllers' in folders else 'src/controllers/'}`\n",
548 |             "   - Handle request/response logic\n",
549 |             "   - Add error handling\n\n",
550 |             
551 |             "5. **Test and Document**\n",
552 |             "   - Write unit tests for controllers\n",
553 |             "   - Test API endpoints with Postman/curl\n",
554 |             "   - Update API documentation\n\n"
555 |         ])
556 |     
557 |     elif framework in ["FastAPI", "Flask", "Django"]:
558 |         guide.extend([
559 |             f"#### For {framework} Features:\n\n",
560 |             "1. **Define Models**\n",
561 |             f"   - Add models in `{'models/' if 'models' in folders else 'app/models/'}`\n",
562 |             "   - Define Pydantic models (FastAPI) or SQLAlchemy models\n",
563 |             "   - Add field validation\n\n",
564 |             
565 |             "2. **Create Endpoints**\n",
566 |             f"   - Add routes in `{'routes/' if 'routes' in folders else 'app/routes/'}`\n",
567 |             "   - Use decorators (@app.get, @app.post, etc.)\n",
568 |             "   - Add request/response models\n\n",
569 |             
570 |             "3. **Business Logic**\n",
571 |             f"   - Implement services in `{'services/' if 'services' in folders else 'app/services/'}`\n",
572 |             "   - Add database operations\n",
573 |             "   - Handle business rules\n\n",
574 |             
575 |             "4. **Testing**\n",
576 |             "   - Write pytest tests\n",
577 |             "   - Test endpoints with TestClient\n",
578 |             "   - Add integration tests\n\n"
579 |         ])
580 |     
581 |     elif framework in ["React", "Next.js", "Vue.js"]:
582 |         guide.extend([
583 |             f"#### For {framework} Features:\n\n",
584 |             "1. **Plan Components**\n",
585 |             "   - Design component hierarchy\n",
586 |             "   - Plan state management\n",
587 |             "   - Define prop interfaces\n\n",
588 |             
589 |             "2. **Create Components**\n",
590 |             f"   - Add components in `{'components/' if 'components' in folders else 'src/components/'}`\n",
591 |             "   - Implement reusable UI elements\n",
592 |             "   - Add TypeScript interfaces\n\n",
593 |             
594 |             "3. **Add Pages/Routes**\n",
595 |             f"   - Create pages in `{'pages/' if 'pages' in folders else 'src/pages/'}`\n",
596 |             "   - Update routing configuration\n",
597 |             "   - Add navigation links\n\n",
598 |             
599 |             "4. **State Management**\n",
600 |             "   - Add hooks or store logic\n",
601 |             "   - Integrate with API endpoints\n",
602 |             "   - Handle loading states\n\n"
603 |         ])
604 |     
605 |     else:
606 |         guide.extend([
607 |             "#### General Development Process:\n\n",
608 |             "1. **Understand Requirements**\n",
609 |             "   - Review feature specifications\n",
610 |             "   - Identify affected components\n\n",
611 |             
612 |             "2. **Implement Core Logic**\n",
613 |             "   - Follow existing code patterns\n",
614 |             "   - Add appropriate tests\n\n",
615 |             
616 |             "3. **Integration**\n",
617 |             "   - Update configuration if needed\n",
618 |             "   - Test with existing features\n\n"
619 |         ])
620 |     
621 |     return "".join(guide)
622 | 
623 | 
624 | def extract_getting_started(files: List[Dict[str, Any]]) -> Dict[str, Any]:
625 |     """
626 |     Extract getting started information from README and package files.
627 |     """
628 |     getting_started = {
629 |         "install_command": None,
630 |         "run_command": None,
631 |         "env_vars": []
632 |     }
633 |     
634 |     # Check README for commands
635 |     for f in files:
636 |         if not f or not isinstance(f, dict):
637 |             continue
638 |         path = normalize_path(f.get("path", ""))
639 |         if path.lower() in ["readme.md", "readme.rst"]:
640 |             content = safe_get_content(f)
641 |             if content:
642 |                 # Look for install commands
643 |                 install_patterns = [
644 |                     r"npm install",
645 |                     r"pip install -r requirements\.txt",
646 |                     r"yarn install",
647 |                     r"go mod download",
648 |                     r"cargo build"
649 |                 ]
650 |                 
651 |                 for pattern in install_patterns:
652 |                     match = re.search(pattern, content, re.IGNORECASE)
653 |                     if match:
654 |                         getting_started["install_command"] = match.group()
655 |                         break
656 |                 
657 |                 # Look for run commands
658 |                 run_patterns = [
659 |                     r"npm (start|run dev)",
660 |                     r"python (main\.py|app\.py)",
661 |                     r"yarn (start|dev)",
662 |                     r"go run",
663 |                     r"cargo run"
664 |                 ]
665 |                 
666 |                 for pattern in run_patterns:
667 |                     match = re.search(pattern, content, re.IGNORECASE)
668 |                     if match:
669 |                         getting_started["run_command"] = match.group()
670 |                         break
671 |     
672 |     # Check package.json for scripts
673 |     for f in files:
674 |         if not f or not isinstance(f, dict):
675 |             continue
676 |         path = normalize_path(f.get("path", ""))
677 |         if path == "package.json":
678 |             content = safe_get_content(f)
679 |             if content:
680 |                 try:
681 |                     data = json.loads(content)
682 |                     scripts = data.get("scripts", {})
683 |                     if "start" in scripts:
684 |                         getting_started["run_command"] = "npm start"
685 |                     elif "dev" in scripts:
686 |                         getting_started["run_command"] = "npm run dev"
687 |                 except:
688 |                     pass
689 |     
690 |     # Check .env.example for environment variables
691 |     for f in files:
692 |         if not f or not isinstance(f, dict):
693 |             continue
694 |         path = normalize_path(f.get("path", ""))
695 |         if path == ".env.example":
696 |             content = safe_get_content(f)
697 |             if content:
698 |                 lines = content.split("\n")
699 |                 for line in lines:
700 |                     line = line.strip()
701 |                     if line and not line.startswith("#") and "=" in line:
702 |                         var_name = line.split("=")[0].strip()
703 |                         getting_started["env_vars"].append(var_name)
704 |     
705 |     return getting_started
706 | 
707 | 
708 | def get_ai_insights(raw_doc: str, metadata: dict) -> str:
709 |     if not watsonx_client.is_configured():
710 |         return ""
711 | 
712 |     prompt = f"""You are a senior software architect reviewing
713 | a code repository. Be concise and specific.
714 | 
715 | Repository details:
716 | - Language: {metadata.get('language', 'Unknown')}
717 | - Framework: {metadata.get('framework', 'Unknown')}
718 | - Has Authentication: {metadata.get('has_auth', False)}
719 | - Has Database: {metadata.get('has_database', False)}
720 | - API Endpoints found: {metadata.get('endpoint_count', 0)}
721 | - Total files analyzed: {metadata.get('total_files_analyzed', 0)}
722 | 
723 | Documentation excerpt:
724 | {raw_doc[:2500]}
725 | 
726 | Provide exactly these four things:
727 | 1. Architecture pattern (1 sentence): MVC / microservices /
728 |    monolith / JAMstack / other
729 | 2. Top 3 files a new developer must read first and why
730 | 3. One potential risk or gotcha in this codebase
731 | 4. Complexity rating: Simple / Medium / Complex with one reason
732 | 
733 | Keep total response under 300 words."""
734 | 
735 |     cache_key = (f"insights_"
736 |                  f"{metadata.get('owner', 'x')}_"
737 |                  f"{metadata.get('repo', 'x')}")
738 |     try:
739 |         return watsonx_client.generate_text(
740 |             prompt=prompt,
741 |             cache_key=cache_key,
742 |             max_tokens=400
743 |         )
744 |     except Exception as e:
745 |         print(f"[insights] watsonx failed: {e}")
746 |         return ""
747 | 
748 | 
749 | def generate_onboarding_doc(repo_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
750 |     """
751 |     Generate a comprehensive onboarding document with structured metadata.
752 |     
753 |     Args:
754 |         repo_data: Repository data from fetch_repo_data()
755 |         
756 |     Returns:
757 |         Tuple of (markdown_document, metadata_dict)
758 |     """
759 |     if not repo_data or not isinstance(repo_data, dict):
760 |         raise ValueError("Invalid repository data: must be a dictionary")
761 |     
762 |     files = repo_data.get("files", [])
763 |     if not files:
764 |         raise ValueError("No files found in repository data")
765 |     
766 |     logger.info(f"Generating enhanced onboarding document for {len(files)} files")
767 |     
768 |     # Extract all analysis data
769 |     overview = extract_project_overview(files)
770 |     architecture = analyze_architecture(files)
771 |     key_files = find_key_files_map(files)
772 |     auth_info = analyze_authentication(files)
773 |     endpoints = find_api_endpoints(files)
774 |     models = find_data_models(files)
775 |     getting_started = extract_getting_started(files)
776 |     
777 |     # Build metadata
778 |     metadata = {
779 |         "language": overview["language"],
780 |         "framework": overview["framework"],
781 |         "project_type": overview["project_type"],
782 |         "has_auth": auth_info["has_auth"],
783 |         "has_database": architecture["database"] is not None,
784 |         "endpoint_count": len(endpoints),
785 |         "model_count": len(models),
786 |         "tier1_files": [f["path"] for f in key_files if f.get("tier") == "TIER1"],
787 |         "tier2_files": [f["path"] for f in key_files if f.get("tier") == "TIER2"],
788 |         "total_files_analyzed": len(files)
789 |     }
790 |     
791 |     # Build markdown document
792 |     doc_parts = []
793 |     
794 |     # Header
795 |     doc_parts.extend([
796 |         f"# {repo_data.get('repo', 'Repository')} - Developer Onboarding Guide\n\n",
797 |         "*Comprehensive auto-generated documentation for faster onboarding*\n\n",
798 |         "---\n\n"
799 |     ])
800 |     
801 |     # 1. PROJECT OVERVIEW
802 |     doc_parts.extend([
803 |         "## 📋 PROJECT OVERVIEW\n\n",
804 |         f"**What this project does:** {overview['description'] or 'No description available from README'}\n\n",
805 |         f"**Primary Language:** {overview['language']}\n\n",
806 |         f"**Framework:** {overview['framework']}\n\n",
807 |         f"**Project Type:** {overview['project_type']}\n\n"
808 |     ])
809 |     
810 |     if overview["dependencies"]:
811 |         doc_parts.append(f"**Key Dependencies:** {', '.join(overview['dependencies'][:8])}\n\n")
812 |     
813 |     doc_parts.append("---\n\n")
814 |     
815 |     # 2. ARCHITECTURE SUMMARY
816 |     doc_parts.extend([
817 |         "## 🏗️ ARCHITECTURE SUMMARY\n\n",
818 |         "### Folder Structure\n"
819 |     ])
820 |     
821 |     for folder, description in architecture["folders"].items():
822 |         doc_parts.append(f"- **`{folder}/`** - {description}\n")
823 |     
824 |     doc_parts.append("\n")
825 |     
826 |     if architecture["entry_point"]:
827 |         doc_parts.append(f"**Application Entry Point:** `{architecture['entry_point']}`\n\n")
828 |     
829 |     if architecture["database"]:
830 |         doc_parts.append(f"**Database:** {architecture['database']}\n\n")
831 |     
832 |     if architecture["external_services"]:
833 |         doc_parts.append(f"**External Services:** {', '.join(architecture['external_services'])}\n\n")
834 |     
835 |     doc_parts.append("---\n\n")
836 |     
837 |     # 3. KEY FILES MAP
838 |     doc_parts.extend([
839 |         "## 🗂️ KEY FILES MAP\n\n",
840 |         "*Essential files every developer should understand*\n\n"
841 |     ])
842 |     
843 |     for i, file_info in enumerate(key_files, 1):
844 |         tier_emoji = "🔥" if file_info["tier"] == "TIER1" else "⚡"
845 |         doc_parts.append(f"{i}. {tier_emoji} **`{file_info['path']}`**\n")
846 |         doc_parts.append(f"   {file_info['description']}\n\n")
847 |     
848 |     doc_parts.append("---\n\n")
849 |     
850 |     # 4. AUTHENTICATION & SECURITY
851 |     doc_parts.extend([
852 |         "## 🔐 AUTHENTICATION & SECURITY\n\n"
853 |     ])
854 |     
855 |     if auth_info["has_auth"]:
856 |         doc_parts.append(f"**Authentication Methods:** {', '.join(auth_info['auth_methods'])}\n\n")
857 |         doc_parts.append("**Auth-related Files:**\n")
858 |         for auth_file in auth_info["auth_files"][:5]:
859 |             doc_parts.append(f"- `{auth_file}`\n")
860 |         doc_parts.append("\n")
861 |     else:
862 |         doc_parts.append("No authentication detected in analyzed files.\n\n")
863 |     
864 |     doc_parts.append("---\n\n")
865 |     
866 |     # 5. API ENDPOINTS
867 |     doc_parts.extend([
868 |         "## 🌐 API ENDPOINTS\n\n"
869 |     ])
870 |     
871 |     if endpoints:
872 |         doc_parts.append("| Method | Endpoint | File |\n")
873 |         doc_parts.append("|--------|----------|------|\n")
874 |         for ep in endpoints:
875 |             doc_parts.append(f"| {ep['method']} | `{ep['path']}` | `{ep['file']}` |\n")
876 |         doc_parts.append("\n")
877 |     else:
878 |         doc_parts.append("No API endpoints detected in analyzed files.\n\n")
879 |     
880 |     doc_parts.append("---\n\n")
881 |     
882 |     # 6. DATA MODELS
883 |     doc_parts.extend([
884 |         "## 📊 DATA MODELS\n\n"
885 |     ])
886 |     
887 |     if models:
888 |         for model in models:
889 |             doc_parts.append(f"### {model['name']} ({model['orm'].title()})\n")
890 |             doc_parts.append(f"*File: `{model['file']}`*\n\n")
891 |             if model['fields']:
892 |                 doc_parts.append("**Fields:**\n")
893 |                 for field in model['fields']:
894 |                     doc_parts.append(f"- {field}\n")
895 |                 doc_parts.append("\n")
896 |     else:
897 |         doc_parts.append("No data models detected in analyzed files.\n\n")
898 |     
899 |     doc_parts.append("---\n\n")
900 |     
901 |     # 7. HOW TO ADD A NEW FEATURE
902 |     doc_parts.extend([
903 |         "## 🚀 HOW TO ADD A NEW FEATURE\n\n",
904 |         generate_feature_guide_by_stack(overview["language"], overview["framework"], architecture["folders"])
905 |     ])
906 |     
907 |     doc_parts.append("---\n\n")
908 |     
909 |     # 8. GETTING STARTED
910 |     doc_parts.extend([
911 |         "## 🎯 GETTING STARTED\n\n"
912 |     ])
913 |     
914 |     if getting_started["install_command"]:
915 |         doc_parts.append(f"**Install Dependencies:**\n```bash\n{getting_started['install_command']}\n```\n\n")
916 |     
917 |     if getting_started["run_command"]:
918 |         doc_parts.append(f"**Run the Application:**\n```bash\n{getting_started['run_command']}\n```\n\n")
919 |     
920 |     if getting_started["env_vars"]:
921 |         doc_parts.append("**Environment Variables:**\n")
922 |         for var in getting_started["env_vars"]:
923 |             doc_parts.append(f"- `{var}`\n")
924 |         doc_parts.append("\n")
925 |     
926 |     doc_parts.extend([
927 |         "### Next Steps\n",
928 |         "1. Read through the key files listed above\n",
929 |         "2. Set up your development environment\n",
930 |         "3. Review the architecture and folder structure\n",
931 |         "4. Start with small changes to familiarize yourself\n",
932 |         "5. Follow the feature addition guide for new development\n\n",
933 |         "*Happy coding! 🎉*\n"
934 |     ])
935 |     
936 |     full_doc = "".join(doc_parts)
937 |     
938 |     # Add AI insights section
939 |     ai_insights = get_ai_insights(full_doc, metadata)
940 |     if ai_insights:
941 |         full_doc += (
942 |             f"\n\n## 🤖 AI Insights"
943 |             f" (Powered by IBM watsonx.ai)\n\n{ai_insights}"
944 |         )
945 |     
946 |     logger.info("Enhanced onboarding document generated successfully")
947 |     
948 |     return full_doc, metadata
949 | 
950 | # Made with Bob

</file_content>

<file_content path="backend/orchestrate_agent.py">
  1 | import re
  2 | import watsonx_client
  3 | 
  4 | 
  5 | def extract_keywords(question: str) -> list:
  6 |     """
  7 |     Extract meaningful keywords from question by removing stop words
  8 |     and adding code-related expansions.
  9 |     """
 10 |     # Remove common stop words
 11 |     stop_words = {
 12 |         'the', 'is', 'are', 'was', 'were', 'a', 'an', 'and', 
 13 |         'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
 14 |         'with', 'by', 'from', 'this', 'that', 'it', 'be',
 15 |         'do', 'does', 'did', 'have', 'has', 'had', 'will',
 16 |         'would', 'could', 'should', 'may', 'might', 'can',
 17 |         'where', 'what', 'how', 'when', 'which', 'who', 'why'
 18 |     }
 19 |     words = re.findall(r'\b\w+\b', question.lower())
 20 |     keywords = [w for w in words if w not in stop_words 
 21 |                 and len(w) > 2]
 22 |     
 23 |     # Also add common code-related expansions
 24 |     expansions = {
 25 |         'auth': ['auth', 'authentication', 'login', 'jwt', 
 26 |                  'token', 'passport', 'middleware', 'session',
 27 |                  'cookie', 'oauth', 'bearer'],
 28 |         'database': ['database', 'db', 'model', 'schema', 
 29 |                      'mongoose', 'sequelize', 'prisma', 
 30 |                      'sqlalchemy', 'migration', 'query'],
 31 |         'route': ['route', 'router', 'endpoint', 'controller',
 32 |                   'handler', 'api', 'path', 'url'],
 33 |         'config': ['config', 'configuration', 'settings', 
 34 |                    'env', 'environment', 'setup'],
 35 |         'test': ['test', 'spec', 'jest', 'pytest', 'unittest'],
 36 |         'deploy': ['deploy', 'dockerfile', 'docker', 
 37 |                    'kubernetes', 'ci', 'cd', 'pipeline']
 38 |     }
 39 |     
 40 |     expanded = list(keywords)
 41 |     for kw in keywords:
 42 |         if kw in expansions:
 43 |             expanded.extend(expansions[kw])
 44 |     
 45 |     return list(set(expanded))
 46 | 
 47 | 
 48 | def find_relevant_files(keywords: list, 
 49 |                         raw_files: list) -> list:
 50 |     """
 51 |     Score each file based on keyword matches and return top 5.
 52 |     """
 53 |     scored_files = []
 54 |     
 55 |     for f in raw_files:
 56 |         score = 0
 57 |         path_lower = f.get("path", "").lower()
 58 |         content_lower = f.get("content", "").lower()
 59 |         
 60 |         for kw in keywords:
 61 |             # Path match scores higher than content match
 62 |             if kw in path_lower:
 63 |                 score += 3
 64 |             # Match in first 200 chars (likely imports/class def)
 65 |             if kw in content_lower[:200]:
 66 |                 score += 2
 67 |             # Match anywhere in content
 68 |             elif kw in content_lower:
 69 |                 score += 1
 70 |         
 71 |         if score > 0:
 72 |             scored_files.append((score, f))
 73 |     
 74 |     # Sort by score descending, take top 5
 75 |     scored_files.sort(key=lambda x: x[0], reverse=True)
 76 |     return [f for _, f in scored_files[:5]]
 77 | 
 78 | 
 79 | def extract_relevant_section(content: str, 
 80 |                               keywords: list) -> str:
 81 |     """
 82 |     Extract sections of content that contain keywords with context.
 83 |     """
 84 |     lines = content.split('\n')
 85 |     relevant_lines = []
 86 |     
 87 |     for i, line in enumerate(lines):
 88 |         line_lower = line.lower()
 89 |         if any(kw in line_lower for kw in keywords):
 90 |             # Include 3 lines before and after for context
 91 |             start = max(0, i - 3)
 92 |             end = min(len(lines), i + 4)
 93 |             relevant_lines.extend(lines[start:end])
 94 |             relevant_lines.append("...")
 95 |     
 96 |     if relevant_lines:
 97 |         return '\n'.join(relevant_lines[:60])
 98 |     # Fallback to first 500 chars
 99 |     return content[:500]
100 | 
101 | 
102 | def build_prompt(question: str, context: str, 
103 |                  relevant_files: list,
104 |                  keywords: list) -> str:
105 |     """
106 |     Build a structured prompt with relevant file sections.
107 |     """
108 |     files_context = ""
109 |     for f in relevant_files:
110 |         section = extract_relevant_section(
111 |             f.get("content", ""), keywords
112 |         )
113 |         files_context += (
114 |             f"\n\n=== FILE: {f['path']} ===\n{section}"
115 |         )
116 |     
117 |     return f"""You are an expert software engineer with deep knowledge of this specific codebase.
118 | 
119 | INSTRUCTIONS:
120 | - Answer ONLY based on the code and files provided below
121 | - Be specific: name exact files, functions, line patterns
122 | - If you see relevant code, quote it briefly
123 | - If not found in provided files, say exactly:
124 |   "Not found in the {len(relevant_files)} analyzed files. Try asking about: [suggest related topic]"
125 | - Never give generic advice not grounded in this code
126 | - Keep answer under 200 words but be complete
127 | 
128 | REPOSITORY SUMMARY:
129 | {context[:800]}
130 | 
131 | MOST RELEVANT SOURCE FILES ({len(relevant_files)} files):
132 | {files_context[:3000] if files_context else "No files matched this query."}
133 | 
134 | QUESTION: {question}
135 | 
136 | SPECIFIC ANSWER (cite file names):"""
137 | 
138 | 
139 | def answer_question(question: str, context: str,
140 |                     raw_files: list = []) -> dict:
141 |     """
142 |     Answer questions about the codebase using improved keyword extraction,
143 |     file matching, and context building.
144 |     """
145 |     keywords = extract_keywords(question)
146 |     relevant_files = find_relevant_files(keywords, raw_files)
147 |     prompt = build_prompt(question, context, 
148 |                           relevant_files, keywords)
149 |     
150 |     cache_key = f"qa_{hash(question[:80])}_{hash(context[:80])}"
151 |     
152 |     try:
153 |         answer = watsonx_client.generate_text(
154 |             prompt=prompt,
155 |             cache_key=cache_key,
156 |             max_tokens=700
157 |         )
158 |         return {
159 |             "answer": answer,
160 |             "sources": [f["path"] for f in relevant_files],
161 |             "keywords_used": keywords,
162 |             "files_searched": len(raw_files),
163 |             "files_matched": len(relevant_files),
164 |             "powered_by": "IBM watsonx.ai"
165 |         }
166 |     except Exception as e:
167 |         print(f"[qa] watsonx error: {e}")
168 |         fallback = ""
169 |         for f in relevant_files[:2]:
170 |             section = extract_relevant_section(
171 |                 f.get("content",""), keywords
172 |             )
173 |             fallback += f"\n{f['path']}:\n{section}\n"
174 |         return {
175 |             "answer": (
176 |                 f"AI unavailable. Relevant code found:\n"
177 |                 f"{fallback[:800] if fallback else 'No matches found.'}"
178 |             ),
179 |             "sources": [f["path"] for f in relevant_files],
180 |             "powered_by": "fallback"
181 |         }
182 | 
183 | 
184 | # Made with Bob

</file_content>

<file_content path="backend/main.py">
  1 | """
  2 | FastAPI application for GitHub repository analysis.
  3 | """
  4 | from dotenv import load_dotenv
  5 | from pathlib import Path
  6 | load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)
  7 | import os
  8 | 
  9 | from fastapi import FastAPI, HTTPException
 10 | from fastapi.middleware.cors import CORSMiddleware
 11 | from pydantic import BaseModel, HttpUrl, field_validator
 12 | from typing import Dict, Any, Optional
 13 | import logging
 14 | import re
 15 | 
 16 | # Import custom modules for GitHub API interaction and documentation generation
 17 | from github_client import fetch_repo_data
 18 | from doc_generator import generate_onboarding_doc
 19 | from orchestrate_agent import answer_question
 20 | import watsonx_client
 21 | 
 22 | # Configure logging to track application behavior and errors
 23 | logging.basicConfig(level=logging.INFO)
 24 | logger = logging.getLogger(__name__)
 25 | 
 26 | # Module-level variables to store the last generated onboarding document and raw files
 27 | _last_onboarding_doc: Optional[str] = None
 28 | _last_repo_files: list = []
 29 | 
 30 | # Initialize FastAPI application with metadata
 31 | app = FastAPI(
 32 |     title="DevOnboard API",
 33 |     description="API for analyzing GitHub repositories",
 34 |     version="1.0.0"
 35 | )
 36 | 
 37 | # Configure CORS (Cross-Origin Resource Sharing) to allow frontend access
 38 | # Reads allowed origins from environment variable, defaults to common development ports
 39 | ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
 40 | 
 41 | # Add CORS middleware to handle cross-origin requests from frontend
 42 | app.add_middleware(
 43 |     CORSMiddleware,
 44 |     allow_origins=ALLOWED_ORIGINS,  # Configurable via environment variable
 45 |     allow_credentials=True,  # Allow cookies and authentication headers
 46 |     allow_methods=["GET", "POST", "OPTIONS"],  # Allowed HTTP methods
 47 |     allow_headers=["Content-Type", "Authorization"],  # Allowed request headers
 48 | )
 49 | 
 50 | 
 51 | class AnalyzeRequest(BaseModel):
 52 |     """
 53 |     Request model for repository analysis endpoint.
 54 |     
 55 |     Attributes:
 56 |         github_url: GitHub repository URL to analyze
 57 |     """
 58 |     github_url: str
 59 | 
 60 |     @field_validator('github_url')
 61 |     @classmethod
 62 |     def validate_github_url(cls, v: str) -> str:
 63 |         """
 64 |         Validate GitHub URL format and content.
 65 |         
 66 |         Performs multiple validation checks:
 67 |         - Removes leading/trailing whitespace
 68 |         - Ensures URL is not empty
 69 |         - Validates GitHub URL pattern (supports http/https, with/without www)
 70 |         - Checks for potentially dangerous special characters
 71 |         
 72 |         Args:
 73 |             cls: Class reference (required for classmethod)
 74 |             v: GitHub URL string to validate
 75 |             
 76 |         Returns:
 77 |             str: Validated and cleaned GitHub URL
 78 |             
 79 |         Raises:
 80 |             ValueError: If URL is empty, has invalid format, or contains dangerous characters
 81 |         """
 82 |         # Strip whitespace from both ends of the URL
 83 |         v = v.strip()
 84 |         
 85 |         # Check for empty or whitespace-only strings
 86 |         if not v:
 87 |             raise ValueError("GitHub URL cannot be empty")
 88 |         
 89 |         # Check for valid GitHub URL pattern using regex
 90 |         # Supports: http/https, with/without www, with/without .git extension
 91 |         github_pattern = r'^https?://(?:www\.)?github\.com/[\w\-\.]+/[\w\-\.]+/?(?:\.git)?$'
 92 |         if not re.match(github_pattern, v, re.IGNORECASE):
 93 |             raise ValueError(
 94 |                 "Invalid GitHub URL format. Expected format: https://github.com/owner/repo"
 95 |             )
 96 |         
 97 |         # Check for special characters that might cause security issues or parsing errors
 98 |         if any(char in v for char in ['<', '>', '"', '{', '}', '|', '\\', '^', '`']):
 99 |             raise ValueError("GitHub URL contains invalid characters")
100 |         
101 |         return v
102 | 
103 |     class Config:
104 |         """Pydantic model configuration with example for API documentation."""
105 |         json_schema_extra = {
106 |             "example": {
107 |                 "github_url": "https://github.com/owner/repo"
108 |             }
109 |         }
110 | 
111 | 
112 | class AnalyzeResponse(BaseModel):
113 |     """
114 |     Response model for repository analysis endpoint.
115 |     
116 |     Attributes:
117 |         onboarding_doc: Generated markdown documentation for the repository
118 |         file_count: Total number of files analyzed in the repository
119 |         metadata: Structured metadata about the analyzed repository
120 |     """
121 |     onboarding_doc: str
122 |     file_count: int
123 |     metadata: Optional[Dict[str, Any]] = None
124 | 
125 | 
126 | class AskRequest(BaseModel):
127 |     """
128 |     Request model for Q&A endpoint.
129 |     
130 |     Attributes:
131 |         question: User's question about the repository
132 |     """
133 |     question: str
134 | 
135 |     @field_validator('question')
136 |     @classmethod
137 |     def validate_question(cls, v: str) -> str:
138 |         """
139 |         Validate question is not empty.
140 |         
141 |         Args:
142 |             cls: Class reference (required for classmethod)
143 |             v: Question string to validate
144 |             
145 |         Returns:
146 |             str: Validated question
147 |             
148 |         Raises:
149 |             ValueError: If question is empty
150 |         """
151 |         v = v.strip()
152 |         if not v:
153 |             raise ValueError("Question cannot be empty")
154 |         if len(v) > 500:
155 |             raise ValueError("Question is too long (max 500 characters)")
156 |         return v
157 | 
158 |     class Config:
159 |         """Pydantic model configuration with example for API documentation."""
160 |         json_schema_extra = {
161 |             "example": {
162 |                 "question": "What are the key files in this repository?"
163 |             }
164 |         }
165 | 
166 | 
167 | class AskResponse(BaseModel):
168 |     """
169 |     Response model for Q&A endpoint.
170 |     
171 |     Attributes:
172 |         answer: AI-generated answer to the question
173 |         sources: List of sources used for the answer
174 |         powered_by: AI model information
175 |         files_searched: Number of files searched
176 |         files_matched: Number of files matched
177 |     """
178 |     answer: str
179 |     sources: list[str]
180 |     powered_by: Optional[str] = None
181 |     files_searched: Optional[int] = None
182 |     files_matched: Optional[int] = None
183 | 
184 | 
185 | @app.get("/")
186 | async def root() -> Dict[str, str]:
187 |     """
188 |     Root endpoint providing API information.
189 |     
190 |     Returns:
191 |         Dict[str, str]: API name, version, and documentation URL
192 |     """
193 |     return {
194 |         "message": "DevOnboard API",
195 |         "version": "1.0.0",
196 |         "docs": "/docs"
197 |     }
198 | 
199 | 
200 | @app.get("/watsonx-status")
201 | async def watsonx_status():
202 |     configured = watsonx_client.is_configured()
203 |     return {
204 |         "watsonx_connected": configured,
205 |         "model": watsonx_client.get_model_id(),
206 |         "region": watsonx_client.get_url(),
207 |         "project_id": watsonx_client.get_project_id_preview(),
208 |         "cache_entries": watsonx_client.get_cache_size(),
209 |         "ibm_bob_built": True,
210 |         "status": "ready" if configured else "not configured"
211 |     }
212 | 
213 | 
214 | @app.get("/health")
215 | async def health():
216 |     configured = watsonx_client.is_configured()
217 |     return {
218 |         "status": "running",
219 |         "watsonx_orchestrate_compatible": True,
220 |         "ibm_bob_built": True,
221 |         "version": "1.0.0",
222 |         "services": {
223 |             "github_api": True,
224 |             "watsonx_ai": configured,
225 |             "model": watsonx_client.get_model_id()
226 |         }
227 |     }
228 | 
229 | 
230 | @app.post("/analyze", response_model=AnalyzeResponse)
231 | async def analyze_repository(request: AnalyzeRequest) -> AnalyzeResponse:
232 |     """
233 |     Analyze a GitHub repository.
234 |     
235 |     Args:
236 |         request: AnalyzeRequest containing the GitHub repository URL
237 |         
238 |     Returns:
239 |         AnalyzeResponse with repository analysis results
240 |         
241 |     Raises:
242 |         HTTPException: If the repository cannot be accessed or analyzed
243 |     """
244 |     global _last_onboarding_doc, _last_repo_files
245 |     
246 |     # Clear watsonx cache for fresh analysis
247 |     watsonx_client.clear_cache()
248 |     
249 |     try:
250 |         # Log the start of repository analysis
251 |         logger.info(f"Analyzing repository: {request.github_url}")
252 |         
253 |         # Fetch repository data from GitHub
254 |         try:
255 |             repo_data = await fetch_repo_data(request.github_url)
256 |         except ValueError as e:
257 |             # Invalid URL or repository not found
258 |             error_msg = str(e)
259 |             logger.error(f"ValueError: {error_msg}")
260 |             print(f"ERROR: {error_msg}")  # Print to terminal for debugging
261 |             if "not found" in error_msg.lower():
262 |                 raise HTTPException(status_code=404, detail=error_msg)
263 |             else:
264 |                 raise HTTPException(status_code=400, detail=error_msg)
265 |         except PermissionError as e:
266 |             # Rate limit or authentication issues
267 |             error_msg = str(e)
268 |             logger.error(f"PermissionError: {error_msg}")
269 |             print(f"ERROR: {error_msg}")  # Print to terminal for debugging
270 |             if "rate limit" in error_msg.lower():
271 |                 raise HTTPException(status_code=429, detail=error_msg)
272 |             else:
273 |                 raise HTTPException(status_code=403, detail=error_msg)
274 |         except ConnectionError as e:
275 |             # Network connectivity issues
276 |             error_msg = str(e)
277 |             logger.error(f"ConnectionError: {error_msg}")
278 |             print(f"ERROR: {error_msg}")  # Print to terminal for debugging
279 |             raise HTTPException(status_code=503, detail=error_msg)
280 |         
281 |         # Extract files from repo_data
282 |         files = repo_data.get("files", [])
283 |         file_count = repo_data.get("file_count", 0)
284 |         
285 |         logger.info(f"Successfully fetched repository data: {file_count} total files, {len(files)} priority files")
286 |         
287 |         # Generate onboarding documentation
288 |         try:
289 |             # Pass the full repo_data dict to the doc generator
290 |             onboarding_doc, metadata = generate_onboarding_doc(repo_data)
291 |             
292 |             # Validate generated documentation is not empty
293 |             if not onboarding_doc or not onboarding_doc.strip():
294 |                 raise ValueError("Generated documentation is empty")
295 |             
296 |             # Store the generated documentation and raw files for use by /ask endpoint
297 |             _last_onboarding_doc = onboarding_doc
298 |             _last_repo_files = files
299 |                 
300 |         except Exception as doc_error:
301 |             # Handle any errors during documentation generation
302 |             error_msg = f"Failed to generate documentation: {str(doc_error)}"
303 |             logger.error(error_msg)
304 |             print(f"ERROR: {error_msg}")  # Print to terminal for debugging
305 |             raise HTTPException(status_code=500, detail=error_msg)
306 |         
307 |         logger.info("Generated onboarding documentation with metadata")
308 |         
309 |         # Return successful response with documentation, file count, and metadata
310 |         return AnalyzeResponse(
311 |             onboarding_doc=onboarding_doc,
312 |             file_count=file_count,
313 |             metadata=metadata
314 |         )
315 |         
316 |     except HTTPException:
317 |         # Re-raise HTTP exceptions as-is (already properly formatted)
318 |         raise
319 |     except Exception as e:
320 |         # Catch-all for unexpected errors
321 |         error_msg = f"Unexpected error: {str(e)}"
322 |         logger.error(error_msg, exc_info=True)
323 |         print(f"ERROR: {error_msg}")  # Print to terminal for debugging
324 |         raise HTTPException(status_code=500, detail=f"Failed to analyze repository: {str(e)}")
325 | 
326 | 
327 | @app.post("/ask", response_model=AskResponse)
328 | async def ask_question(request: AskRequest) -> AskResponse:
329 |     """
330 |     Answer a question about the repository using AI.
331 |     
332 |     Args:
333 |         request: AskRequest containing the question
334 |         
335 |     Returns:
336 |         AskResponse with the AI-generated answer
337 |         
338 |     Raises:
339 |         HTTPException: If the question cannot be answered or no repository has been analyzed
340 |     """
341 |     global _last_onboarding_doc, _last_repo_files
342 |     
343 |     try:
344 |         logger.info(f"Processing question: {request.question[:100]}...")
345 |         
346 |         # Check if we have a stored onboarding document
347 |         if not _last_onboarding_doc:
348 |             raise HTTPException(
349 |                 status_code=400,
350 |                 detail="No repository has been analyzed yet. Please analyze a repository first using the /analyze endpoint."
351 |             )
352 |         
353 |         # Call the orchestrate agent to answer the question using stored context and raw files
354 |         result = answer_question(request.question, _last_onboarding_doc, _last_repo_files)
355 |         
356 |         logger.info("Question answered successfully")
357 |         
358 |         return AskResponse(
359 |             answer=result["answer"],
360 |             sources=result["sources"],
361 |             powered_by=result.get("powered_by"),
362 |             files_searched=result.get("files_searched"),
363 |             files_matched=result.get("files_matched")
364 |         )
365 |         
366 |     except HTTPException:
367 |         # Re-raise HTTP exceptions as-is
368 |         raise
369 |     except ValueError as e:
370 |         # Handle validation errors
371 |         logger.error(f"Invalid request: {str(e)}")
372 |         raise HTTPException(
373 |             status_code=400,
374 |             detail=f"Invalid request: {str(e)}"
375 |         )
376 |     except Exception as e:
377 |         # Catch-all for unexpected errors
378 |         logger.error(f"Error answering question: {str(e)}", exc_info=True)
379 |         raise HTTPException(
380 |             status_code=500,
381 |             detail=f"Failed to answer question: {str(e)}"
382 |         )
383 | 
384 | 
385 | if __name__ == "__main__":
386 |     """
387 |     Run the FastAPI application using Uvicorn server.
388 |     
389 |     This block only executes when the script is run directly (not imported).
390 |     Starts the server on all network interfaces (0.0.0.0) on port 8000
391 |     with auto-reload enabled for development.
392 |     """
393 |     import uvicorn
394 |     uvicorn.run(
395 |         "main:app",  # Application instance to run
396 |         host="0.0.0.0",  # Listen on all network interfaces
397 |         port=8000,  # Port to bind to
398 |         reload=True  # Auto-reload on code changes (development only)
399 |     )
400 | 
401 | # Made with Bob

</file_content>
<environment_details>
# VSCode Visible Files
backend\orchestrate_agent.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/doc_generator.py,backend/watsonx_client.py,backend/orchestrate_agent.py,backend/main.py,backend/github_client.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
### New Output
 INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [41360]
INFO:     Started server process [14596]
INFO:     Waiting for application startup.
INFO:     Application startup complete.


# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:02:55.411Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.00

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>


# Current Workspace Directory (d:/devonboard) Files
.gitignore
README.md
.bob/
backend/
backend/doc_generator.py
backend/github_client.py
backend/main.py
backend/orchestrate_agent.py
backend/pytest.ini
backend/requirements.txt
backend/test_watson.py
backend/watsonx_client.py
backend/tests/
backend/tests/__init__.py
backend/tests/README.md
backend/tests/test_doc_generator.py
backend/tests/test_github_client.py
docs/
docs/ARCHITECTURE_PLAN.md
docs/EDGE_CASES_FIXED.md
docs/FILE_STRUCTURE_CHECKLIST.md
docs/IMPLEMENTATION_PLAN.md
docs/PLANNING_SUMMARY.md
docs/QUICK_START_GUIDE.md
frontend/
frontend/.gitignore
frontend/eslint.config.js
frontend/index.html
frontend/package-lock.json
frontend/package.json
frontend/README.md
frontend/vite.config.js
frontend/public/
frontend/public/favicon.svg
frontend/public/icons.svg
frontend/src/
frontend/src/App.css
frontend/src/App.jsx
frontend/src/index.css
frontend/src/main.jsx
frontend/src/MarkdownRenderer.jsx
frontend/src/assets/
frontend/src/assets/hero.png
frontend/src/assets/react.svg
frontend/src/assets/vite.svg
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

I'll implement the complete rewrite as specified. Let me start by reading all the files together to understand the current state.

<read_file>
<args>
<file>
<path>backend/github_client.py</path>
</file>
<file>
<path>backend/doc_generator.py</path>
</file>
<file>
<path>backend/orchestrate_agent.py</path>
</file>
<file>
<path>backend/main.py</path>
</file>
</args>
</read_file>

---

**User:**

[read_file for 4 files] Result:
<files>
<file><path>backend/github_client.py</path>
<content lines="1-416">
  1 | """
  2 | GitHub API client for fetching repository contents.
  3 | Production-ready implementation with robust error handling.
  4 | """
  5 | import os
  6 | import re
  7 | import base64
  8 | import asyncio
  9 | from typing import Dict, Any, Optional
 10 | import httpx
 11 | from pathlib import Path
 12 | from dotenv import load_dotenv
 13 | import logging
 14 | 
 15 | # Load environment variables from .env file in the same directory
 16 | load_dotenv(dotenv_path=Path(__file__).parent / ".env")
 17 | 
 18 | # Initialize logger
 19 | logger = logging.getLogger(__name__)
 20 | 
 21 | # GitHub API configuration
 22 | GITHUB_API_BASE = "https://api.github.com"
 23 | GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
 24 | 
 25 | # Request timeout in seconds
 26 | REQUEST_TIMEOUT = 30.0
 27 | 
 28 | # Maximum file size to fetch (40KB for TIER 3)
 29 | MAX_FILE_SIZE = 40 * 1024
 30 | 
 31 | # Module-level cache for repository data
 32 | _repo_cache: Dict[str, Dict[str, Any]] = {}
 33 | 
 34 | # TIER 1 - Critical config files (always fetch if they exist)
 35 | TIER1_FILES = [
 36 |     "README.md",
 37 |     "README.rst",
 38 |     "package.json",
 39 |     "requirements.txt",
 40 |     "setup.py",
 41 |     "setup.cfg",
 42 |     "pom.xml",
 43 |     "build.gradle",
 44 |     "Cargo.toml",
 45 |     "go.mod",
 46 |     "docker-compose.yml",
 47 |     "Dockerfile",
 48 |     ".env.example"
 49 | ]
 50 | 
 51 | # TIER 2 - Entry points and key patterns (fetch up to 8)
 52 | TIER2_PATTERNS = {
 53 |     "entry_points": [
 54 |         "main.py", "app.py", "server.py",
 55 |         "index.js", "app.js", "server.js", "main.js",
 56 |         "index.ts", "app.ts",
 57 |         "main.go", "main.rs"
 58 |     ],
 59 |     "path_keywords": [
 60 |         "route", "router",
 61 |         "auth", "login", "middleware",
 62 |         "model", "schema", "database", "db",
 63 |         "config",
 64 |         "controller"
 65 |     ]
 66 | }
 67 | 
 68 | # TIER 3 - Additional files (up to 10)
 69 | TIER3_CONFIG = {
 70 |     "max_files": 10,
 71 |     "min_size": 1024,  # 1KB
 72 |     "max_size": 40 * 1024,  # 40KB
 73 |     "preferred_folders": ["", "src", "app", "lib"],  # root or these folders
 74 |     "exclude_patterns": ["test", "spec", "__test__", ".test.", "dist/", "build/", ".next/", "__pycache__"]
 75 | }
 76 | 
 77 | 
 78 | def parse_github_url(url: str) -> tuple[str, str]:
 79 |     """
 80 |     Parse GitHub URL to extract owner and repository name.
 81 |     
 82 |     Supports formats:
 83 |     - https://github.com/owner/repo
 84 |     - https://github.com/owner/repo.git
 85 |     - https://github.com/owner/repo/tree/main
 86 |     - github.com/owner/repo
 87 |     
 88 |     Args:
 89 |         url: GitHub repository URL
 90 |         
 91 |     Returns:
 92 |         Tuple of (owner, repo)
 93 |         
 94 |     Raises:
 95 |         ValueError: If URL format is invalid
 96 |     """
 97 |     if not url or not isinstance(url, str):
 98 |         raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
 99 |     
100 |     url = url.strip()
101 |     
102 |     if not url:
103 |         raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
104 |     
105 |     # Remove trailing slashes
106 |     url = url.rstrip("/")
107 |     
108 |     # Remove .git extension if present
109 |     if url.endswith(".git"):
110 |         url = url[:-4]
111 |     
112 |     # Remove tree/branch paths (e.g., /tree/main)
113 |     url = re.sub(r'/tree/[^/]+.*$', '', url)
114 |     
115 |     # Pattern to match GitHub URLs
116 |     # Supports: http(s)://github.com/owner/repo or github.com/owner/repo
117 |     pattern = r'(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s]+)'
118 |     
119 |     match = re.search(pattern, url, re.IGNORECASE)
120 |     
121 |     if not match:
122 |         raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
123 |     
124 |     owner = match.group(1).strip()
125 |     repo = match.group(2).strip()
126 |     
127 |     if not owner or not repo:
128 |         raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
129 |     
130 |     return owner, repo
131 | 
132 | 
133 | async def _fetch_single_file(
134 |     client: httpx.AsyncClient,
135 |     owner: str,
136 |     repo: str,
137 |     path: str,
138 |     headers: Dict[str, str],
139 |     size: int = 0,
140 |     tier: str = "TIER3"
141 | ) -> Optional[Dict[str, Any]]:
142 |     """
143 |     Fetch a single file's content from GitHub API with metadata.
144 |     
145 |     Args:
146 |         client: httpx AsyncClient instance
147 |         owner: Repository owner
148 |         repo: Repository name
149 |         path: File path
150 |         headers: Request headers
151 |         size: File size in bytes
152 |         tier: Which tier this file belongs to (TIER1, TIER2, TIER3)
153 |         
154 |     Returns:
155 |         Dictionary with path, content, size, folder, and tier, or None if fetch fails
156 |     """
157 |     content_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
158 |     
159 |     try:
160 |         content_response = await client.get(content_url, headers=headers)
161 |         
162 |         if content_response.status_code == 200:
163 |             content_data = content_response.json()
164 |             encoded_content = content_data.get("content", "")
165 |             
166 |             if encoded_content:
167 |                 try:
168 |                     # Decode base64 content
169 |                     decoded = base64.b64decode(encoded_content)
170 |                     text_content = decoded.decode("utf-8", errors="ignore")
171 |                     
172 |                     # Extract folder from path
173 |                     folder = "/".join(path.split("/")[:-1]) if "/" in path else ""
174 |                     
175 |                     logger.info(f"Fetched content for {path} ({tier})")
176 |                     return {
177 |                         "path": path,
178 |                         "content": text_content,
179 |                         "size": size,
180 |                         "folder": folder,
181 |                         "tier": tier
182 |                     }
183 |                 except Exception as e:
184 |                     logger.warning(f"Failed to decode {path}: {e}")
185 |     except Exception as e:
186 |         logger.warning(f"Failed to fetch {path}: {e}")
187 |     
188 |     return None
189 | 
190 | 
191 | async def fetch_repo_data(url: str) -> Dict[str, Any]:
192 |     """
193 |     Fetch repository data from GitHub API.
194 |     
195 |     Args:
196 |         url: GitHub repository URL
197 |         
198 |     Returns:
199 |         Dictionary containing repository data:
200 |         {
201 |             "owner": str,
202 |             "repo": str,
203 |             "description": str,
204 |             "stars": int,
205 |             "language": str,
206 |             "files": [{"path": str, "content": str}],
207 |             "file_count": int
208 |         }
209 |         
210 |     Raises:
211 |         ValueError: For invalid URL or repository not found
212 |         PermissionError: For rate limit or authentication issues
213 |         ConnectionError: For network connectivity issues
214 |     """
215 |     # Parse GitHub URL
216 |     try:
217 |         owner, repo = parse_github_url(url)
218 |     except ValueError as e:
219 |         raise ValueError(str(e))
220 |     
221 |     # Check cache first
222 |     cache_key = f"{owner}/{repo}"
223 |     if cache_key in _repo_cache:
224 |         logger.info(f"Returning cached data for {cache_key}")
225 |         return _repo_cache[cache_key]
226 |     
227 |     logger.info(f"Fetching repository data for {owner}/{repo}")
228 |     
229 |     # Set up headers
230 |     headers = {
231 |         "Accept": "application/vnd.github.v3+json",
232 |         "User-Agent": "DevOnboard-App"
233 |     }
234 |     
235 |     # Add authorization header if token exists
236 |     if GITHUB_TOKEN:
237 |         headers["Authorization"] = f"token {GITHUB_TOKEN}"
238 |         logger.info("Using GitHub token for authentication")
239 |     else:
240 |         logger.warning("No GitHub token found - rate limits will be lower")
241 |     
242 |     try:
243 |         async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
244 |             # Step 1: Get repository metadata
245 |             repo_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
246 |             
247 |             try:
248 |                 response = await client.get(repo_url, headers=headers)
249 |             except httpx.ConnectError:
250 |                 raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
251 |             except httpx.TimeoutException:
252 |                 raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
253 |             
254 |             # Handle HTTP errors
255 |             if response.status_code == 401:
256 |                 raise PermissionError("Invalid GitHub token. Check your GITHUB_TOKEN in .env")
257 |             elif response.status_code == 403:
258 |                 # Check if it's a rate limit issue
259 |                 if "rate limit" in response.text.lower():
260 |                     raise PermissionError("GitHub API rate limit exceeded. Add a GITHUB_TOKEN to .env")
261 |                 raise PermissionError("GitHub API rate limit exceeded. Add a GITHUB_TOKEN to .env")
262 |             elif response.status_code == 404:
263 |                 raise ValueError("Repository not found. Check the URL and make sure it is public")
264 |             
265 |             response.raise_for_status()
266 |             repo_data = response.json()
267 |             
268 |             # Extract repository metadata
269 |             description = repo_data.get("description", "")
270 |             stars = repo_data.get("stargazers_count", 0)
271 |             language = repo_data.get("language", "")
272 |             default_branch = repo_data.get("default_branch", "main")
273 |             
274 |             # Step 2: Get repository file tree
275 |             tree_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
276 |             
277 |             try:
278 |                 response = await client.get(tree_url, headers=headers)
279 |             except httpx.ConnectError:
280 |                 raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
281 |             except httpx.TimeoutException:
282 |                 raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
283 |             
284 |             if response.status_code == 401:
285 |                 raise PermissionError("Invalid GitHub token. Check your GITHUB_TOKEN in .env")
286 |             elif response.status_code == 403:
287 |                 raise PermissionError("GitHub API rate limit exceeded. Add a GITHUB_TOKEN to .env")
288 |             elif response.status_code == 404:
289 |                 raise ValueError("Repository not found. Check the URL and make sure it is public")
290 |             
291 |             response.raise_for_status()
292 |             tree_data = response.json()
293 |             
294 |             tree = tree_data.get("tree", [])
295 |             
296 |             if not tree:
297 |                 raise ValueError("Repository appears to be empty")
298 |             
299 |             # Step 3: Smart file selection with tiered priority
300 |             file_count = 0
301 |             tier1_files = []
302 |             tier2_candidates = []
303 |             tier3_candidates = []
304 |             
305 |             for item in tree:
306 |                 if item.get("type") != "blob":
307 |                     continue
308 |                 
309 |                 file_count += 1
310 |                 path = item.get("path", "")
311 |                 size = item.get("size", 0)
312 |                 filename = path.split("/")[-1]
313 |                 path_lower = path.lower()
314 |                 
315 |                 # TIER 1: Critical config files (always fetch)
316 |                 if filename in TIER1_FILES:
317 |                     tier1_files.append({"path": path, "size": size, "tier": "TIER1"})
318 |                     continue
319 |                 
320 |                 # TIER 2: Entry points and key patterns (up to 8)
321 |                 tier2_match = False
322 |                 
323 |                 # Check entry point files
324 |                 if filename in TIER2_PATTERNS["entry_points"]:
325 |                     tier2_match = True
326 |                 
327 |                 # Check path keywords
328 |                 if not tier2_match:
329 |                     for keyword in TIER2_PATTERNS["path_keywords"]:
330 |                         if keyword in path_lower:
331 |                             tier2_match = True
332 |                             break
333 |                 
334 |                 if tier2_match:
335 |                     tier2_candidates.append({"path": path, "size": size, "tier": "TIER2"})
336 |                     continue
337 |                 
338 |                 # TIER 3: Additional files with filters
339 |                 # Check if file should be excluded
340 |                 should_exclude = False
341 |                 for exclude_pattern in TIER3_CONFIG["exclude_patterns"]:
342 |                     if exclude_pattern in path_lower:
343 |                         should_exclude = True
344 |                         break
345 |                 
346 |                 if should_exclude:
347 |                     continue
348 |                 
349 |                 # Check size constraints
350 |                 if size < TIER3_CONFIG["min_size"] or size > TIER3_CONFIG["max_size"]:
351 |                     continue
352 |                 
353 |                 # Check if in preferred folders
354 |                 folder = path.split("/")[0] if "/" in path else ""
355 |                 if folder in TIER3_CONFIG["preferred_folders"] or folder == "":
356 |                     tier3_candidates.append({"path": path, "size": size, "tier": "TIER3"})
357 |             
358 |             # Select files: All TIER1 + up to 8 TIER2 + up to 10 TIER3
359 |             files_to_fetch = []
360 |             files_to_fetch.extend(tier1_files)
361 |             files_to_fetch.extend(tier2_candidates[:8])
362 |             files_to_fetch.extend(tier3_candidates[:TIER3_CONFIG["max_files"]])
363 |             
364 |             logger.info(f"Selected {len(tier1_files)} TIER1, {min(8, len(tier2_candidates))} TIER2, "
365 |                        f"{min(TIER3_CONFIG['max_files'], len(tier3_candidates))} TIER3 files "
366 |                        f"(out of {file_count} total files)")
367 |             
368 |             # Step 4: Fetch all selected files in parallel using asyncio.gather()
369 |             fetch_tasks = [
370 |                 _fetch_single_file(
371 |                     client, owner, repo,
372 |                     file_info["path"],
373 |                     headers,
374 |                     file_info["size"],
375 |                     file_info["tier"]
376 |                 )
377 |                 for file_info in files_to_fetch
378 |             ]
379 |             
380 |             # Execute all fetches in parallel
381 |             results = await asyncio.gather(*fetch_tasks, return_exceptions=False)
382 |             
383 |             # Filter out None results (failed fetches)
384 |             files = [result for result in results if result is not None]
385 |             
386 |             logger.info(f"Successfully fetched {len(files)} files out of {file_count} total files")
387 |             
388 |             # Prepare result
389 |             result = {
390 |                 "owner": owner,
391 |                 "repo": repo,
392 |                 "description": description,
393 |                 "stars": stars,
394 |                 "language": language,
395 |                 "files": files,
396 |                 "file_count": file_count
397 |             }
398 |             
399 |             # Cache the result
400 |             _repo_cache[cache_key] = result
401 |             
402 |             return result
403 |             
404 |     except httpx.ConnectError:
405 |         raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
406 |     except httpx.TimeoutException:
407 |         raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
408 |     except (ValueError, PermissionError, ConnectionError):
409 |         # Re-raise these as-is
410 |         raise
411 |     except Exception as e:
412 |         logger.error(f"Unexpected error: {e}", exc_info=True)
413 |         raise ConnectionError(f"Failed to fetch repository data: {str(e)}")
414 | 
415 | 
416 | # Made with Bob
</content>
</file>
<file><path>backend/doc_generator.py</path>
<content lines="1-950">
  1 | """
  2 | Documentation generator for creating onboarding documents from repository data.
  3 | Enhanced version with deeper analysis and structured sections.
  4 | """
  5 | import os
  6 | import re
  7 | from typing import Dict, Any, List, Optional, Tuple
  8 | import logging
  9 | import json
 10 | import watsonx_client
 11 | 
 12 | # Initialize logger for tracking documentation generation process
 13 | logger = logging.getLogger(__name__)
 14 | 
 15 | # Maximum path length to prevent filesystem issues and path traversal attacks
 16 | MAX_PATH_LENGTH = 4096
 17 | 
 18 | 
 19 | def normalize_path(path: str) -> str:
 20 |     """
 21 |     Normalize file path to use forward slashes and handle edge cases.
 22 |     
 23 |     Args:
 24 |         path: File path to normalize
 25 |         
 26 |     Returns:
 27 |         Normalized path with forward slashes
 28 |     """
 29 |     if not path:
 30 |         return ""
 31 |     
 32 |     normalized = path.replace("\\", "/")
 33 |     normalized = re.sub(r'/+', '/', normalized)
 34 |     
 35 |     if len(normalized) > MAX_PATH_LENGTH:
 36 |         logger.warning(f"Path exceeds maximum length: {normalized[:100]}...")
 37 |         normalized = normalized[:MAX_PATH_LENGTH]
 38 |     
 39 |     return normalized
 40 | 
 41 | 
 42 | def safe_get_content(file_dict: Dict[str, Any]) -> Optional[str]:
 43 |     """
 44 |     Safely extract content from file dictionary with validation.
 45 |     
 46 |     Args:
 47 |         file_dict: File dictionary that may contain content
 48 |         
 49 |     Returns:
 50 |         File content as string or None if invalid
 51 |     """
 52 |     if not file_dict or not isinstance(file_dict, dict):
 53 |         return None
 54 |     
 55 |     content = file_dict.get("content")
 56 |     
 57 |     if content is None or content == "":
 58 |         return None
 59 |     
 60 |     if not isinstance(content, str):
 61 |         try:
 62 |             content = str(content)
 63 |         except Exception as e:
 64 |             logger.warning(f"Failed to convert content to string: {e}")
 65 |             return None
 66 |     
 67 |     if '\x00' in content:
 68 |         logger.warning("Binary content detected, skipping")
 69 |         return None
 70 |     
 71 |     return content
 72 | 
 73 | 
 74 | def detect_language_and_framework(files: List[Dict[str, Any]]) -> Tuple[str, str]:
 75 |     """
 76 |     Detect primary programming language and framework from files.
 77 |     
 78 |     Args:
 79 |         files: List of file dictionaries
 80 |         
 81 |     Returns:
 82 |         Tuple of (language, framework)
 83 |     """
 84 |     language = "Unknown"
 85 |     framework = "Unknown"
 86 |     
 87 |     # Count file extensions
 88 |     extensions = {}
 89 |     for f in files:
 90 |         if not f or not isinstance(f, dict):
 91 |             continue
 92 |         path = normalize_path(f.get("path", ""))
 93 |         if "." in path:
 94 |             ext = path.split(".")[-1].lower()
 95 |             extensions[ext] = extensions.get(ext, 0) + 1
 96 |     
 97 |     # Determine primary language
 98 |     if extensions.get("py", 0) > 0:
 99 |         language = "Python"
100 |     elif extensions.get("js", 0) > 0 or extensions.get("ts", 0) > 0:
101 |         language = "JavaScript/TypeScript"
102 |     elif extensions.get("java", 0) > 0:
103 |         language = "Java"
104 |     elif extensions.get("go", 0) > 0:
105 |         language = "Go"
106 |     elif extensions.get("rs", 0) > 0:
107 |         language = "Rust"
108 |     
109 |     # Detect framework from package files
110 |     for f in files:
111 |         if not f or not isinstance(f, dict):
112 |             continue
113 |         path = normalize_path(f.get("path", ""))
114 |         content = safe_get_content(f)
115 |         
116 |         if path == "package.json" and content:
117 |             try:
118 |                 data = json.loads(content)
119 |                 deps = data.get("dependencies", {})
120 |                 if "express" in deps:
121 |                     framework = "Express.js"
122 |                 elif "next" in deps:
123 |                     framework = "Next.js"
124 |                 elif "react" in deps:
125 |                     framework = "React"
126 |                 elif "vue" in deps:
127 |                     framework = "Vue.js"
128 |                 elif "angular" in deps or "@angular/core" in deps:
129 |                     framework = "Angular"
130 |             except:
131 |                 pass
132 |         
133 |         elif path == "requirements.txt" and content:
134 |             if "fastapi" in content.lower():
135 |                 framework = "FastAPI"
136 |             elif "django" in content.lower():
137 |                 framework = "Django"
138 |             elif "flask" in content.lower():
139 |                 framework = "Flask"
140 |         
141 |         elif path == "go.mod" and content:
142 |             if "gin-gonic/gin" in content:
143 |                 framework = "Gin"
144 |             elif "gorilla/mux" in content:
145 |                 framework = "Gorilla Mux"
146 |         
147 |         elif path == "Cargo.toml" and content:
148 |             if "actix-web" in content:
149 |                 framework = "Actix Web"
150 |             elif "rocket" in content:
151 |                 framework = "Rocket"
152 |     
153 |     return language, framework
154 | 
155 | 
156 | def extract_project_overview(files: List[Dict[str, Any]]) -> Dict[str, Any]:
157 |     """
158 |     Extract comprehensive project overview.
159 |     
160 |     Returns dict with: description, language, framework, dependencies, project_type
161 |     """
162 |     overview = {
163 |         "description": "",
164 |         "language": "Unknown",
165 |         "framework": "Unknown",
166 |         "dependencies": [],
167 |         "project_type": "Other"
168 |     }
169 |     
170 |     # Detect language and framework
171 |     overview["language"], overview["framework"] = detect_language_and_framework(files)
172 |     
173 |     # Extract README description
174 |     for f in files:
175 |         if not f or not isinstance(f, dict):
176 |             continue
177 |         path = normalize_path(f.get("path", ""))
178 |         if path.lower() in ["readme.md", "readme.rst", "readme.txt", "readme"]:
179 |             content = safe_get_content(f)
180 |             if content:
181 |                 lines = content.split("\n")
182 |                 desc_lines = []
183 |                 for line in lines:
184 |                     line = line.strip()
185 |                     if line and not line.startswith("#") and not line.startswith("!"):
186 |                         desc_lines.append(line)
187 |                         if len(" ".join(desc_lines)) > 300:
188 |                             break
189 |                 overview["description"] = " ".join(desc_lines[:3])
190 |             break
191 |     
192 |     # Extract dependencies
193 |     for f in files:
194 |         if not f or not isinstance(f, dict):
195 |             continue
196 |         path = normalize_path(f.get("path", ""))
197 |         content = safe_get_content(f)
198 |         
199 |         if path == "package.json" and content:
200 |             try:
201 |                 data = json.loads(content)
202 |                 deps = data.get("dependencies", {})
203 |                 overview["dependencies"] = list(deps.keys())[:10]
204 |             except:
205 |                 pass
206 |         
207 |         elif path == "requirements.txt" and content:
208 |             lines = content.split("\n")[:10]
209 |             deps = []
210 |             for line in lines:
211 |                 line = line.strip()
212 |                 if line and not line.startswith("#"):
213 |                     pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
214 |                     if pkg:
215 |                         deps.append(pkg)
216 |             overview["dependencies"] = deps
217 |     
218 |     # Determine project type
219 |     has_api = any("api" in f.get("path", "").lower() or "route" in f.get("path", "").lower() 
220 |                   for f in files if f and isinstance(f, dict))
221 |     has_frontend = any(f.get("path", "").lower().endswith((".jsx", ".tsx", ".vue")) 
222 |                        for f in files if f and isinstance(f, dict))
223 |     has_cli = any("cli" in f.get("path", "").lower() or "command" in f.get("path", "").lower()
224 |                   for f in files if f and isinstance(f, dict))
225 |     
226 |     if has_api and has_frontend:
227 |         overview["project_type"] = "Full-stack"
228 |     elif has_api:
229 |         overview["project_type"] = "API"
230 |     elif has_frontend:
231 |         overview["project_type"] = "Frontend"
232 |     elif has_cli:
233 |         overview["project_type"] = "CLI"
234 |     elif any(path in ["setup.py", "pyproject.toml", "package.json"] 
235 |              for f in files if f and isinstance(f, dict) 
236 |              for path in [normalize_path(f.get("path", ""))]):
237 |         overview["project_type"] = "Library"
238 |     
239 |     return overview
240 | 
241 | 
242 | def analyze_architecture(files: List[Dict[str, Any]]) -> Dict[str, Any]:
243 |     """
244 |     Analyze architecture: folder structure, entry point, database, external services.
245 |     """
246 |     architecture = {
247 |         "folders": {},
248 |         "entry_point": None,
249 |         "database":  None,
250 |         "external_services": []
251 |     }
252 |     
253 |     # Analyze folder structure
254 |     folders = {}
255 |     for f in files:
256 |         if not f or not isinstance(f, dict):
257 |             continue
258 |         path = normalize_path(f.get("path", ""))
259 |         if "/" in path:
260 |             folder = path.split("/")[0]
261 |             if folder not in folders:
262 |                 folders[folder] = []
263 |             folders[folder].append(path)
264 |     
265 |     # Categorize folders
266 |     folder_descriptions = {
267 |         "src": "Source code directory",
268 |         "app": "Application logic",
269 |         "backend": "Server-side code",
270 |         "frontend": "Client-side code",
271 |         "api": "API endpoints",
272 |         "components": "UI components",
273 |         "utils": "Utility functions",
274 |         "lib": "Shared libraries",
275 |         "config": "Configuration files",
276 |         "tests": "Test files",
277 |         "docs": "Documentation",
278 |         "public": "Static assets",
279 |         "static": "Static files",
280 |         "assets": "Media files",
281 |         "models": "Data models",
282 |         "routes": "Routing logic",
283 |         "controllers": "Business logic",
284 |         "services": "Service layer",
285 |         "middleware": "Middleware functions"
286 |     }
287 |     
288 |     for folder, file_list in folders.items():
289 |         description = folder_descriptions.get(folder, f"Contains {len(file_list)} files")
290 |         architecture["folders"][folder] = description
291 |     
292 |     # Find entry point
293 |     entry_points = ["main.py", "app.py", "server.py", "index.js", "app.js", "server.js", "main.js", "index.ts", "app.ts"]
294 |     for f in files:
295 |         if not f or not isinstance(f, dict):
296 |             continue
297 |         path = normalize_path(f.get("path", ""))
298 |         filename = path.split("/")[-1]
299 |         if filename in entry_points:
300 |             architecture["entry_point"] = path
301 |             break
302 |     
303 |     # Detect database
304 |     db_indicators = ["sqlite", "postgres", "mysql", "mongodb", "redis", "prisma", "sequelize", "mongoose", "sqlalchemy"]
305 |     for f in files:
306 |         content = safe_get_content(f)
307 |         if content:
308 |             content_lower = content.lower()
309 |             for db in db_indicators:
310 |                 if db in content_lower:
311 |                     architecture["database"] = db.title()
312 |                     break
313 |             if architecture["database"]:
314 |                 break
315 |     
316 |     # Detect external services
317 |     service_indicators = ["aws", "stripe", "twilio", "sendgrid", "firebase", "auth0", "oauth", "jwt"]
318 |     for f in files:
319 |         content = safe_get_content(f)
320 |         if content:
321 |             content_lower = content.lower()
322 |             for service in service_indicators:
323 |                 if service in content_lower and service not in architecture["external_services"]:
324 |                     architecture["external_services"].append(service.upper())
325 |     
326 |     return architecture
327 | 
328 | 
329 | def find_key_files_map(files: List[Dict[str, Any]]) -> List[Dict[str, str]]:
330 |     """
331 |     Create a map of TIER 1 and TIER 2 files with descriptions.
332 |     """
333 |     key_files = []
334 |     
335 |     for f in files:
336 |         if not f or not isinstance(f, dict):
337 |             continue
338 |         
339 |         tier = f.get("tier", "")
340 |         if tier not in ["TIER1", "TIER2"]:
341 |             continue
342 |         
343 |         path = normalize_path(f.get("path", ""))
344 |         filename = path.split("/")[-1]
345 |         
346 |         # Generate description based on file type
347 |         description = ""
348 |         if filename == "README.md":
349 |             description = "Project documentation and setup instructions"
350 |         elif filename == "package.json":
351 |             description = "Node.js dependencies and scripts configuration"
352 |         elif filename == "requirements.txt":
353 |             description = "Python dependencies specification"
354 |         elif filename in ["main.py", "app.py", "server.py"]:
355 |             description = "Main application entry point"
356 |         elif filename in ["index.js", "app.js", "server.js", "main.js"]:
357 |             description = "JavaScript application entry point"
358 |         elif "route" in path.lower():
359 |             description = "API routing and endpoint definitions"
360 |         elif "auth" in path.lower():
361 |             description = "Authentication and authorization logic"
362 |         elif "model" in path.lower():
363 |             description = "Data models and database schemas"
364 |         elif "config" in path.lower():
365 |             description = "Application configuration settings"
366 |         elif "controller" in path.lower():
367 |             description = "Business logic and request handlers"
368 |         else:
369 |             description = f"Important {tier.lower()} file for the project"
370 |         
371 |         key_files.append({
372 |             "path": path,
373 |             "description": description,
374 |             "tier": tier
375 |         })
376 |     
377 |     return key_files
378 | 
379 | 
380 | def analyze_authentication(files: List[Dict[str, Any]]) -> Dict[str, Any]:
381 |     """
382 |     Analyze authentication and security implementation.
383 |     """
384 |     auth_info = {
385 |         "has_auth": False,
386 |         "auth_methods": [],
387 |         "auth_files": []
388 |     }
389 |     
390 |     auth_keywords = ["jwt", "oauth", "passport", "bcrypt", "session", "cookie", "token", "auth", "login", "middleware"]
391 |     
392 |     for f in files:
393 |         content = safe_get_content(f)
394 |         path = normalize_path(f.get("path", ""))
395 |         
396 |         if content:
397 |             content_lower = content.lower()
398 |             path_lower = path.lower()
399 |             
400 |             # Check for auth keywords in content or path
401 |             found_auth = False
402 |             for keyword in auth_keywords:
403 |                 if keyword in content_lower or keyword in path_lower:
404 |                     found_auth = True
405 |                     if keyword not in auth_info["auth_methods"]:
406 |                         auth_info["auth_methods"].append(keyword.upper())
407 |             
408 |             if found_auth:
409 |                 auth_info["has_auth"] = True
410 |                 auth_info["auth_files"].append(path)
411 |     
412 |     return auth_info
413 | 
414 | 
415 | def find_api_endpoints(files: List[Dict[str, Any]]) -> List[Dict[str, str]]:
416 |     """
417 |     Find API endpoints from route definitions.
418 |     """
419 |     endpoints = []
420 |     
421 |     # Patterns for different frameworks
422 |     patterns = {
423 |         "express": [
424 |             r"app\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
425 |             r"router\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"
426 |         ],
427 |         "fastapi": [
428 |             r"@app\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
429 |             r"@router\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"
430 |         ],
431 |         "flask": [
432 |             r"@app\.route\s*\(\s*['\"]([^'\"]+)['\"].*methods\s*=\s*\[['\"]([^'\"]+)['\"]",
433 |             r"@app\.route\s*\(\s*['\"]([^'\"]+)['\"]"
434 |         ],
435 |         "django": [
436 |             r"path\s*\(\s*['\"]([^'\"]+)['\"]"
437 |         ]
438 |     }
439 |     
440 |     for f in files:
441 |         content = safe_get_content(f)
442 |         if not content:
443 |             continue
444 |         
445 |         path = normalize_path(f.get("path", ""))
446 |         
447 |         # Try all patterns
448 |         for framework, pattern_list in patterns.items():
449 |             for pattern in pattern_list:
450 |                 matches = re.findall(pattern, content, re.IGNORECASE)
451 |                 for match in matches:
452 |                     if isinstance(match, tuple):
453 |                         if len(match) == 2:
454 |                             method, endpoint = match
455 |                             endpoints.append({"method": method.upper(), "path": endpoint, "file": path})
456 |                         else:
457 |                             endpoint = match[0] if match else ""
458 |                             endpoints.append({"method": "GET", "path": endpoint, "file": path})
459 |                     else:
460 |                         endpoints.append({"method": "GET", "path": match, "file": path})
461 |     
462 |     # Remove duplicates and limit to 15
463 |     seen = set()
464 |     unique_endpoints = []
465 |     for ep in endpoints:
466 |         key = f"{ep['method']} {ep['path']}"
467 |         if key not in seen:
468 |             seen.add(key)
469 |             unique_endpoints.append(ep)
470 |             if len(unique_endpoints) >= 15:
471 |                 break
472 |     
473 |     return unique_endpoints
474 | 
475 | 
476 | def find_data_models(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
477 |     """
478 |     Find data models and schemas.
479 |     """
480 |     models = []
481 |     
482 |     # Patterns for different ORMs/frameworks
483 |     model_patterns = {
484 |         "mongoose": r"const\s+(\w+)\s*=\s*mongoose\.model",
485 |         "sequelize": r"const\s+(\w+)\s*=\s*sequelize\.define",
486 |         "sqlalchemy": r"class\s+(\w+)\s*\([^)]*Model[^)]*\)",
487 |         "django": r"class\s+(\w+)\s*\([^)]*models\.Model[^)]*\)",
488 |         "prisma": r"model\s+(\w+)\s*{",
489 |         "typeorm": r"@Entity\s*\(\s*['\"]?(\w+)['\"]?\s*\)",
490 |         "pydantic": r"class\s+(\w+)\s*\([^)]*BaseModel[^)]*\)"
491 |     }
492 |     
493 |     for f in files:
494 |         content = safe_get_content(f)
495 |         if not content:
496 |             continue
497 |         
498 |         path = normalize_path(f.get("path", ""))
499 |         
500 |         for orm, pattern in model_patterns.items():
501 |             matches = re.findall(pattern, content, re.IGNORECASE)
502 |             for match in matches:
503 |                 model_name = match if isinstance(match, str) else match[0]
504 |                 
505 |                 # Extract fields (simplified)
506 |                 fields = []
507 |                 if orm == "prisma":
508 |                     field_pattern = r"(\w+)\s+(\w+)"
509 |                     field_matches = re.findall(field_pattern, content)
510 |                     fields = [f"{name}: {type_}" for name, type_ in field_matches[:5]]
511 |                 
512 |                 models.append({
513 |                     "name": model_name,
514 |                     "orm": orm,
515 |                     "file": path,
516 |                     "fields": fields
517 |                 })
518 |     
519 |     return models
520 | 
521 | 
522 | def generate_feature_guide_by_stack(language: str, framework: str, folders: Dict[str, str]) -> str:
523 |     """
524 |     Generate framework-specific feature addition guide.
525 |     """
526 |     guide = []
527 |     
528 |     if framework in ["Express.js", "Node.js"]:
529 |         guide.extend([
530 |             "#### For Express.js Features:\n\n",
531 |             "1. **Plan the Feature**\n",
532 |             "   - Define API endpoints needed\n",
533 |             "   - Identify data models required\n",
534 |             "   - Plan middleware integration\n\n",
535 |             
536 |             "2. **Create/Update Models**\n",
537 |             f"   - Add models in `{'models/' if 'models' in folders else 'src/models/'}`\n",
538 |             "   - Define Mongoose schemas or Sequelize models\n",
539 |             "   - Add validation rules\n\n",
540 |             
541 |             "3. **Add Routes**\n",
542 |             f"   - Create route files in `{'routes/' if 'routes' in folders else 'src/routes/'}`\n",
543 |             "   - Define GET, POST, PUT, DELETE endpoints\n",
544 |             "   - Add route validation middleware\n\n",
545 |             
546 |             "4. **Implement Controllers**\n",
547 |             f"   - Add business logic in `{'controllers/' if 'controllers' in folders else 'src/controllers/'}`\n",
548 |             "   - Handle request/response logic\n",
549 |             "   - Add error handling\n\n",
550 |             
551 |             "5. **Test and Document**\n",
552 |             "   - Write unit tests for controllers\n",
553 |             "   - Test API endpoints with Postman/curl\n",
554 |             "   - Update API documentation\n\n"
555 |         ])
556 |     
557 |     elif framework in ["FastAPI", "Flask", "Django"]:
558 |         guide.extend([
559 |             f"#### For {framework} Features:\n\n",
560 |             "1. **Define Models**\n",
561 |             f"   - Add models in `{'models/' if 'models' in folders else 'app/models/'}`\n",
562 |             "   - Define Pydantic models (FastAPI) or SQLAlchemy models\n",
563 |             "   - Add field validation\n\n",
564 |             
565 |             "2. **Create Endpoints**\n",
566 |             f"   - Add routes in `{'routes/' if 'routes' in folders else 'app/routes/'}`\n",
567 |             "   - Use decorators (@app.get, @app.post, etc.)\n",
568 |             "   - Add request/response models\n\n",
569 |             
570 |             "3. **Business Logic**\n",
571 |             f"   - Implement services in `{'services/' if 'services' in folders else 'app/services/'}`\n",
572 |             "   - Add database operations\n",
573 |             "   - Handle business rules\n\n",
574 |             
575 |             "4. **Testing**\n",
576 |             "   - Write pytest tests\n",
577 |             "   - Test endpoints with TestClient\n",
578 |             "   - Add integration tests\n\n"
579 |         ])
580 |     
581 |     elif framework in ["React", "Next.js", "Vue.js"]:
582 |         guide.extend([
583 |             f"#### For {framework} Features:\n\n",
584 |             "1. **Plan Components**\n",
585 |             "   - Design component hierarchy\n",
586 |             "   - Plan state management\n",
587 |             "   - Define prop interfaces\n\n",
588 |             
589 |             "2. **Create Components**\n",
590 |             f"   - Add components in `{'components/' if 'components' in folders else 'src/components/'}`\n",
591 |             "   - Implement reusable UI elements\n",
592 |             "   - Add TypeScript interfaces\n\n",
593 |             
594 |             "3. **Add Pages/Routes**\n",
595 |             f"   - Create pages in `{'pages/' if 'pages' in folders else 'src/pages/'}`\n",
596 |             "   - Update routing configuration\n",
597 |             "   - Add navigation links\n\n",
598 |             
599 |             "4. **State Management**\n",
600 |             "   - Add hooks or store logic\n",
601 |             "   - Integrate with API endpoints\n",
602 |             "   - Handle loading states\n\n"
603 |         ])
604 |     
605 |     else:
606 |         guide.extend([
607 |             "#### General Development Process:\n\n",
608 |             "1. **Understand Requirements**\n",
609 |             "   - Review feature specifications\n",
610 |             "   - Identify affected components\n\n",
611 |             
612 |             "2. **Implement Core Logic**\n",
613 |             "   - Follow existing code patterns\n",
614 |             "   - Add appropriate tests\n\n",
615 |             
616 |             "3. **Integration**\n",
617 |             "   - Update configuration if needed\n",
618 |             "   - Test with existing features\n\n"
619 |         ])
620 |     
621 |     return "".join(guide)
622 | 
623 | 
624 | def extract_getting_started(files: List[Dict[str, Any]]) -> Dict[str, Any]:
625 |     """
626 |     Extract getting started information from README and package files.
627 |     """
628 |     getting_started = {
629 |         "install_command": None,
630 |         "run_command": None,
631 |         "env_vars": []
632 |     }
633 |     
634 |     # Check README for commands
635 |     for f in files:
636 |         if not f or not isinstance(f, dict):
637 |             continue
638 |         path = normalize_path(f.get("path", ""))
639 |         if path.lower() in ["readme.md", "readme.rst"]:
640 |             content = safe_get_content(f)
641 |             if content:
642 |                 # Look for install commands
643 |                 install_patterns = [
644 |                     r"npm install",
645 |                     r"pip install -r requirements\.txt",
646 |                     r"yarn install",
647 |                     r"go mod download",
648 |                     r"cargo build"
649 |                 ]
650 |                 
651 |                 for pattern in install_patterns:
652 |                     match = re.search(pattern, content, re.IGNORECASE)
653 |                     if match:
654 |                         getting_started["install_command"] = match.group()
655 |                         break
656 |                 
657 |                 # Look for run commands
658 |                 run_patterns = [
659 |                     r"npm (start|run dev)",
660 |                     r"python (main\.py|app\.py)",
661 |                     r"yarn (start|dev)",
662 |                     r"go run",
663 |                     r"cargo run"
664 |                 ]
665 |                 
666 |                 for pattern in run_patterns:
667 |                     match = re.search(pattern, content, re.IGNORECASE)
668 |                     if match:
669 |                         getting_started["run_command"] = match.group()
670 |                         break
671 |     
672 |     # Check package.json for scripts
673 |     for f in files:
674 |         if not f or not isinstance(f, dict):
675 |             continue
676 |         path = normalize_path(f.get("path", ""))
677 |         if path == "package.json":
678 |             content = safe_get_content(f)
679 |             if content:
680 |                 try:
681 |                     data = json.loads(content)
682 |                     scripts = data.get("scripts", {})
683 |                     if "start" in scripts:
684 |                         getting_started["run_command"] = "npm start"
685 |                     elif "dev" in scripts:
686 |                         getting_started["run_command"] = "npm run dev"
687 |                 except:
688 |                     pass
689 |     
690 |     # Check .env.example for environment variables
691 |     for f in files:
692 |         if not f or not isinstance(f, dict):
693 |             continue
694 |         path = normalize_path(f.get("path", ""))
695 |         if path == ".env.example":
696 |             content = safe_get_content(f)
697 |             if content:
698 |                 lines = content.split("\n")
699 |                 for line in lines:
700 |                     line = line.strip()
701 |                     if line and not line.startswith("#") and "=" in line:
702 |                         var_name = line.split("=")[0].strip()
703 |                         getting_started["env_vars"].append(var_name)
704 |     
705 |     return getting_started
706 | 
707 | 
708 | def get_ai_insights(raw_doc: str, metadata: dict) -> str:
709 |     if not watsonx_client.is_configured():
710 |         return ""
711 | 
712 |     prompt = f"""You are a senior software architect reviewing
713 | a code repository. Be concise and specific.
714 | 
715 | Repository details:
716 | - Language: {metadata.get('language', 'Unknown')}
717 | - Framework: {metadata.get('framework', 'Unknown')}
718 | - Has Authentication: {metadata.get('has_auth', False)}
719 | - Has Database: {metadata.get('has_database', False)}
720 | - API Endpoints found: {metadata.get('endpoint_count', 0)}
721 | - Total files analyzed: {metadata.get('total_files_analyzed', 0)}
722 | 
723 | Documentation excerpt:
724 | {raw_doc[:2500]}
725 | 
726 | Provide exactly these four things:
727 | 1. Architecture pattern (1 sentence): MVC / microservices /
728 |    monolith / JAMstack / other
729 | 2. Top 3 files a new developer must read first and why
730 | 3. One potential risk or gotcha in this codebase
731 | 4. Complexity rating: Simple / Medium / Complex with one reason
732 | 
733 | Keep total response under 300 words."""
734 | 
735 |     cache_key = (f"insights_"
736 |                  f"{metadata.get('owner', 'x')}_"
737 |                  f"{metadata.get('repo', 'x')}")
738 |     try:
739 |         return watsonx_client.generate_text(
740 |             prompt=prompt,
741 |             cache_key=cache_key,
742 |             max_tokens=400
743 |         )
744 |     except Exception as e:
745 |         print(f"[insights] watsonx failed: {e}")
746 |         return ""
747 | 
748 | 
749 | def generate_onboarding_doc(repo_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
750 |     """
751 |     Generate a comprehensive onboarding document with structured metadata.
752 |     
753 |     Args:
754 |         repo_data: Repository data from fetch_repo_data()
755 |         
756 |     Returns:
757 |         Tuple of (markdown_document, metadata_dict)
758 |     """
759 |     if not repo_data or not isinstance(repo_data, dict):
760 |         raise ValueError("Invalid repository data: must be a dictionary")
761 |     
762 |     files = repo_data.get("files", [])
763 |     if not files:
764 |         raise ValueError("No files found in repository data")
765 |     
766 |     logger.info(f"Generating enhanced onboarding document for {len(files)} files")
767 |     
768 |     # Extract all analysis data
769 |     overview = extract_project_overview(files)
770 |     architecture = analyze_architecture(files)
771 |     key_files = find_key_files_map(files)
772 |     auth_info = analyze_authentication(files)
773 |     endpoints = find_api_endpoints(files)
774 |     models = find_data_models(files)
775 |     getting_started = extract_getting_started(files)
776 |     
777 |     # Build metadata
778 |     metadata = {
779 |         "language": overview["language"],
780 |         "framework": overview["framework"],
781 |         "project_type": overview["project_type"],
782 |         "has_auth": auth_info["has_auth"],
783 |         "has_database": architecture["database"] is not None,
784 |         "endpoint_count": len(endpoints),
785 |         "model_count": len(models),
786 |         "tier1_files": [f["path"] for f in key_files if f.get("tier") == "TIER1"],
787 |         "tier2_files": [f["path"] for f in key_files if f.get("tier") == "TIER2"],
788 |         "total_files_analyzed": len(files)
789 |     }
790 |     
791 |     # Build markdown document
792 |     doc_parts = []
793 |     
794 |     # Header
795 |     doc_parts.extend([
796 |         f"# {repo_data.get('repo', 'Repository')} - Developer Onboarding Guide\n\n",
797 |         "*Comprehensive auto-generated documentation for faster onboarding*\n\n",
798 |         "---\n\n"
799 |     ])
800 |     
801 |     # 1. PROJECT OVERVIEW
802 |     doc_parts.extend([
803 |         "## 📋 PROJECT OVERVIEW\n\n",
804 |         f"**What this project does:** {overview['description'] or 'No description available from README'}\n\n",
805 |         f"**Primary Language:** {overview['language']}\n\n",
806 |         f"**Framework:** {overview['framework']}\n\n",
807 |         f"**Project Type:** {overview['project_type']}\n\n"
808 |     ])
809 |     
810 |     if overview["dependencies"]:
811 |         doc_parts.append(f"**Key Dependencies:** {', '.join(overview['dependencies'][:8])}\n\n")
812 |     
813 |     doc_parts.append("---\n\n")
814 |     
815 |     # 2. ARCHITECTURE SUMMARY
816 |     doc_parts.extend([
817 |         "## 🏗️ ARCHITECTURE SUMMARY\n\n",
818 |         "### Folder Structure\n"
819 |     ])
820 |     
821 |     for folder, description in architecture["folders"].items():
822 |         doc_parts.append(f"- **`{folder}/`** - {description}\n")
823 |     
824 |     doc_parts.append("\n")
825 |     
826 |     if architecture["entry_point"]:
827 |         doc_parts.append(f"**Application Entry Point:** `{architecture['entry_point']}`\n\n")
828 |     
829 |     if architecture["database"]:
830 |         doc_parts.append(f"**Database:** {architecture['database']}\n\n")
831 |     
832 |     if architecture["external_services"]:
833 |         doc_parts.append(f"**External Services:** {', '.join(architecture['external_services'])}\n\n")
834 |     
835 |     doc_parts.append("---\n\n")
836 |     
837 |     # 3. KEY FILES MAP
838 |     doc_parts.extend([
839 |         "## 🗂️ KEY FILES MAP\n\n",
840 |         "*Essential files every developer should understand*\n\n"
841 |     ])
842 |     
843 |     for i, file_info in enumerate(key_files, 1):
844 |         tier_emoji = "🔥" if file_info["tier"] == "TIER1" else "⚡"
845 |         doc_parts.append(f"{i}. {tier_emoji} **`{file_info['path']}`**\n")
846 |         doc_parts.append(f"   {file_info['description']}\n\n")
847 |     
848 |     doc_parts.append("---\n\n")
849 |     
850 |     # 4. AUTHENTICATION & SECURITY
851 |     doc_parts.extend([
852 |         "## 🔐 AUTHENTICATION & SECURITY\n\n"
853 |     ])
854 |     
855 |     if auth_info["has_auth"]:
856 |         doc_parts.append(f"**Authentication Methods:** {', '.join(auth_info['auth_methods'])}\n\n")
857 |         doc_parts.append("**Auth-related Files:**\n")
858 |         for auth_file in auth_info["auth_files"][:5]:
859 |             doc_parts.append(f"- `{auth_file}`\n")
860 |         doc_parts.append("\n")
861 |     else:
862 |         doc_parts.append("No authentication detected in analyzed files.\n\n")
863 |     
864 |     doc_parts.append("---\n\n")
865 |     
866 |     # 5. API ENDPOINTS
867 |     doc_parts.extend([
868 |         "## 🌐 API ENDPOINTS\n\n"
869 |     ])
870 |     
871 |     if endpoints:
872 |         doc_parts.append("| Method | Endpoint | File |\n")
873 |         doc_parts.append("|--------|----------|------|\n")
874 |         for ep in endpoints:
875 |             doc_parts.append(f"| {ep['method']} | `{ep['path']}` | `{ep['file']}` |\n")
876 |         doc_parts.append("\n")
877 |     else:
878 |         doc_parts.append("No API endpoints detected in analyzed files.\n\n")
879 |     
880 |     doc_parts.append("---\n\n")
881 |     
882 |     # 6. DATA MODELS
883 |     doc_parts.extend([
884 |         "## 📊 DATA MODELS\n\n"
885 |     ])
886 |     
887 |     if models:
888 |         for model in models:
889 |             doc_parts.append(f"### {model['name']} ({model['orm'].title()})\n")
890 |             doc_parts.append(f"*File: `{model['file']}`*\n\n")
891 |             if model['fields']:
892 |                 doc_parts.append("**Fields:**\n")
893 |                 for field in model['fields']:
894 |                     doc_parts.append(f"- {field}\n")
895 |                 doc_parts.append("\n")
896 |     else:
897 |         doc_parts.append("No data models detected in analyzed files.\n\n")
898 |     
899 |     doc_parts.append("---\n\n")
900 |     
901 |     # 7. HOW TO ADD A NEW FEATURE
902 |     doc_parts.extend([
903 |         "## 🚀 HOW TO ADD A NEW FEATURE\n\n",
904 |         generate_feature_guide_by_stack(overview["language"], overview["framework"], architecture["folders"])
905 |     ])
906 |     
907 |     doc_parts.append("---\n\n")
908 |     
909 |     # 8. GETTING STARTED
910 |     doc_parts.extend([
911 |         "## 🎯 GETTING STARTED\n\n"
912 |     ])
913 |     
914 |     if getting_started["install_command"]:
915 |         doc_parts.append(f"**Install Dependencies:**\n```bash\n{getting_started['install_command']}\n```\n\n")
916 |     
917 |     if getting_started["run_command"]:
918 |         doc_parts.append(f"**Run the Application:**\n```bash\n{getting_started['run_command']}\n```\n\n")
919 |     
920 |     if getting_started["env_vars"]:
921 |         doc_parts.append("**Environment Variables:**\n")
922 |         for var in getting_started["env_vars"]:
923 |             doc_parts.append(f"- `{var}`\n")
924 |         doc_parts.append("\n")
925 |     
926 |     doc_parts.extend([
927 |         "### Next Steps\n",
928 |         "1. Read through the key files listed above\n",
929 |         "2. Set up your development environment\n",
930 |         "3. Review the architecture and folder structure\n",
931 |         "4. Start with small changes to familiarize yourself\n",
932 |         "5. Follow the feature addition guide for new development\n\n",
933 |         "*Happy coding! 🎉*\n"
934 |     ])
935 |     
936 |     full_doc = "".join(doc_parts)
937 |     
938 |     # Add AI insights section
939 |     ai_insights = get_ai_insights(full_doc, metadata)
940 |     if ai_insights:
941 |         full_doc += (
942 |             f"\n\n## 🤖 AI Insights"
943 |             f" (Powered by IBM watsonx.ai)\n\n{ai_insights}"
944 |         )
945 |     
946 |     logger.info("Enhanced onboarding document generated successfully")
947 |     
948 |     return full_doc, metadata
949 | 
950 | # Made with Bob
</content>
</file>
<file><path>backend/orchestrate_agent.py</path>
<content lines="1-184">
  1 | import re
  2 | import watsonx_client
  3 | 
  4 | 
  5 | def extract_keywords(question: str) -> list:
  6 |     """
  7 |     Extract meaningful keywords from question by removing stop words
  8 |     and adding code-related expansions.
  9 |     """
 10 |     # Remove common stop words
 11 |     stop_words = {
 12 |         'the', 'is', 'are', 'was', 'were', 'a', 'an', 'and', 
 13 |         'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
 14 |         'with', 'by', 'from', 'this', 'that', 'it', 'be',
 15 |         'do', 'does', 'did', 'have', 'has', 'had', 'will',
 16 |         'would', 'could', 'should', 'may', 'might', 'can',
 17 |         'where', 'what', 'how', 'when', 'which', 'who', 'why'
 18 |     }
 19 |     words = re.findall(r'\b\w+\b', question.lower())
 20 |     keywords = [w for w in words if w not in stop_words 
 21 |                 and len(w) > 2]
 22 |     
 23 |     # Also add common code-related expansions
 24 |     expansions = {
 25 |         'auth': ['auth', 'authentication', 'login', 'jwt', 
 26 |                  'token', 'passport', 'middleware', 'session',
 27 |                  'cookie', 'oauth', 'bearer'],
 28 |         'database': ['database', 'db', 'model', 'schema', 
 29 |                      'mongoose', 'sequelize', 'prisma', 
 30 |                      'sqlalchemy', 'migration', 'query'],
 31 |         'route': ['route', 'router', 'endpoint', 'controller',
 32 |                   'handler', 'api', 'path', 'url'],
 33 |         'config': ['config', 'configuration', 'settings', 
 34 |                    'env', 'environment', 'setup'],
 35 |         'test': ['test', 'spec', 'jest', 'pytest', 'unittest'],
 36 |         'deploy': ['deploy', 'dockerfile', 'docker', 
 37 |                    'kubernetes', 'ci', 'cd', 'pipeline']
 38 |     }
 39 |     
 40 |     expanded = list(keywords)
 41 |     for kw in keywords:
 42 |         if kw in expansions:
 43 |             expanded.extend(expansions[kw])
 44 |     
 45 |     return list(set(expanded))
 46 | 
 47 | 
 48 | def find_relevant_files(keywords: list, 
 49 |                         raw_files: list) -> list:
 50 |     """
 51 |     Score each file based on keyword matches and return top 5.
 52 |     """
 53 |     scored_files = []
 54 |     
 55 |     for f in raw_files:
 56 |         score = 0
 57 |         path_lower = f.get("path", "").lower()
 58 |         content_lower = f.get("content", "").lower()
 59 |         
 60 |         for kw in keywords:
 61 |             # Path match scores higher than content match
 62 |             if kw in path_lower:
 63 |                 score += 3
 64 |             # Match in first 200 chars (likely imports/class def)
 65 |             if kw in content_lower[:200]:
 66 |                 score += 2
 67 |             # Match anywhere in content
 68 |             elif kw in content_lower:
 69 |                 score += 1
 70 |         
 71 |         if score > 0:
 72 |             scored_files.append((score, f))
 73 |     
 74 |     # Sort by score descending, take top 5
 75 |     scored_files.sort(key=lambda x: x[0], reverse=True)
 76 |     return [f for _, f in scored_files[:5]]
 77 | 
 78 | 
 79 | def extract_relevant_section(content: str, 
 80 |                               keywords: list) -> str:
 81 |     """
 82 |     Extract sections of content that contain keywords with context.
 83 |     """
 84 |     lines = content.split('\n')
 85 |     relevant_lines = []
 86 |     
 87 |     for i, line in enumerate(lines):
 88 |         line_lower = line.lower()
 89 |         if any(kw in line_lower for kw in keywords):
 90 |             # Include 3 lines before and after for context
 91 |             start = max(0, i - 3)
 92 |             end = min(len(lines), i + 4)
 93 |             relevant_lines.extend(lines[start:end])
 94 |             relevant_lines.append("...")
 95 |     
 96 |     if relevant_lines:
 97 |         return '\n'.join(relevant_lines[:60])
 98 |     # Fallback to first 500 chars
 99 |     return content[:500]
100 | 
101 | 
102 | def build_prompt(question: str, context: str, 
103 |                  relevant_files: list,
104 |                  keywords: list) -> str:
105 |     """
106 |     Build a structured prompt with relevant file sections.
107 |     """
108 |     files_context = ""
109 |     for f in relevant_files:
110 |         section = extract_relevant_section(
111 |             f.get("content", ""), keywords
112 |         )
113 |         files_context += (
114 |             f"\n\n=== FILE: {f['path']} ===\n{section}"
115 |         )
116 |     
117 |     return f"""You are an expert software engineer with deep knowledge of this specific codebase.
118 | 
119 | INSTRUCTIONS:
120 | - Answer ONLY based on the code and files provided below
121 | - Be specific: name exact files, functions, line patterns
122 | - If you see relevant code, quote it briefly
123 | - If not found in provided files, say exactly:
124 |   "Not found in the {len(relevant_files)} analyzed files. Try asking about: [suggest related topic]"
125 | - Never give generic advice not grounded in this code
126 | - Keep answer under 200 words but be complete
127 | 
128 | REPOSITORY SUMMARY:
129 | {context[:800]}
130 | 
131 | MOST RELEVANT SOURCE FILES ({len(relevant_files)} files):
132 | {files_context[:3000] if files_context else "No files matched this query."}
133 | 
134 | QUESTION: {question}
135 | 
136 | SPECIFIC ANSWER (cite file names):"""
137 | 
138 | 
139 | def answer_question(question: str, context: str,
140 |                     raw_files: list = []) -> dict:
141 |     """
142 |     Answer questions about the codebase using improved keyword extraction,
143 |     file matching, and context building.
144 |     """
145 |     keywords = extract_keywords(question)
146 |     relevant_files = find_relevant_files(keywords, raw_files)
147 |     prompt = build_prompt(question, context, 
148 |                           relevant_files, keywords)
149 |     
150 |     cache_key = f"qa_{hash(question[:80])}_{hash(context[:80])}"
151 |     
152 |     try:
153 |         answer = watsonx_client.generate_text(
154 |             prompt=prompt,
155 |             cache_key=cache_key,
156 |             max_tokens=700
157 |         )
158 |         return {
159 |             "answer": answer,
160 |             "sources": [f["path"] for f in relevant_files],
161 |             "keywords_used": keywords,
162 |             "files_searched": len(raw_files),
163 |             "files_matched": len(relevant_files),
164 |             "powered_by": "IBM watsonx.ai"
165 |         }
166 |     except Exception as e:
167 |         print(f"[qa] watsonx error: {e}")
168 |         fallback = ""
169 |         for f in relevant_files[:2]:
170 |             section = extract_relevant_section(
171 |                 f.get("content",""), keywords
172 |             )
173 |             fallback += f"\n{f['path']}:\n{section}\n"
174 |         return {
175 |             "answer": (
176 |                 f"AI unavailable. Relevant code found:\n"
177 |                 f"{fallback[:800] if fallback else 'No matches found.'}"
178 |             ),
179 |             "sources": [f["path"] for f in relevant_files],
180 |             "powered_by": "fallback"
181 |         }
182 | 
183 | 
184 | # Made with Bob
</content>
</file>
<file><path>backend/main.py</path>
<content lines="1-401">
  1 | """
  2 | FastAPI application for GitHub repository analysis.
  3 | """
  4 | from dotenv import load_dotenv
  5 | from pathlib import Path
  6 | load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)
  7 | import os
  8 | 
  9 | from fastapi import FastAPI, HTTPException
 10 | from fastapi.middleware.cors import CORSMiddleware
 11 | from pydantic import BaseModel, HttpUrl, field_validator
 12 | from typing import Dict, Any, Optional
 13 | import logging
 14 | import re
 15 | 
 16 | # Import custom modules for GitHub API interaction and documentation generation
 17 | from github_client import fetch_repo_data
 18 | from doc_generator import generate_onboarding_doc
 19 | from orchestrate_agent import answer_question
 20 | import watsonx_client
 21 | 
 22 | # Configure logging to track application behavior and errors
 23 | logging.basicConfig(level=logging.INFO)
 24 | logger = logging.getLogger(__name__)
 25 | 
 26 | # Module-level variables to store the last generated onboarding document and raw files
 27 | _last_onboarding_doc: Optional[str] = None
 28 | _last_repo_files: list = []
 29 | 
 30 | # Initialize FastAPI application with metadata
 31 | app = FastAPI(
 32 |     title="DevOnboard API",
 33 |     description="API for analyzing GitHub repositories",
 34 |     version="1.0.0"
 35 | )
 36 | 
 37 | # Configure CORS (Cross-Origin Resource Sharing) to allow frontend access
 38 | # Reads allowed origins from environment variable, defaults to common development ports
 39 | ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
 40 | 
 41 | # Add CORS middleware to handle cross-origin requests from frontend
 42 | app.add_middleware(
 43 |     CORSMiddleware,
 44 |     allow_origins=ALLOWED_ORIGINS,  # Configurable via environment variable
 45 |     allow_credentials=True,  # Allow cookies and authentication headers
 46 |     allow_methods=["GET", "POST", "OPTIONS"],  # Allowed HTTP methods
 47 |     allow_headers=["Content-Type", "Authorization"],  # Allowed request headers
 48 | )
 49 | 
 50 | 
 51 | class AnalyzeRequest(BaseModel):
 52 |     """
 53 |     Request model for repository analysis endpoint.
 54 |     
 55 |     Attributes:
 56 |         github_url: GitHub repository URL to analyze
 57 |     """
 58 |     github_url: str
 59 | 
 60 |     @field_validator('github_url')
 61 |     @classmethod
 62 |     def validate_github_url(cls, v: str) -> str:
 63 |         """
 64 |         Validate GitHub URL format and content.
 65 |         
 66 |         Performs multiple validation checks:
 67 |         - Removes leading/trailing whitespace
 68 |         - Ensures URL is not empty
 69 |         - Validates GitHub URL pattern (supports http/https, with/without www)
 70 |         - Checks for potentially dangerous special characters
 71 |         
 72 |         Args:
 73 |             cls: Class reference (required for classmethod)
 74 |             v: GitHub URL string to validate
 75 |             
 76 |         Returns:
 77 |             str: Validated and cleaned GitHub URL
 78 |             
 79 |         Raises:
 80 |             ValueError: If URL is empty, has invalid format, or contains dangerous characters
 81 |         """
 82 |         # Strip whitespace from both ends of the URL
 83 |         v = v.strip()
 84 |         
 85 |         # Check for empty or whitespace-only strings
 86 |         if not v:
 87 |             raise ValueError("GitHub URL cannot be empty")
 88 |         
 89 |         # Check for valid GitHub URL pattern using regex
 90 |         # Supports: http/https, with/without www, with/without .git extension
 91 |         github_pattern = r'^https?://(?:www\.)?github\.com/[\w\-\.]+/[\w\-\.]+/?(?:\.git)?$'
 92 |         if not re.match(github_pattern, v, re.IGNORECASE):
 93 |             raise ValueError(
 94 |                 "Invalid GitHub URL format. Expected format: https://github.com/owner/repo"
 95 |             )
 96 |         
 97 |         # Check for special characters that might cause security issues or parsing errors
 98 |         if any(char in v for char in ['<', '>', '"', '{', '}', '|', '\\', '^', '`']):
 99 |             raise ValueError("GitHub URL contains invalid characters")
100 |         
101 |         return v
102 | 
103 |     class Config:
104 |         """Pydantic model configuration with example for API documentation."""
105 |         json_schema_extra = {
106 |             "example": {
107 |                 "github_url": "https://github.com/owner/repo"
108 |             }
109 |         }
110 | 
111 | 
112 | class AnalyzeResponse(BaseModel):
113 |     """
114 |     Response model for repository analysis endpoint.
115 |     
116 |     Attributes:
117 |         onboarding_doc: Generated markdown documentation for the repository
118 |         file_count: Total number of files analyzed in the repository
119 |         metadata: Structured metadata about the analyzed repository
120 |     """
121 |     onboarding_doc: str
122 |     file_count: int
123 |     metadata: Optional[Dict[str, Any]] = None
124 | 
125 | 
126 | class AskRequest(BaseModel):
127 |     """
128 |     Request model for Q&A endpoint.
129 |     
130 |     Attributes:
131 |         question: User's question about the repository
132 |     """
133 |     question: str
134 | 
135 |     @field_validator('question')
136 |     @classmethod
137 |     def validate_question(cls, v: str) -> str:
138 |         """
139 |         Validate question is not empty.
140 |         
141 |         Args:
142 |             cls: Class reference (required for classmethod)
143 |             v: Question string to validate
144 |             
145 |         Returns:
146 |             str: Validated question
147 |             
148 |         Raises:
149 |             ValueError: If question is empty
150 |         """
151 |         v = v.strip()
152 |         if not v:
153 |             raise ValueError("Question cannot be empty")
154 |         if len(v) > 500:
155 |             raise ValueError("Question is too long (max 500 characters)")
156 |         return v
157 | 
158 |     class Config:
159 |         """Pydantic model configuration with example for API documentation."""
160 |         json_schema_extra = {
161 |             "example": {
162 |                 "question": "What are the key files in this repository?"
163 |             }
164 |         }
165 | 
166 | 
167 | class AskResponse(BaseModel):
168 |     """
169 |     Response model for Q&A endpoint.
170 |     
171 |     Attributes:
172 |         answer: AI-generated answer to the question
173 |         sources: List of sources used for the answer
174 |         powered_by: AI model information
175 |         files_searched: Number of files searched
176 |         files_matched: Number of files matched
177 |     """
178 |     answer: str
179 |     sources: list[str]
180 |     powered_by: Optional[str] = None
181 |     files_searched: Optional[int] = None
182 |     files_matched: Optional[int] = None
183 | 
184 | 
185 | @app.get("/")
186 | async def root() -> Dict[str, str]:
187 |     """
188 |     Root endpoint providing API information.
189 |     
190 |     Returns:
191 |         Dict[str, str]: API name, version, and documentation URL
192 |     """
193 |     return {
194 |         "message": "DevOnboard API",
195 |         "version": "1.0.0",
196 |         "docs": "/docs"
197 |     }
198 | 
199 | 
200 | @app.get("/watsonx-status")
201 | async def watsonx_status():
202 |     configured = watsonx_client.is_configured()
203 |     return {
204 |         "watsonx_connected": configured,
205 |         "model": watsonx_client.get_model_id(),
206 |         "region": watsonx_client.get_url(),
207 |         "project_id": watsonx_client.get_project_id_preview(),
208 |         "cache_entries": watsonx_client.get_cache_size(),
209 |         "ibm_bob_built": True,
210 |         "status": "ready" if configured else "not configured"
211 |     }
212 | 
213 | 
214 | @app.get("/health")
215 | async def health():
216 |     configured = watsonx_client.is_configured()
217 |     return {
218 |         "status": "running",
219 |         "watsonx_orchestrate_compatible": True,
220 |         "ibm_bob_built": True,
221 |         "version": "1.0.0",
222 |         "services": {
223 |             "github_api": True,
224 |             "watsonx_ai": configured,
225 |             "model": watsonx_client.get_model_id()
226 |         }
227 |     }
228 | 
229 | 
230 | @app.post("/analyze", response_model=AnalyzeResponse)
231 | async def analyze_repository(request: AnalyzeRequest) -> AnalyzeResponse:
232 |     """
233 |     Analyze a GitHub repository.
234 |     
235 |     Args:
236 |         request: AnalyzeRequest containing the GitHub repository URL
237 |         
238 |     Returns:
239 |         AnalyzeResponse with repository analysis results
240 |         
241 |     Raises:
242 |         HTTPException: If the repository cannot be accessed or analyzed
243 |     """
244 |     global _last_onboarding_doc, _last_repo_files
245 |     
246 |     # Clear watsonx cache for fresh analysis
247 |     watsonx_client.clear_cache()
248 |     
249 |     try:
250 |         # Log the start of repository analysis
251 |         logger.info(f"Analyzing repository: {request.github_url}")
252 |         
253 |         # Fetch repository data from GitHub
254 |         try:
255 |             repo_data = await fetch_repo_data(request.github_url)
256 |         except ValueError as e:
257 |             # Invalid URL or repository not found
258 |             error_msg = str(e)
259 |             logger.error(f"ValueError: {error_msg}")
260 |             print(f"ERROR: {error_msg}")  # Print to terminal for debugging
261 |             if "not found" in error_msg.lower():
262 |                 raise HTTPException(status_code=404, detail=error_msg)
263 |             else:
264 |                 raise HTTPException(status_code=400, detail=error_msg)
265 |         except PermissionError as e:
266 |             # Rate limit or authentication issues
267 |             error_msg = str(e)
268 |             logger.error(f"PermissionError: {error_msg}")
269 |             print(f"ERROR: {error_msg}")  # Print to terminal for debugging
270 |             if "rate limit" in error_msg.lower():
271 |                 raise HTTPException(status_code=429, detail=error_msg)
272 |             else:
273 |                 raise HTTPException(status_code=403, detail=error_msg)
274 |         except ConnectionError as e:
275 |             # Network connectivity issues
276 |             error_msg = str(e)
277 |             logger.error(f"ConnectionError: {error_msg}")
278 |             print(f"ERROR: {error_msg}")  # Print to terminal for debugging
279 |             raise HTTPException(status_code=503, detail=error_msg)
280 |         
281 |         # Extract files from repo_data
282 |         files = repo_data.get("files", [])
283 |         file_count = repo_data.get("file_count", 0)
284 |         
285 |         logger.info(f"Successfully fetched repository data: {file_count} total files, {len(files)} priority files")
286 |         
287 |         # Generate onboarding documentation
288 |         try:
289 |             # Pass the full repo_data dict to the doc generator
290 |             onboarding_doc, metadata = generate_onboarding_doc(repo_data)
291 |             
292 |             # Validate generated documentation is not empty
293 |             if not onboarding_doc or not onboarding_doc.strip():
294 |                 raise ValueError("Generated documentation is empty")
295 |             
296 |             # Store the generated documentation and raw files for use by /ask endpoint
297 |             _last_onboarding_doc = onboarding_doc
298 |             _last_repo_files = files
299 |                 
300 |         except Exception as doc_error:
301 |             # Handle any errors during documentation generation
302 |             error_msg = f"Failed to generate documentation: {str(doc_error)}"
303 |             logger.error(error_msg)
304 |             print(f"ERROR: {error_msg}")  # Print to terminal for debugging
305 |             raise HTTPException(status_code=500, detail=error_msg)
306 |         
307 |         logger.info("Generated onboarding documentation with metadata")
308 |         
309 |         # Return successful response with documentation, file count, and metadata
310 |         return AnalyzeResponse(
311 |             onboarding_doc=onboarding_doc,
312 |             file_count=file_count,
313 |             metadata=metadata
314 |         )
315 |         
316 |     except HTTPException:
317 |         # Re-raise HTTP exceptions as-is (already properly formatted)
318 |         raise
319 |     except Exception as e:
320 |         # Catch-all for unexpected errors
321 |         error_msg = f"Unexpected error: {str(e)}"
322 |         logger.error(error_msg, exc_info=True)
323 |         print(f"ERROR: {error_msg}")  # Print to terminal for debugging
324 |         raise HTTPException(status_code=500, detail=f"Failed to analyze repository: {str(e)}")
325 | 
326 | 
327 | @app.post("/ask", response_model=AskResponse)
328 | async def ask_question(request: AskRequest) -> AskResponse:
329 |     """
330 |     Answer a question about the repository using AI.
331 |     
332 |     Args:
333 |         request: AskRequest containing the question
334 |         
335 |     Returns:
336 |         AskResponse with the AI-generated answer
337 |         
338 |     Raises:
339 |         HTTPException: If the question cannot be answered or no repository has been analyzed
340 |     """
341 |     global _last_onboarding_doc, _last_repo_files
342 |     
343 |     try:
344 |         logger.info(f"Processing question: {request.question[:100]}...")
345 |         
346 |         # Check if we have a stored onboarding document
347 |         if not _last_onboarding_doc:
348 |             raise HTTPException(
349 |                 status_code=400,
350 |                 detail="No repository has been analyzed yet. Please analyze a repository first using the /analyze endpoint."
351 |             )
352 |         
353 |         # Call the orchestrate agent to answer the question using stored context and raw files
354 |         result = answer_question(request.question, _last_onboarding_doc, _last_repo_files)
355 |         
356 |         logger.info("Question answered successfully")
357 |         
358 |         return AskResponse(
359 |             answer=result["answer"],
360 |             sources=result["sources"],
361 |             powered_by=result.get("powered_by"),
362 |             files_searched=result.get("files_searched"),
363 |             files_matched=result.get("files_matched")
364 |         )
365 |         
366 |     except HTTPException:
367 |         # Re-raise HTTP exceptions as-is
368 |         raise
369 |     except ValueError as e:
370 |         # Handle validation errors
371 |         logger.error(f"Invalid request: {str(e)}")
372 |         raise HTTPException(
373 |             status_code=400,
374 |             detail=f"Invalid request: {str(e)}"
375 |         )
376 |     except Exception as e:
377 |         # Catch-all for unexpected errors
378 |         logger.error(f"Error answering question: {str(e)}", exc_info=True)
379 |         raise HTTPException(
380 |             status_code=500,
381 |             detail=f"Failed to answer question: {str(e)}"
382 |         )
383 | 
384 | 
385 | if __name__ == "__main__":
386 |     """
387 |     Run the FastAPI application using Uvicorn server.
388 |     
389 |     This block only executes when the script is run directly (not imported).
390 |     Starts the server on all network interfaces (0.0.0.0) on port 8000
391 |     with auto-reload enabled for development.
392 |     """
393 |     import uvicorn
394 |     uvicorn.run(
395 |         "main:app",  # Application instance to run
396 |         host="0.0.0.0",  # Listen on all network interfaces
397 |         port=8000,  # Port to bind to
398 |         reload=True  # Auto-reload on code changes (development only)
399 |     )
400 | 
401 | # Made with Bob
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
backend\orchestrate_agent.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/doc_generator.py,backend/watsonx_client.py,backend/orchestrate_agent.py,backend/main.py,backend/github_client.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:03:01.324Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.09

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

I'll implement the complete rewrite as specified in the task. This is a multi-step process, so let me create a TODO list first.

<update_todo_list>
<todos>
[ ] Part 1: Rewrite github_client.py with repo type detection and smart file selection
[ ] Part 2: Rewrite doc_generator.py with new section structure
[ ] Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring
[ ] Part 4: Update main.py to store metadata and pass raw files to Q&A
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
backend\orchestrate_agent.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/doc_generator.py,backend/watsonx_client.py,backend/orchestrate_agent.py,backend/main.py,backend/github_client.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:03:06.939Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.25

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Part 1: Rewrite github_client.py with repo type detection and smart file selection | Pending |
| 2 | Part 2: Rewrite doc_generator.py with new section structure | Pending |
| 3 | Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring | Pending |
| 4 | Part 4: Update main.py to store metadata and pass raw files to Q&A | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me start with Part 1 - rewriting github_client.py with the complete new strategy:

<write_to_file>
<path>backend/github_client.py</path>
<content>"""
GitHub API client for fetching repository contents.
Complete rewrite with repo type detection and smart file selection.
"""
import os
import re
import base64
import asyncio
from typing import Dict, Any, Optional, List
import httpx
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables from .env file in the same directory
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Initialize logger
logger = logging.getLogger(__name__)

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Request timeout in seconds
REQUEST_TIMEOUT = 30.0

# Module-level cache for repository data
_repo_cache: Dict[str, Dict[str, Any]] = {}


def parse_github_url(url: str) -> tuple[str, str]:
    """
    Parse GitHub URL to extract owner and repository name.
    
    Supports formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/tree/main
    - github.com/owner/repo
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo)
        
    Raises:
        ValueError: If URL format is invalid
    """
    if not url or not isinstance(url, str):
        raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
    
    url = url.strip()
    
    if not url:
        raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
    
    # Remove trailing slashes
    url = url.rstrip("/")
    
    # Remove .git extension if present
    if url.endswith(".git"):
        url = url[:-4]
    
    # Remove tree/branch paths (e.g., /tree/main)
    url = re.sub(r'/tree/[^/]+.*$', '', url)
    
    # Pattern to match GitHub URLs
    pattern = r'(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s]+)'
    
    match = re.search(pattern, url, re.IGNORECASE)
    
    if not match:
        raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
    
    owner = match.group(1).strip()
    repo = match.group(2).strip()
    
    if not owner or not repo:
        raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")
    
    return owner, repo


def detect_language(file_paths: List[str]) -> str:
    """Detect primary programming language from file extensions."""
    extensions = {}
    for p in file_paths:
        ext = p.rsplit('.', 1)[-1].lower() if '.' in p else ''
        if ext in ['js', 'ts', 'jsx', 'tsx', 'py', 'java',
                   'go', 'rs', 'rb', 'php', 'cs', 'cpp', 'c']:
            extensions[ext] = extensions.get(ext, 0) + 1
    
    if not extensions:
        return 'Unknown'
    
    primary = max(extensions, key=extensions.get)
    mapping = {
        'js': 'JavaScript', 'ts': 'TypeScript',
        'jsx': 'JavaScript/React', 'tsx': 'TypeScript/React',
        'py': 'Python', 'java': 'Java', 'go': 'Go',
        'rs': 'Rust', 'rb': 'Ruby', 'php': 'PHP',
        'cs': 'C#', 'cpp': 'C++', 'c': 'C'
    }
    return mapping.get(primary, primary.upper())


def detect_framework(file_paths: List[str]) -> str:
    """Detect framework from file paths and names."""
    paths_str = ' '.join(file_paths).lower()
    
    frameworks = {
        'Next.js': ['next.config', 'pages/_app', 'app/page'],
        'React': ['react', '.jsx', '.tsx'],
        'Vue': ['vue.config', '.vue'],
        'Angular': ['angular.json', 'ng-'],
        'Express': ['express', 'router'],
        'FastAPI': ['fastapi', '@app.get', '@router'],
        'Django': ['django', 'settings.py', 'urls.py'],
        'Flask': ['flask', '@app.route'],
        'Spring': ['spring', 'application.properties'],
        'Rails': ['gemfile', 'routes.rb'],
        'Laravel': ['artisan', 'composer.json']
    }
    
    for fw, indicators in frameworks.items():
        if any(ind in paths_str for ind in indicators):
            return fw
    
    return 'Unknown'


def detect_repo_type(file_paths: List[str]) -> Dict[str, Any]:
    """
    Detect repository type by scanning all file paths.
    Returns dict with has_frontend, has_backend, has_database, has_auth, has_tests, language, framework.
    """
    paths_str = ' '.join(file_paths).lower()
    
    return {
        'has_frontend': any(x in paths_str for x in [
            'react', 'vue', 'angular', 'next', 'nuxt',
            'jsx', 'tsx', 'html', 'css', 'component'
        ]),
        'has_backend': any(x in paths_str for x in [
            'server', 'app.py', 'main.py', 'index.js',
            'app.js', 'django', 'flask', 'fastapi',
            'express', 'spring', 'rails', 'api', 'route'
        ]),
        'has_database': any(x in paths_str for x in [
            'model', 'schema', 'migration', 'mongoose',
            'sequelize', 'prisma', 'sqlalchemy', 'entity',
            'database', 'db'
        ]),
        'has_auth': any(x in paths_str for x in [
            'auth', 'login', 'jwt', 'passport', 'oauth',
            'session', 'middleware', 'guard', 'token'
        ]),
        'has_tests': any(x in paths_str for x in [
            'test', 'spec', '__test__', 'jest', 'pytest'
        ]),
        'language': detect_language(file_paths),
        'framework': detect_framework(file_paths)
    }


async def _fetch_single_file(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    path: str,
    headers: Dict[str, str],
    size: int = 0,
    priority: int = 4,
    category: str = "other"
) -> Optional[Dict[str, Any]]:
    """
    Fetch a single file's content from GitHub API with metadata.
    
    Returns:
        Dictionary with path, content (up to 8000 chars), size, priority, category
    """
    content_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
    
    try:
        content_response = await client.get(content_url, headers=headers)
        
        if content_response.status_code == 200:
            content_data = content_response.json()
            encoded_content = content_data.get("content", "")
            
            if encoded_content:
                try:
                    # Decode base64 content
                    decoded = base64.b64decode(encoded_content)
                    text_content = decoded.decode("utf-8", errors="ignore")
                    
                    # Limit to 8000 chars
                    text_content = text_content[:8000]
                    
                    logger.info(f"Fetched {path} (priority={priority}, category={category})")
                    return {
                        "path": path,
                        "content": text_content,
                        "size": size,
                        "priority": priority,
                        "category": category
                    }
                except Exception as e:
                    logger.warning(f"Failed to decode {path}: {e}")
    except Exception as e:
        logger.warning(f"Failed to fetch {path}: {e}")
    
    return None


async def fetch_repo_data(url: str) -> Dict[str, Any]:
    """
    Fetch repository data with smart file selection based on repo type detection.
    
    Returns:
        {
            "owner": str,
            "repo": str,
            "description": str,
            "stars": int,
            "language": str,
            "files": [{"path": str, "content": str, "priority": int, "category": str}],
            "file_count": int,
            "repo_type": dict  # Detection results
        }
    """
    # Parse GitHub URL
    try:
        owner, repo = parse_github_url(url)
    except ValueError as e:
        raise ValueError(str(e))
    
    # Check cache first
    cache_key = f"{owner}/{repo}"
    if cache_key in _repo_cache:
        logger.info(f"Returning cached data for {cache_key}")
        return _repo_cache[cache_key]
    
    logger.info(f"Fetching repository data for {owner}/{repo}")
    
    # Set up headers
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DevOnboard-App"
    }
    
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
        logger.info("Using GitHub token for authentication")
    else:
        logger.warning("No GitHub token found - rate limits will be lower")
    
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            # Step 1: Get repository metadata
            repo_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
            
            try:
                response = await client.get(repo_url, headers=headers)
            except (httpx.ConnectError, httpx.TimeoutException):
                raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
            
            # Handle HTTP errors
            if response.status_code == 401:
                raise PermissionError("Invalid GitHub token. Check your GITHUB_TOKEN in .env")
            elif response.status_code == 403:
                raise PermissionError("GitHub API rate limit exceeded. Add a GITHUB_TOKEN to .env")
            elif response.status_code == 404:
                raise ValueError("Repository not found. Check the URL and make sure it is public")
            
            response.raise_for_status()
            repo_data = response.json()
            
            # Extract repository metadata
            description = repo_data.get("description", "")
            stars = repo_data.get("stargazers_count", 0)
            language = repo_data.get("language", "")
            default_branch = repo_data.get("default_branch", "main")
            
            # Step 2: Get repository file tree
            tree_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
            
            try:
                response = await client.get(tree_url, headers=headers)
            except (httpx.ConnectError, httpx.TimeoutException):
                raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
            
            if response.status_code == 401:
                raise PermissionError("Invalid GitHub token. Check your GITHUB_TOKEN in .env")
            elif response.status_code == 403:
                raise PermissionError("GitHub API rate limit exceeded. Add a GITHUB_TOKEN to .env")
            elif response.status_code == 404:
                raise ValueError("Repository not found. Check the URL and make sure it is public")
            
            response.raise_for_status()
            tree_data = response.json()
            
            tree = tree_data.get("tree", [])
            
            if not tree:
                raise ValueError("Repository appears to be empty")
            
            # Step 3: Detect repo type
            all_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
            repo_type = detect_repo_type(all_paths)
            
            logger.info(f"Detected: {repo_type['language']}, {repo_type['framework']}, "
                       f"auth={repo_type['has_auth']}, db={repo_type['has_database']}")
            
            # Step 4: Smart file selection
            files_to_fetch = []
            file_count = 0
            
            # Priority 1 - Config files (always fetch)
            config_files = [
                "README.md", "README.rst", "package.json", "requirements.txt",
                "setup.py", "setup.cfg", "pyproject.toml", "pom.xml",
                "build.gradle", "Cargo.toml", "go.mod", "composer.json",
                "Gemfile", ".env.example", "docker-compose.yml", "Dockerfile"
            ]
            
            for item in tree:
                if item.get("type") != "blob":
                    continue
                
                file_count += 1
                path = item.get("path", "")
                size = item.get("size", 0)
                filename = path.split("/")[-1]
                path_lower = path.lower()
                
                if filename in config_files:
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 1, "category": "config"
                    })
            
            # Priority 2 - Entry points
            entry_points = {
                "index.js": "entry", "index.ts": "entry", "app.js": "entry",
                "app.ts": "entry", "server.js": "entry", "server.ts": "entry",
                "main.js": "entry", "main.ts": "entry", "main.py": "entry",
                "app.py": "entry", "server.py": "entry", "wsgi.py": "entry",
                "asgi.py": "entry", "Main.java": "entry", "Application.java": "entry",
                "main.go": "entry"
            }
            
            for item in tree:
                if item.get("type") != "blob":
                    continue
                path = item.get("path", "")
                size = item.get("size", 0)
                filename = path.split("/")[-1]
                
                if filename in entry_points and not any(f["path"] == path for f in files_to_fetch):
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 2, "category": entry_points[filename]
                    })
                    break  # Only first match
            
            # Priority 3 - Based on detected repo type
            for item in tree:
                if item.get("type") != "blob":
                    continue
                path = item.get("path", "")
                size = item.get("size", 0)
                path_lower = path.lower()
                
                if any(f["path"] == path for f in files_to_fetch):
                    continue
                
                # Auth files
                if repo_type['has_auth'] and any(kw in path_lower for kw in [
                    'auth', 'login', 'jwt', 'passport', 'middleware',
                    'guard', 'permission', 'session', 'oauth', 'token'
                ]):
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 3, "category": "auth"
                    })
                
                # Database/Model files
                elif repo_type['has_database'] and any(kw in path_lower for kw in [
                    'model', 'schema', 'entity', 'migration', 'repository', 'dao'
                ]):
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 3, "category": "database"
                    })
                
                # Route files
                elif repo_type['has_backend'] and any(kw in path_lower for kw in [
                    'route', 'router', 'controller', 'handler', 'endpoint', 'api', 'view'
                ]):
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 3, "category": "route"
                    })
                
                # Component files
                elif repo_type['has_frontend'] and any(kw in path_lower for kw in [
                    'page', 'component', 'screen', 'layout', 'store', 'context', 'hook'
                ]):
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 3, "category": "component"
                    })
            
            # Priority 4 - Fill remaining slots (up to 40 total)
            exclude_patterns = ['test', 'spec', '__test__', '.test.', 'dist/', 
                              'build/', 'node_modules', '__pycache__', '.git']
            
            for item in tree:
                if len(files_to_fetch) >= 40:
                    break
                
                if item.get("type") != "blob":
                    continue
                
                path = item.get("path", "")
                size = item.get("size", 0)
                path_lower = path.lower()
                
                if any(f["path"] == path for f in files_to_fetch):
                    continue
                
                # Skip excluded patterns
                if any(ex in path_lower for ex in exclude_patterns):
                    continue
                
                # Prefer files in root, src/, app/, lib/
                folder = path.split("/")[0] if "/" in path else ""
                if folder in ["", "src", "app", "lib"] or "/" not in path:
                    files_to_fetch.append({
                        "path": path, "size": size, "priority": 4, "category": "other"
                    })
            
            logger.info(f"Selected {len(files_to_fetch)} files to fetch (out of {file_count} total)")
            
            # Step 5: Fetch all files in parallel
            fetch_tasks = [
                _fetch_single_file(
                    client, owner, repo,
                    f["path"], headers, f["size"], f["priority"], f["category"]
                )
                for f in files_to_fetch
            ]
            
            results = await asyncio.gather(*fetch_tasks, return_exceptions=False)
            files = [r for r in results if r is not None]
            
            logger.info(f"Successfully fetched {len(files)} files with full content")
            
            # Prepare result
            result = {
                "owner": owner,
                "repo": repo,
                "description": description,
                "stars": stars,
                "language": language,
                "files": files,
                "file_count": file_count,
                "repo_type": repo_type
            }
            
            # Cache the result
            _repo_cache[cache_key] = result
            
            return result
            
    except (httpx.ConnectError, httpx.TimeoutException):
        raise ConnectionError("Cannot reach GitHub API. Check your internet connection")
    except (ValueError, PermissionError, ConnectionError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise ConnectionError(f"Failed to fetch repository data: {str(e)}")


# Made with Bob
</content>
<line_count>485</line_count>
</write_to_file>

---

**User:**

[write_to_file for 'backend/github_client.py'] Result:
<file_write_result>
<path>backend/github_client.py</path>
<operation>modified</operation>
<user_edits>@@ -479,4 +479,4 @@
         raise ConnectionError(f"Failed to fetch repository data: {str(e)}")
 
 
-# Made with Bob
\ No newline at end of file
+# Made with Bob
</user_edits>
<problems>

New problems detected after saving the file:
backend/github_client.py
- [basedpyright Error] 98 |     primary = max(extensions, key=extensions.get) : No overloads for "max" match the provided arguments
- [basedpyright Error] 98 |     primary = max(extensions, key=extensions.get) : Argument of type "Overload[(key: Unknown, default: None = None, /) -&gt; (Unknown | None), (key: Unknown, default: Unknown, /) -&gt; Unknown, (key: Unknown, default: _T@get, /) -&gt; (Unknown | _T@get)]" cannot be assigned to parameter "key" of type "(_T@max) -&gt; SupportsRichComparison" in function "max"
  No overloaded function matches type "(Unknown) -&gt; SupportsRichComparison"
- [basedpyright Error] 106 |     return mapping.get(primary, primary.upper()) : Type "str | None" is not assignable to return type "str"
  Type "str | None" is not assignable to type "str"
    "None" is not assignable to "str"</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
<i>If the user's edits have addressed part of the task or changed the requirements, adjust your approach accordingly.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
backend\github_client.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/doc_generator.py,backend/watsonx_client.py,backend/orchestrate_agent.py,backend/github_client.py,backend/main.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Recently Modified Files
These files have been modified since you last accessed them (file was just edited so you may need to re-read it before editing):
backend/github_client.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
### New Output
WARNING:  WatchFiles detected changes in 'github_client.py'. Reloading...


# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:04:11.456Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.42

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Part 1: Rewrite github_client.py with repo type detection and smart file selection | Pending |
| 2 | Part 2: Rewrite doc_generator.py with new section structure | Pending |
| 3 | Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring | Pending |
| 4 | Part 4: Update main.py to store metadata and pass raw files to Q&A | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Good! Part 1 is complete. Let me update the TODO and move to Part 2:

<update_todo_list>
<todos>
[x] Part 1: Rewrite github_client.py with repo type detection and smart file selection
[-] Part 2: Rewrite doc_generator.py with new section structure
[ ] Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring
[ ] Part 4: Update main.py to store metadata and pass raw files to Q&A
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
backend\github_client.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/doc_generator.py,backend/watsonx_client.py,backend/orchestrate_agent.py,backend/github_client.py,backend/main.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:04:16.241Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.59

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Part 1: Rewrite github_client.py with repo type detection and smart file selection | Completed |
| 2 | Part 2: Rewrite doc_generator.py with new section structure | In Progress |
| 3 | Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring | Pending |
| 4 | Part 4: Update main.py to store metadata and pass raw files to Q&A | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me rewrite doc_generator.py with the new structure as specified:

<write_to_file>
<path>backend/doc_generator.py</path>
<content>"""
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
</content>
<line_count>268</line_count>
</write_to_file>

---

**User:**

[write_to_file for 'backend/doc_generator.py'] Result:
<file_write_result>
<path>backend/doc_generator.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
backend\doc_generator.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/watsonx_client.py,backend/orchestrate_agent.py,backend/github_client.py,backend/doc_generator.py,backend/main.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Recently Modified Files
These files have been modified since you last accessed them (file was just edited so you may need to re-read it before editing):
backend/doc_generator.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:05:06.464Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.78

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Part 1: Rewrite github_client.py with repo type detection and smart file selection | Completed |
| 2 | Part 2: Rewrite doc_generator.py with new section structure | In Progress |
| 3 | Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring | Pending |
| 4 | Part 4: Update main.py to store metadata and pass raw files to Q&A | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Excellent! Part 2 is complete. Let me update the TODO and move to Part 3:

<update_todo_list>
<todos>
[x] Part 1: Rewrite github_client.py with repo type detection and smart file selection
[x] Part 2: Rewrite doc_generator.py with new section structure
[-] Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring
[ ] Part 4: Update main.py to store metadata and pass raw files to Q&A
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
backend\doc_generator.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/watsonx_client.py,backend/orchestrate_agent.py,backend/github_client.py,backend/doc_generator.py,backend/main.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:05:11.849Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.96

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Part 1: Rewrite github_client.py with repo type detection and smart file selection | Completed |
| 2 | Part 2: Rewrite doc_generator.py with new section structure | Completed |
| 3 | Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring | In Progress |
| 4 | Part 4: Update main.py to store metadata and pass raw files to Q&A | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me rewrite orchestrate_agent.py with the complete new logic:

<write_to_file>
<path>backend/orchestrate_agent.py</path>
<content>"""
Q&A orchestration agent - Complete rewrite with better keyword extraction and file scoring.
"""
import re
import watsonx_client


def extract_keywords(question: str) -> list:
    """
    Extract meaningful keywords from question by removing stop words
    and adding semantic expansions.
    """
    stop_words = {
        'the', 'is', 'are', 'was', 'were', 'a', 'an', 'and',
        'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'this', 'that', 'it', 'be', 'do', 'does',
        'did', 'have', 'has', 'had', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'where', 'what', 'how',
        'when', 'which', 'who', 'why', 'me', 'my', 'your', 'their',
        'please', 'tell', 'show', 'give', 'find', 'get', 'list'
    }
    words = re.findall(r'\b\w+\b', question.lower())
    keywords = [
        w for w in words
        if w not in stop_words and len(w) > 2
    ]
    
    # Semantic expansions for common dev questions
    expansions = {
        'auth': ['auth', 'authentication', 'login', 'logout',
                 'jwt', 'token', 'passport', 'middleware',
                 'session', 'cookie', 'oauth', 'bearer',
                 'guard', 'permission', 'role', 'user'],
        'authentication': ['auth', 'login', 'jwt', 'token',
                          'passport', 'session', 'cookie'],
        'database': ['database', 'db', 'model', 'schema',
                    'mongoose', 'sequelize', 'prisma',
                    'sqlalchemy', 'migration', 'query',
                    'repository', 'entity', 'orm'],
        'route': ['route', 'router', 'endpoint', 'controller',
                 'handler', 'api', 'path', 'url', 'rest'],
        'api': ['route', 'router', 'endpoint', 'controller',
               'handler', 'rest', 'graphql', 'api'],
        'model': ['model', 'schema', 'entity', 'database',
                 'migration', 'orm', 'repository'],
        'test': ['test', 'spec', 'jest', 'pytest', 'unittest',
                'testing', 'mock', 'fixture'],
        'config': ['config', 'configuration', 'settings',
                  'env', 'environment', 'setup', 'options'],
        'middleware': ['middleware', 'interceptor', 'guard',
                      'filter', 'pipe', 'hook'],
        'deploy': ['deploy', 'dockerfile', 'docker',
                  'kubernetes', 'ci', 'cd', 'pipeline',
                  'workflow', 'action', 'heroku', 'vercel'],
        'error': ['error', 'exception', 'catch', 'try',
                 'handle', 'handling', 'logging', 'logger'],
        'security': ['security', 'auth', 'jwt', 'bcrypt',
                    'hash', 'encrypt', 'ssl', 'cors', 'csrf']
    }
    
    expanded = list(keywords)
    for kw in keywords:
        if kw in expansions:
            expanded.extend(expansions[kw])
    
    return list(set(expanded))


def score_and_rank_files(keywords: list, raw_files: list) -> list:
    """
    Score each file based on keyword matches and return top 6.
    """
    scored = []
    
    for f in raw_files:
        score = 0
        path = f.get('path', '').lower()
        content = f.get('content', '')
        content_lower = content.lower()
        category = f.get('category', 'other')
        priority = f.get('priority', 4)
        
        # Base score from priority
        score += (5 - priority)
        
        for kw in keywords:
            # Strongest signal: keyword in file path
            if kw in path:
                score += 5
            # Strong: in first 300 chars (imports, class def)
            if kw in content_lower[:300]:
                score += 3
            # Medium: in first 1000 chars
            elif kw in content_lower[:1000]:
                score += 2
            # Weak: anywhere in file
            elif kw in content_lower:
                score += 1
        
        # Boost auth/route files for relevant questions
        if category in ['auth', 'route', 'database']:
            score += 2
        
        if score > 0:
            scored.append((score, f))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:6]]


def extract_relevant_section(content: str, keywords: list, max_lines: int = 80) -> str:
    """
    Extract sections of content that contain keywords with context.
    """
    if not content:
        return ""
    
    lines = content.split('\n')
    line_scores = []
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        score = sum(
            3 if kw in line_lower else 0
            for kw in keywords
        )
        line_scores.append((i, score))
    
    # Get top scoring line indices
    hot_lines = sorted(
        [x for x in line_scores if x[1] > 0],
        key=lambda x: x[1],
        reverse=True
    )[:8]
    
    if not hot_lines:
        # No keyword matches - return file start
        return '\n'.join(lines[:40])
    
    # Collect context windows around hot lines
    included = set()
    result_lines = []
    
    for idx, _ in sorted(hot_lines, key=lambda x: x[0]):
        start = max(0, idx - 4)
        end = min(len(lines), idx + 8)
        
        if start not in included:
            if included and min(included) < start - 2:
                result_lines.append('...')
            for i in range(start, end):
                if i not in included:
                    result_lines.append(lines[i])
                    included.add(i)
        
        if len(result_lines) >= max_lines:
            break
    
    return '\n'.join(result_lines)


def answer_question(question: str, context: str, raw_files: list = []) -> dict:
    """
    Answer questions about the codebase using improved keyword extraction,
    file matching, and context building.
    """
    keywords = extract_keywords(question)
    relevant_files = score_and_rank_files(keywords, raw_files)
    
    # Build rich file context
    files_context = ""
    for f in relevant_files:
        section = extract_relevant_section(
            f.get('content', ''), keywords
        )
        if section.strip():
            files_context += (
                f"\n\n{'='*50}\n"
                f"FILE: {f['path']}\n"
                f"CATEGORY: {f.get('category', 'other')}\n"
                f"{'='*50}\n"
                f"{section}"
            )
    
    # Count actual code lines provided
    code_lines = len(files_context.split('\n'))
    
    prompt = f"""You are a precise code analyst.
A developer is asking about a specific codebase.

YOUR RULES:
1. Answer ONLY from the code provided below
2. Always cite the EXACT file path like: "In `path/to/file.js`"
3. Quote actual code snippets when relevant (max 5 lines)
4. If you find the answer: be direct and specific
5. If NOT found in provided code: say exactly
   "I could not find this in the {len(relevant_files)} 
   files analyzed. The most relevant files checked were: 
   {', '.join([f['path'] for f in relevant_files[:3]])}"
6. Never invent code or make assumptions
7. Keep answer under 250 words

REPOSITORY CONTEXT:
{context[:600]}

SOURCE CODE ({len(relevant_files)} most relevant files, 
{code_lines} lines of code):
{files_context[:4000] if files_context else "No files matched this query."}

DEVELOPER QUESTION: {question}

PRECISE ANSWER:"""
    
    cache_key = (
        f"qa_{hash(question[:100])}_"
        f"{hash(context[:100])}"
    )
    
    try:
        answer = watsonx_client.generate_text(
            prompt=prompt,
            cache_key=cache_key,
            max_tokens=700
        )
        
        # Clean up any prompt leakage
        answer = answer.replace("PRECISE ANSWER:", "").strip()
        
        return {
            "answer": answer,
            "sources": [f["path"] for f in relevant_files],
            "keywords_matched": keywords[:8],
            "files_searched": len(raw_files),
            "files_matched": len(relevant_files),
            "powered_by": "IBM watsonx.ai"
        }
        
    except Exception as e:
        print(f"[qa] Error: {e}")
        fallback = ""
        for f in relevant_files[:2]:
            section = extract_relevant_section(
                f.get('content', ''), keywords, 30
            )
            fallback += (
                f"\n**{f['path']}:**\n"
                f"```\n{section}\n```\n"
            )
        return {
            "answer": (
                f"AI unavailable. "
                f"Most relevant code found:\n\n"
                f"{fallback if fallback else 'No matches.'}"
            ),
            "sources": [f["path"] for f in relevant_files],
            "powered_by": "fallback_keyword_search"
        }


# Made with Bob
</content>
<line_count>237</line_count>
</write_to_file>

---

**User:**

[write_to_file for 'backend/orchestrate_agent.py'] Result:
<file_write_result>
<path>backend/orchestrate_agent.py</path>
<operation>modified</operation>
<user_edits>@@ -257,4 +257,4 @@
         }
 
 
-# Made with Bob
\ No newline at end of file
+# Made with Bob
</user_edits>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
<i>If the user's edits have addressed part of the task or changed the requirements, adjust your approach accordingly.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
backend\orchestrate_agent.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/watsonx_client.py,backend/github_client.py,backend/doc_generator.py,backend/orchestrate_agent.py,backend/main.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Recently Modified Files
These files have been modified since you last accessed them (file was just edited so you may need to re-read it before editing):
backend/orchestrate_agent.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:05:56.067Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.16

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Part 1: Rewrite github_client.py with repo type detection and smart file selection | Completed |
| 2 | Part 2: Rewrite doc_generator.py with new section structure | Completed |
| 3 | Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring | In Progress |
| 4 | Part 4: Update main.py to store metadata and pass raw files to Q&A | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Perfect! Part 3 is complete. Now let me update the TODO and move to the final part - updating main.py:

<update_todo_list>
<todos>
[x] Part 1: Rewrite github_client.py with repo type detection and smart file selection
[x] Part 2: Rewrite doc_generator.py with new section structure
[x] Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring
[-] Part 4: Update main.py to store metadata and pass raw files to Q&A
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
backend\github_client.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/watsonx_client.py,backend/github_client.py,backend/doc_generator.py,backend/orchestrate_agent.py,backend/main.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:06:01.240Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.35

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Part 1: Rewrite github_client.py with repo type detection and smart file selection | Completed |
| 2 | Part 2: Rewrite doc_generator.py with new section structure | Completed |
| 3 | Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring | Completed |
| 4 | Part 4: Update main.py to store metadata and pass raw files to Q&A | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me update main.py to add the module-level variables and ensure proper data flow:

<apply_diff>
<path>backend/main.py</path>
<diff>
<<<<<<< SEARCH
# Module-level variables to store the last generated onboarding document and raw files
_last_onboarding_doc: Optional[str] = None
_last_repo_files: list = []
=======
# Module-level variables to store the last generated onboarding document, raw files, and metadata
last_onboarding_doc: str = ""
last_repo_files: list = []
last_repo_metadata: dict = {}
last_repo_owner: str = ""
last_repo_name: str = ""
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'backend/main.py'] Result:
<file_write_result>
<path>backend/main.py</path>
<operation>modified</operation>
<problems>

New problems detected after saving the file:
backend/main.py
- [basedpyright Error] 9 | from fastapi import FastAPI, HTTPException : Import "fastapi" could not be resolved
- [basedpyright Error] 10 | from fastapi.middleware.cors import CORSMiddleware : Import "fastapi.middleware.cors" could not be resolved
- [basedpyright Error] 396 |     import uvicorn : Import "uvicorn" could not be resolved</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
backend\main.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/watsonx_client.py,backend/github_client.py,backend/main.py,backend/doc_generator.py,backend/orchestrate_agent.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Recently Modified Files
These files have been modified since you last accessed them (file was just edited so you may need to re-read it before editing):
backend/main.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:06:09.124Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.55

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Part 1: Rewrite github_client.py with repo type detection and smart file selection | Completed |
| 2 | Part 2: Rewrite doc_generator.py with new section structure | Completed |
| 3 | Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring | Completed |
| 4 | Part 4: Update main.py to store metadata and pass raw files to Q&A | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me update the /analyze endpoint to store all the necessary data:

<apply_diff>
<path>backend/main.py</path>
<diff>
<<<<<<< SEARCH
    global _last_onboarding_doc, _last_repo_files
    
    # Clear watsonx cache for fresh analysis
    watsonx_client.clear_cache()
    
    try:
        # Log the start of repository analysis
        logger.info(f"Analyzing repository: {request.github_url}")
        
        # Fetch repository data from GitHub
        try:
            repo_data = await fetch_repo_data(request.github_url)
=======
    global last_onboarding_doc, last_repo_files, last_repo_metadata, last_repo_owner, last_repo_name
    
    # Clear watsonx cache for fresh analysis
    watsonx_client.clear_cache()
    
    try:
        # Log the start of repository analysis
        logger.info(f"Analyzing repository: {request.github_url}")
        
        # Fetch repository data from GitHub
        try:
            repo_data = await fetch_repo_data(request.github_url)
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'backend/main.py'] Result:
<file_write_result>
<path>backend/main.py</path>
<operation>modified</operation>
<problems>

New problems detected after saving the file:
backend/main.py
- [basedpyright Error] 350 |         if not _last_onboarding_doc: : "_last_onboarding_doc" is unbound
- [basedpyright Error] 357 |         result = answer_question(request.question, _last_onboarding_doc, _last_repo_files) : "_last_repo_files" is unbound</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
backend\main.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/watsonx_client.py,backend/github_client.py,backend/main.py,backend/doc_generator.py,backend/orchestrate_agent.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:06:17.582Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.75

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Part 1: Rewrite github_client.py with repo type detection and smart file selection | Completed |
| 2 | Part 2: Rewrite doc_generator.py with new section structure | Completed |
| 3 | Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring | Completed |
| 4 | Part 4: Update main.py to store metadata and pass raw files to Q&A | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me update the rest of the /analyze endpoint and the /ask endpoint in one go:

<apply_diff>
<path>backend/main.py</path>
<diff>
<<<<<<< SEARCH
        # Generate onboarding documentation
        try:
            # Pass the full repo_data dict to the doc generator
            onboarding_doc, metadata = generate_onboarding_doc(repo_data)
            
            # Validate generated documentation is not empty
            if not onboarding_doc or not onboarding_doc.strip():
                raise ValueError("Generated documentation is empty")
            
            # Store the generated documentation and raw files for use by /ask endpoint
            _last_onboarding_doc = onboarding_doc
            _last_repo_files = files
                
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
=======
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
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'backend/main.py'] Result:
<file_write_result>
<path>backend/main.py</path>
<operation>modified</operation>
<problems>

New problems detected after saving the file:
backend/main.py
- [basedpyright Error] 353 |         if not _last_onboarding_doc: : "_last_onboarding_doc" is unbound
- [basedpyright Error] 360 |         result = answer_question(request.question, _last_onboarding_doc, _last_repo_files) : "_last_repo_files" is unbound
- [basedpyright Error] 399 |     import uvicorn : Import "uvicorn" could not be resolved</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
backend\main.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/watsonx_client.py,backend/github_client.py,backend/main.py,backend/doc_generator.py,backend/orchestrate_agent.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
### New Output
 INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [14596]
WARNING:  WatchFiles detected changes in 'main.py', 'orchestrate_agent.py', 'doc_generator.py'. Reloading...


# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:06:32.245Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.96

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Part 1: Rewrite github_client.py with repo type detection and smart file selection | Completed |
| 2 | Part 2: Rewrite doc_generator.py with new section structure | Completed |
| 3 | Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring | Completed |
| 4 | Part 4: Update main.py to store metadata and pass raw files to Q&A | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me update the /ask endpoint to use the new variable names:

<apply_diff>
<path>backend/main.py</path>
<diff>
<<<<<<< SEARCH
    global _last_onboarding_doc, _last_repo_files
    
    try:
        logger.info(f"Processing question: {request.question[:100]}...")
        
        # Check if we have a stored onboarding document
        if not _last_onboarding_doc:
            raise HTTPException(
                status_code=400,
                detail="No repository has been analyzed yet. Please analyze a repository first using the /analyze endpoint."
            )
        
        # Call the orchestrate agent to answer the question using stored context and raw files
        result = answer_question(request.question, _last_onboarding_doc, _last_repo_files)
=======
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
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'backend/main.py'] Result:
<file_write_result>
<path>backend/main.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
backend\main.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/watsonx_client.py,backend/github_client.py,backend/main.py,backend/doc_generator.py,backend/orchestrate_agent.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
### New Output
 INFO:     Started server process [28312]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
ERROR:    Traceback (most recent call last):
  File "C:\Python312\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python312\Lib\asyncio\base_events.py", line 687, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
asyncio.exceptions.CancelledError

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Python312\Lib\asyncio\runners.py", line 194, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "C:\Python312\Lib\asyncio\runners.py", line 123, in run
    raise KeyboardInterrupt()
KeyboardInterrupt

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\ASUS\AppData\Roaming\Python\Python312\site-packages\starlette\routing.py", line 645, in lifespan
    await receive()
  File "C:\Users\ASUS\AppData\Roaming\Python\Python312\site-packages\uvicorn\lifespan\on.py", line 137, in receive
    return await self.receive_queue.get()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python312\Lib\asyncio\queues.py", line 158, in get
    await getter
asyncio.exceptions.CancelledError

INFO:     Started server process [38660]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
WARNING:  WatchFiles detected changes in 'main.py'. Reloading...


# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:06:41.589Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$2.16

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Part 1: Rewrite github_client.py with repo type detection and smart file selection | Completed |
| 2 | Part 2: Rewrite doc_generator.py with new section structure | Completed |
| 3 | Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring | Completed |
| 4 | Part 4: Update main.py to store metadata and pass raw files to Q&A | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Perfect! The server is restarting. Now let me update the TODO list and provide a completion summary:

<update_todo_list>
<todos>
[x] Part 1: Rewrite github_client.py with repo type detection and smart file selection
[x] Part 2: Rewrite doc_generator.py with new section structure
[x] Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring
[x] Part 4: Update main.py to store metadata and pass raw files to Q&A
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
backend\main.py

# VSCode Open Tabs
docs/IMPLEMENTATION_PLAN.md,docs/ARCHITECTURE_PLAN.md,README.md,docs/QUICK_START_GUIDE.md,docs/FILE_STRUCTURE_CHECKLIST.md,docs/PLANNING_SUMMARY.md,docs/EDGE_CASES_FIXED.md,backend/watsonx_client.py,backend/github_client.py,backend/main.py,backend/doc_generator.py,backend/orchestrate_agent.py,backend/test_watson.py,backend/requirements.txt,frontend/src/App.jsx,frontend/src/App.css,frontend/src/MarkdownRenderer.jsx,frontend/src/index.css,frontend/README.md

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `d:\devonboard`
### Original command: `cd backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-03T10:06:46.834Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$2.38

# Review Exclusions
The following file patterns are excluded from code reviews:
- .bobignore
- node_modules/
- __pycache__/
- .git/
- *.pyc
- dist/
- build/
- .env

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Part 1: Rewrite github_client.py with repo type detection and smart file selection | Completed |
| 2 | Part 2: Rewrite doc_generator.py with new section structure | Completed |
| 3 | Part 3: Rewrite orchestrate_agent.py with improved keyword extraction and scoring | Completed |
| 4 | Part 4: Update main.py to store metadata and pass raw files to Q&A | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<attempt_completion>
<result>
Complete end-to-end rewrite finished! All 4 parts implemented successfully:

## ✅ PART 1 - github_client.py
- Added `detect_repo_type()` to analyze file paths and detect: has_frontend, has_backend, has_database, has_auth, has_tests, language, framework
- Implemented smart file selection with 4 priorities:
  - Priority 1: Config files (README, package.json, requirements.txt, etc.)
  - Priority 2: Entry points (main.py, app.js, index.ts, etc.)
  - Priority 3: Category-based (auth files if has_auth, models if has_database, routes if has_backend, components if has_frontend)
  - Priority 4: Fill remaining slots up to 40 files from root/src/app/lib
- Each file now stores: path, content (up to 8000 chars), size, priority, category
- Returns repo_type detection results in response

## ✅ PART 2 - doc_generator.py
- Complete rewrite with 8 structured sections
- Extracts actual code content from files
- Sections include: Project Overview, File Structure, Key Files, Authentication (with code), API Routes (extracted from code), Data Models (extracted from code), Getting Started, How to Add Feature
- Uses helper functions to find files by pattern and extract content
- Returns metadata dict with: language, framework, has_auth, has_database, endpoint_count, model_count, total_files_analyzed, owner, repo

## ✅ PART 3 - orchestrate_agent.py
- Enhanced `extract_keywords()` with semantic expansions (auth→[authentication, login, jwt, token, etc.])
- New `score_and_rank_files()` scores files based on:
  - Priority level (5-priority points)
  - Keyword in path (+5)
  - Keyword in first 300 chars (+3)
  - Keyword in first 1000 chars (+2)
  - Keyword anywhere (+1)
  - Category boost for auth/route/database (+2)
- `extract_relevant_section()` finds hot lines with keywords and includes context
- Builds rich prompt with actual code sections (up to 4000 chars)
- Returns: answer, sources, keywords_matched, files_searched, files_matched, powered_by

## ✅ PART 4 - main.py
- Added module-level variables: last_onboarding_doc, last_repo_files, last_repo_metadata, last_repo_owner, last_repo_name
- /analyze endpoint now stores all data after generation
- /ask endpoint passes last_repo_files to answer_question() for code-based Q&A
- Returns full metadata in AnalyzeResponse

**Result:** Q&A answers will now be much more specific because they're based on actual extracted code content (up to 8000 chars per file, 6 most relevant files, with smart keyword matching and context extraction).
</result>
</attempt_completion>

