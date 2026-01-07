"""
Pytest configuration and fixtures for notebook testing.
"""
import os
import sys
from pathlib import Path

# Add notebooks directory to path
repo_root = Path(__file__).parent.parent
notebooks_dir = repo_root / "notebooks"
if str(notebooks_dir) not in sys.path:
    sys.path.insert(0, str(notebooks_dir))

# Set test environment variables
os.environ.setdefault("NAMESPACE", "langsmith-test")
os.environ.setdefault("CLUSTER_NAME", "test-cluster")
os.environ.setdefault("HELM_RELEASE", "langsmith")
os.environ.setdefault("ARTIFACTS_DIR", str(repo_root / "tests" / "artifacts"))

# Cloud provider defaults (can be overridden by GitHub Actions)
os.environ.setdefault("CLOUD_PROVIDER", "aws")
os.environ.setdefault("AWS_REGION", "us-west-2")
os.environ.setdefault("AZURE_LOCATION", "eastus")

# Create artifacts directory
artifacts_dir = Path(os.environ["ARTIFACTS_DIR"])
artifacts_dir.mkdir(parents=True, exist_ok=True)

