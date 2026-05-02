# Backend Tests

This directory contains unit tests for the backend modules.

## Test Files

- `test_doc_generator.py` - Tests for document generation functionality
- `test_github_client.py` - Tests for GitHub API client with mocked responses

## Running Tests

### Run all tests
```bash
cd backend
pytest tests/
```

### Run with verbose output
```bash
cd backend
pytest tests/ -v
```

### Run specific test file
```bash
cd backend
pytest tests/test_doc_generator.py -v
pytest tests/test_github_client.py -v
```

### Run specific test class or function
```bash
cd backend
pytest tests/test_doc_generator.py::TestGenerateOnboardingDoc -v
pytest tests/test_github_client.py::TestParseGithubUrl::test_https_url -v
```

## Test Coverage

### doc_generator.py tests (31 tests)
- ✅ `normalize_path()` - Path normalization
- ✅ `safe_get_content()` - Safe content extraction
- ✅ `extract_project_overview()` - Project overview generation
- ✅ `identify_key_files()` - Key file identification
- ✅ `analyze_folder_structure()` - Folder structure analysis
- ✅ `generate_feature_guide()` - Feature guide generation
- ✅ `generate_onboarding_doc()` - Main markdown generation (validates output)

### github_client.py tests (31 tests)
- ✅ `parse_github_url()` - URL parsing with error handling
- ✅ `should_skip_file()` - Binary file filtering
- ✅ `fetch_repo_tree()` - Repository tree fetching (mocked)
- ✅ `fetch_file_content()` - File content fetching (mocked)
- ✅ `fetch_repo_contents()` - Main integration function (mocked)

## Key Test Features

1. **Mocked GitHub API calls** - No real API requests are made
2. **Error handling tests** - Invalid URLs, rate limits, timeouts
3. **Binary file filtering** - Ensures binary files are excluded
4. **Markdown validation** - Verifies valid markdown output
5. **Edge case coverage** - Empty inputs, None values, malformed data

## Dependencies

Tests require:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-mock` - Mocking utilities

Install with:
```bash
pip install -r requirements.txt
```

## Test Results

All 62 tests pass successfully:
- 31 tests for `doc_generator.py`
- 31 tests for `github_client.py`