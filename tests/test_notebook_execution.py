"""
Test notebook execution using nbconvert.

This module executes notebooks and validates they complete without errors.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

# Repository root
REPO_ROOT = Path(__file__).parent.parent
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"


def execute_notebook(notebook_path: Path, timeout: int = 600) -> tuple[bool, str]:
    """
    Execute a Jupyter notebook using nbconvert.
    
    Args:
        notebook_path: Path to the notebook file
        timeout: Maximum execution time in seconds
        
    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        # Use nbconvert to execute the notebook
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                "--inplace",
                "--ExecutePreprocessor.timeout=600",
                "--ExecutePreprocessor.kernel_name=python3",
                str(notebook_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(notebook_path.parent),
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            error_msg = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        return False, f"Notebook execution timed out after {timeout} seconds"
    except Exception as e:
        return False, f"Error executing notebook: {str(e)}"


def get_notebook_cells(notebook_path: Path) -> list:
    """Get all code cells from a notebook."""
    with open(notebook_path, "r") as f:
        nb = json.load(f)
    return [cell for cell in nb.get("cells", []) if cell.get("cell_type") == "code"]


class TestNotebookExecution:
    """Base class for notebook execution tests."""
    
    @pytest.fixture(autouse=True)
    def setup_test_env(self, monkeypatch):
        """Set up test environment variables."""
        # Set minimal required env vars for testing
        test_env = {
            "NAMESPACE": "langsmith-test",
            "CLUSTER_NAME": "test-cluster",
            "HELM_RELEASE": "langsmith",
            "ARTIFACTS_DIR": str(REPO_ROOT / "tests" / "artifacts"),
            "CLOUD_PROVIDER": os.environ.get("CLOUD_PROVIDER", "aws"),
            "AWS_REGION": os.environ.get("AWS_REGION", "us-west-2"),
            "AZURE_LOCATION": os.environ.get("AZURE_LOCATION", "eastus"),
            # Mock values for testing (will fail actual operations but allow syntax checks)
            "LANGSMITH_DOMAIN": "test.langsmith.example.com",
            "OIDC_ISSUER": "https://test-idp.example.com/oauth2/default",
            "OIDC_CLIENT_ID": "test-client-id",
            "OIDC_CLIENT_SECRET": "test-client-secret",
            "OIDC_REDIRECT_URI": "https://test.langsmith.example.com/auth/callback",
        }
        
        for key, value in test_env.items():
            monkeypatch.setenv(key, value)
    
    def _validate_notebook_syntax(self, notebook_path: Path):
        """Helper method to validate notebook has valid JSON structure and code cells."""
        assert notebook_path.exists(), f"Notebook not found: {notebook_path}"
        
        with open(notebook_path, "r") as f:
            nb = json.load(f)
        
        assert "cells" in nb, "Notebook missing cells"
        assert len(nb["cells"]) > 0, "Notebook has no cells"
        
        code_cells = [c for c in nb["cells"] if c.get("cell_type") == "code"]
        assert len(code_cells) > 0, "Notebook has no code cells"


# Module 1 tests
class TestModule1Notebooks(TestNotebookExecution):
    """Test Module 1 notebooks."""
    
    @pytest.mark.parametrize("notebook", [
        "01_preflight.ipynb",
        "99_teardown.ipynb",  # Always test syntax, even if execution is skipped
        # Note: Skip terraform/helm/validation notebooks in CI as they require actual infrastructure
        # "02_terraform_apply.ipynb",
        # "03_helm_install_langsmith.ipynb",
        # "04_validate_ingress_and_ui.ipynb",
    ])
    def test_module1_notebook_syntax(self, notebook):
        """Test Module 1 notebook syntax."""
        notebook_path = NOTEBOOKS_DIR / "module-1" / notebook
        self._validate_notebook_syntax(notebook_path)
    
    @pytest.mark.skipif(
        os.environ.get("CI_SKIP_EXECUTION") == "true",
        reason="Skipping execution in CI (requires infrastructure)"
    )
    @pytest.mark.parametrize("notebook", [
        "01_preflight.ipynb",
    ])
    def test_module1_notebook_execution(self, notebook):
        """Test Module 1 notebook execution (only if infrastructure available)."""
        notebook_path = NOTEBOOKS_DIR / "module-1" / notebook
        success, output = execute_notebook(notebook_path, timeout=300)
        assert success, f"Notebook execution failed:\n{output}"
    
    @pytest.mark.skipif(
        os.environ.get("CI_SKIP_EXECUTION") == "true",
        reason="Skipping execution in CI (requires infrastructure)"
    )
    def test_module1_teardown_execution(self):
        """
        Test Module 1 teardown notebook execution.
        
        This test runs when CI_SKIP_EXECUTION is not true, ensuring that
        resources created during execution tests are properly cleaned up.
        
        IMPORTANT: This test should run AFTER other execution tests to ensure
        proper cleanup. It will destroy all infrastructure created during testing.
        
        Note: The teardown notebook has commented-out code sections that must be
        uncommented to actually destroy resources. This test validates the notebook
        structure and execution flow, but actual resource destruction requires
        manual uncommenting in the notebook itself.
        """
        notebook_path = NOTEBOOKS_DIR / "module-1" / "99_teardown.ipynb"
        # Teardown may take longer, especially for Terraform destroy
        # Using 30 minutes timeout to allow for full infrastructure teardown
        success, output = execute_notebook(notebook_path, timeout=1800)  # 30 minutes
        assert success, f"Teardown notebook execution failed:\n{output}"


# Module 2 tests
class TestModule2Notebooks(TestNotebookExecution):
    """Test Module 2 notebooks."""
    
    @pytest.mark.parametrize("notebook", [
        "01_sso_oidc_validation.ipynb",
        "02_sso_saml_validation.ipynb",
    ])
    def test_module2_notebook_syntax(self, notebook):
        """Test Module 2 notebook syntax."""
        notebook_path = NOTEBOOKS_DIR / "module-2" / notebook
        self._validate_notebook_syntax(notebook_path)
    
    @pytest.mark.skipif(
        os.environ.get("CI_SKIP_EXECUTION") == "true",
        reason="Skipping execution in CI (requires infrastructure)"
    )
    @pytest.mark.parametrize("notebook", [
        "01_sso_oidc_validation.ipynb",
        "02_sso_saml_validation.ipynb",
    ])
    def test_module2_notebook_execution(self, notebook):
        """Test Module 2 notebook execution (only if infrastructure available)."""
        notebook_path = NOTEBOOKS_DIR / "module-2" / notebook
        success, output = execute_notebook(notebook_path, timeout=300)
        assert success, f"Notebook execution failed:\n{output}"


# Module 3 tests
class TestModule3Notebooks(TestNotebookExecution):
    """Test Module 3 notebooks."""
    
    @pytest.mark.parametrize("notebook", [
        "01_ops_sanity_checks.ipynb",
    ])
    def test_module3_notebook_syntax(self, notebook):
        """Test Module 3 notebook syntax."""
        notebook_path = NOTEBOOKS_DIR / "module-3" / notebook
        self._validate_notebook_syntax(notebook_path)
    
    @pytest.mark.skipif(
        os.environ.get("CI_SKIP_EXECUTION") == "true",
        reason="Skipping execution in CI (requires infrastructure)"
    )
    @pytest.mark.parametrize("notebook", [
        "01_ops_sanity_checks.ipynb",
    ])
    def test_module3_notebook_execution(self, notebook):
        """Test Module 3 notebook execution (only if infrastructure available)."""
        notebook_path = NOTEBOOKS_DIR / "module-3" / notebook
        # Ops sanity checks may take longer due to resource usage checks
        success, output = execute_notebook(notebook_path, timeout=600)
        assert success, f"Notebook execution failed:\n{output}"


# Module 4 tests
class TestModule4Notebooks(TestNotebookExecution):
    """Test Module 4 notebooks."""
    
    @pytest.mark.parametrize("notebook", [
        "00_setup_or_resume_environment.ipynb",
        "01_diagnostics_baseline.ipynb",
        "10_failure_lab_postgres.ipynb",
        "20_failure_lab_redis.ipynb",
        "30_failure_lab_clickhouse.ipynb",
        "40_failure_lab_blob_storage.ipynb",
    ])
    def test_module4_notebook_syntax(self, notebook):
        """Test Module 4 notebook syntax."""
        notebook_path = NOTEBOOKS_DIR / "module-4" / notebook
        self._validate_notebook_syntax(notebook_path)
    
    @pytest.mark.skipif(
        os.environ.get("CI_SKIP_EXECUTION") == "true",
        reason="Skipping execution in CI (requires infrastructure)"
    )
    @pytest.mark.parametrize("notebook", [
        "00_setup_or_resume_environment.ipynb",
        "01_diagnostics_baseline.ipynb",
    ])
    def test_module4_notebook_execution(self, notebook):
        """
        Test Module 4 notebook execution (only if infrastructure available).
        
        Tests setup and baseline notebooks which are read-only validation.
        Failure labs are syntax-tested only to avoid modifying production environments.
        """
        notebook_path = NOTEBOOKS_DIR / "module-4" / notebook
        # Setup and baseline checks may take longer due to diagnostics collection
        success, output = execute_notebook(notebook_path, timeout=600)
        assert success, f"Notebook execution failed:\n{output}"
    
    @pytest.mark.skipif(
        os.environ.get("CI_SKIP_EXECUTION") == "true",
        reason="Skipping execution in CI (requires infrastructure and failure injection)"
    )
    @pytest.mark.parametrize("notebook", [
        "10_failure_lab_postgres.ipynb",
        "20_failure_lab_redis.ipynb",
        "30_failure_lab_clickhouse.ipynb",
        "40_failure_lab_blob_storage.ipynb",
    ])
    def test_module4_failure_lab_execution(self, notebook):
        """
        Test Module 4 failure lab notebook execution (only if infrastructure available).
        
        WARNING: These notebooks inject failures by modifying secrets and configurations.
        They should only be run in test environments, not production.
        
        These tests validate that failure injection and remediation workflows function
        correctly. The notebooks include safety mechanisms (commented-out injection code)
        but should still be used with caution.
        """
        notebook_path = NOTEBOOKS_DIR / "module-4" / notebook
        # Failure labs may take longer due to failure injection, observation, and remediation
        success, output = execute_notebook(notebook_path, timeout=900)  # 15 minutes
        assert success, f"Notebook execution failed:\n{output}"

