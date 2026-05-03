"""
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
