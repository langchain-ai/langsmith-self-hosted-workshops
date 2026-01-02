# GitHub Actions Workflows

This directory contains CI/CD workflows for the LangSmith Self-Hosted Workshops repository.

## Workflows

### `test-notebooks.yml`

Main workflow for testing notebook syntax and execution.

**Triggers:**
- Pull requests to `main`/`master`
- Pushes to `main`/`master`
- Manual workflow dispatch

**Jobs:**
1. **test-notebook-syntax**: Validates notebook JSON structure
2. **test-module-1-preflight**: Tests Module 1 preflight notebook
3. **test-module-2-syntax**: Tests Module 2 auth validation notebooks
4. **lint-python**: Lints Python code in shared modules

## Environment Variables

### Required for Syntax Tests (Always Available)

These are set in the workflow and don't require secrets:

```yaml
NAMESPACE: "langsmith-test"
CLUSTER_NAME: "test-cluster"
HELM_RELEASE: "langsmith"
CLOUD_PROVIDER: "aws"
AWS_REGION: "us-west-2"
LANGSMITH_DOMAIN: "test.langsmith.example.com"
```

### Required for Full Execution Tests (Optional)

For full notebook execution, set these in GitHub Secrets:

**AWS:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `AWS_ACCOUNT_ID` (optional, for validation)

**Azure:**
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_LOCATION`

**Infrastructure:**
- `CLUSTER_NAME`
- `NAMESPACE`
- `TERRAFORM_REPO_DIR`
- `HELM_REPO_DIR`

**OIDC/SAML (Module 2):**
- `OIDC_ISSUER`
- `OIDC_CLIENT_ID`
- `OIDC_CLIENT_SECRET`
- `OIDC_REDIRECT_URI`
- `SAML_METADATA_URL` (if using SAML)

## Customizing Workflows

### Adding New Test Jobs

1. Add job to `test-notebooks.yml`
2. Set appropriate `needs:` dependencies
3. Configure environment variables
4. Add artifact uploads if needed

### Enabling Full Execution Tests

To enable full notebook execution in CI:

1. Set required secrets in GitHub repository settings
2. Remove or modify `CI_SKIP_EXECUTION` environment variable
3. Update test conditions in `test_notebook_execution.py`

### Adding New Modules

When adding Module 3, 4, etc.:

1. Create new test class in `test_notebook_execution.py`
2. Add parametrized tests for new notebooks
3. Add new job in GitHub Actions workflow
4. Update this README

## Workflow Status

Workflow status badges can be added to README:

```markdown
![Test Notebooks](https://github.com/your-org/langsmith-self-hosted-workshops/workflows/Test%20Notebooks/badge.svg)
```

## Troubleshooting

### Workflow Fails on Syntax Tests

- Check notebook JSON is valid
- Verify all imports are available
- Check Python version compatibility

### Workflow Times Out

- Increase `timeout-minutes` in job definition
- Check for long-running operations
- Consider splitting into smaller jobs

### Environment Variable Issues

- Verify secrets are set in repository settings
- Check variable names match exactly
- Ensure secrets are accessible to workflow

