# Backend Tests

This directory contains comprehensive unit tests for the DevOnboard backend modules.

**Total: 62 tests across all modules** ✅

## Test Files

- `test_doc_generator.py` - 31 tests for document generation functionality
- `test_github_client.py` - 31 tests for GitHub API client with mocked responses

All tests were generated using **IBM Bob** in Code mode.

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

### doc_generator.py tests (31 tests) ✅
- ✅ `normalize_path()` - Path normalization with edge cases
- ✅ `safe_get_content()` - Safe content extraction with error handling
- ✅ `extract_project_overview()` - Project overview generation
- ✅ `identify_key_files()` - Key file identification with scoring algorithm
- ✅ `analyze_folder_structure()` - Folder structure analysis
- ✅ `generate_feature_guide()` - Feature guide generation
- ✅ `generate_onboarding_doc()` - Main markdown generation (validates output structure)

### github_client.py tests (31 tests) ✅
- ✅ `parse_github_url()` - URL parsing with comprehensive error handling
- ✅ `should_skip_file()` - Binary file filtering (images, PDFs, etc.)
- ✅ `fetch_repo_tree()` - Repository tree fetching (fully mocked)
- ✅ `fetch_file_content()` - File content fetching (fully mocked)
- ✅ `fetch_repo_contents()` - Main integration function (fully mocked)

## Key Test Features

1. **Fully Mocked GitHub API calls** - No real API requests, no rate limits
2. **Comprehensive Error handling** - Invalid URLs, rate limits, timeouts, network errors
3. **Binary file filtering** - Ensures binary files (.png, .jpg, .pdf, etc.) are excluded
4. **Markdown validation** - Verifies valid markdown output structure
5. **Edge case coverage** - Empty inputs, None values, malformed data, special characters
6. **Fast execution** - All 62 tests run in seconds
7. **No external dependencies** - Tests run offline

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

**All 62 tests pass successfully** ✅

```
tests/test_doc_generator.py::TestNormalizePath ✅ (5 tests)
tests/test_doc_generator.py::TestSafeGetContent ✅ (5 tests)
tests/test_doc_generator.py::TestExtractProjectOverview ✅ (5 tests)
tests/test_doc_generator.py::TestIdentifyKeyFiles ✅ (6 tests)
tests/test_doc_generator.py::TestAnalyzeFolderStructure ✅ (5 tests)
tests/test_doc_generator.py::TestGenerateFeatureGuide ✅ (5 tests)

tests/test_github_client.py::TestParseGithubUrl ✅ (10 tests)
tests/test_github_client.py::TestShouldSkipFile ✅ (6 tests)
tests/test_github_client.py::TestFetchRepoTree ✅ (5 tests)
tests/test_github_client.py::TestFetchFileContent ✅ (5 tests)
tests/test_github_client.py::TestFetchRepoContents ✅ (5 tests)
```

## Built with IBM Bob

All tests were generated using IBM Bob:
- Test structure planned in Plan mode
- Test code generated in Code mode
- Edge cases identified and tested by Bob
- Documentation written by Bob

## Why Testing Matters

These comprehensive tests ensure:
- **Reliability**: Code works as expected
- **Maintainability**: Changes don't break existing functionality
- **Confidence**: Deploy with confidence
- **Documentation**: Tests serve as usage examples
- **Quality**: High code quality standards

## Running Specific Test Categories

```bash
# Run only doc_generator tests
pytest tests/test_doc_generator.py -v

# Run only github_client tests
pytest tests/test_github_client.py -v

# Run tests with coverage report
pytest tests/ --cov=. --cov-report=html

# Run tests in parallel (faster)
pytest tests/ -n auto
```