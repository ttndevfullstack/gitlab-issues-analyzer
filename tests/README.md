# Test Suite for GitLab Issues Analyzer

This directory contains the complete test suite for the GitLab Issues Analyzer project.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (isolated, fast)
│   ├── test_config.py
│   ├── test_gitlab_client.py
│   ├── test_analyzer.py
│   ├── test_reporter.py
│   ├── test_email_sender.py
│   └── test_monitor.py
├── integration/             # Integration tests (component interactions)
│   ├── test_gitlab_integration.py
│   ├── test_analyzer_integration.py
│   └── test_email_integration.py
└── e2e/                     # End-to-end tests (full workflows)
    └── test_full_workflow.py
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# End-to-end tests only
pytest tests/e2e/
```

### Run Specific Test File

```bash
pytest tests/unit/test_config.py
```

### Run Specific Test

```bash
pytest tests/unit/test_config.py::TestConfigLoading::test_load_config_from_environment_variables
```

### Run Tests with Coverage

```bash
pytest --cov=src --cov-report=html --cov-report=term-missing
```

### Skip Slow Tests

```bash
pytest -m "not slow"
```

### Skip Tests Requiring Credentials

```bash
pytest -m "not requires_credentials"
```

## Test Markers

Tests are marked with categories:

- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.requires_credentials` - Tests that need real API credentials
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests

## Test Coverage

The test suite aims for 80%+ code coverage. Current test cases cover:

### Unit Tests
- ✅ Config module (7 test cases)
- ✅ GitLab Client module (11 test cases)
- ✅ Analyzer module (10 test cases)
- ✅ Reporter module (6 test cases)
- ✅ Email Sender module (7 test cases)
- ✅ Monitor module (9 test cases)

### Integration Tests
- ✅ GitLab API integration (3 test cases)
- ✅ Analyzer integration (2 test cases)
- ✅ Email integration (1 test case)

### End-to-End Tests
- ✅ Complete webhook workflow (1 test case)
- ✅ Complete polling workflow (1 test case)
- ✅ Error handling workflow (1 test case)

## Writing New Tests

When adding new tests:

1. Follow the naming convention: `test_<function_name>_<scenario>_<expected_result>()`
2. Use fixtures from `conftest.py` when possible
3. Mock external dependencies (APIs, file system, network)
4. Add appropriate markers (`@pytest.mark.slow`, etc.)
5. Include docstrings describing what is being tested
6. Reference test case IDs from `TEST_CASES.md` in docstrings

## Test Fixtures

Common fixtures available in `conftest.py`:

- `sample_issue_data` - Sample GitLab issue data
- `sample_comprehensive_issue_data` - Issue data with comments, related issues, attachments
- `sample_analysis` - Sample WWWH-TR analysis
- `sample_webhook_payload` - Sample GitLab webhook payload
- `sample_config` - Sample configuration dictionary
- `sample_smtp_config` - Sample SMTP configuration
- `mock_gitlab_response` - Mock GitLab API response
- `mock_ai_response` - Mock AI API response
- `mock_smtp_server` - Mock SMTP server

## Continuous Integration

Tests should be run in CI/CD pipelines:

1. Run all unit tests on every commit
2. Run integration tests on pull requests
3. Run E2E tests on main branch only
4. Generate coverage reports
5. Fail build if coverage drops below threshold

## Notes

- Unit tests use mocks for all external dependencies
- Integration tests use mocked HTTP responses
- E2E tests may require test credentials (marked with `@pytest.mark.requires_credentials`)
- Some tests are marked as `@pytest.mark.slow` and can be skipped during development

For more details, see [TEST_CASES.md](../docs/TEST_CASES.md).

