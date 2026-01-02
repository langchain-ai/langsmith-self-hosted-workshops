# Tests for LangSmith Self-Hosted Workshops

This directory contains tests for validating notebook execution and syntax.

## Test Structure

- `conftest.py`: Pytest configuration and fixtures
- `test_notebook_execution.py`: Notebook execution tests
- `requirements.txt`: Test dependencies
- `artifacts/`: Directory for test artifacts (created automatically)

## Running Tests Locally

### Prerequisites

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Install system dependencies (if needed)
# macOS: brew install jq
# Ubuntu: sudo apt-get install jq
```

### Run All Tests

```bash
# Run syntax tests only (fast, no infrastructure required)
CI_SKIP_EXECUTION=true pytest tests/ -v

# Run full execution tests (requires infrastructure)
pytest tests/ -v
```

### Run Specific Test Suites

```bash
# Test Module 1 notebooks
pytest tests/test_notebook_execution.py::TestModule1Notebooks -v

# Test Module 2 notebooks
pytest tests/test_notebook_execution.py::TestModule2Notebooks -v
```

### Run Individual Notebook Tests

```bash
# Test specific notebook syntax
pytest tests/test_notebook_execution.py::TestModule1Notebooks::test_module1_notebook_syntax -v
```

## CI/CD Integration

Tests run automatically on:
- Pull requests to `main`/`master`
- Pushes to `main`/`master`
- Manual workflow dispatch

### GitHub Actions Workflow

The `.github/workflows/test-notebooks.yml` workflow:

1. **Test Notebook Syntax**: Validates JSON structure and code cells
2. **Test Module 1 Preflight**: Validates preflight notebook structure
3. **Test Module 2 Syntax**: Validates auth validation notebooks
4. **Lint Python Code**: Runs flake8 and black checks

### Environment Variables

The workflow uses test environment variables. For full execution tests, set:

```yaml
# In GitHub Actions secrets/variables
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
CLUSTER_NAME
NAMESPACE
# ... etc
```

## Test Strategy

### Syntax Tests (Always Run)

- Validate notebook JSON structure
- Check for code cells
- Verify imports can be resolved
- No infrastructure required

### Execution Tests (Conditional)

- Full notebook execution
- Requires actual infrastructure (cluster, IdP, etc.)
- Skipped in CI by default (`CI_SKIP_EXECUTION=true`)
- Can be enabled for integration testing environments

## Adding New Tests

1. Add notebook to appropriate test class in `test_notebook_execution.py`
2. Update `pytest.parametrize` decorator with notebook name
3. Add any required environment variables to `conftest.py`
4. Update GitHub Actions workflow if needed

## Troubleshooting

### Import Errors

If tests fail with import errors:
- Ensure `notebooks/shared/` is in Python path
- Check that `conftest.py` is setting up paths correctly
- Verify all required packages are in `requirements.txt`

### Timeout Errors

If notebook execution times out:
- Increase timeout in `execute_notebook()` function
- Check for infinite loops or long-running operations
- Consider mocking external API calls

### Environment Variable Issues

If tests fail due to missing env vars:
- Check `conftest.py` for default values
- Verify GitHub Actions workflow sets required variables
- Add variables to test fixtures if needed

