from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

# Install required packages if not available
def _ensure_packages():
    """Ensure required Python packages are installed."""
    required_packages = [
        "python-dotenv",  # For loading .env files
        "pyyaml",  # For parsing YAML files (Chart.yaml, etc.)
        "requests",  # For HTTP requests (UI validation)
    ]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *required_packages])

_ensure_packages()

from dotenv import load_dotenv
from ._shell import run
from ._validation import ok, warn, fail
from ._aws_helpers import aws_region, sts_identity

def load_env(env_file: Optional[str] = None) -> None:
    """
    Load environment variables from a .env file.
    If env_file is not provided, looks for .env or workshop.env in the notebooks directory.
    
    Raises RuntimeError if neither env file is found.
    """
    if env_file is None:
        # Look for .env file in notebooks root, with fallback to workshop.env
        notebooks_dir = Path(__file__).parent.parent
        # Try .env first (standard), then workshop.env (Jupyter-friendly)
        env_file = notebooks_dir / ".env"
        if not env_file.exists():
            env_file = notebooks_dir / "workshop.env"
    
    env_path = Path(env_file).expanduser().resolve()
    
    if not env_path.exists():
        # Calculate relative path from repo root for cleaner display
        repo_root = Path(__file__).parent.parent.parent
        notebooks_dir = Path(__file__).parent.parent
        
        # Show both options in the error message
        try:
            notebooks_dir_display = notebooks_dir.relative_to(repo_root)
        except ValueError:
            notebooks_dir_display = Path("notebooks")
        
        print(f"""❌ Environment file not found
💡 To fix this, create one of these files:
   Option 1 (via terminal): {notebooks_dir_display}/.env
   Option 2 (via Jupyter): {notebooks_dir_display}/workshop.env

   Copy a template:
   cp env-samples/workshop.env.example {notebooks_dir_display}/.env
   # OR
   cp env-samples/workshop.env.example {notebooks_dir_display}/workshop.env

   Then edit the file and fill in your configuration values.
""")
        raise RuntimeError(f"Missing environment file. Expected {notebooks_dir_display}/.env or {notebooks_dir_display}/workshop.env")
    
    load_dotenv(env_path, override=False)  # Don't override existing env vars
    ok(f"Loaded environment variables from {env_path.name}")

def check_required_tools() -> None:
    """
    Check that all required tools are available:
    - aws cli
    - terraform
    - helm
    - kubectl
    - jq
    """
    print("### Checking required tools...")
    tools = [
        ("aws", ["aws", "--version"]),
        ("terraform", ["terraform", "version"]),
        ("helm", ["helm", "version"]),
        ("kubectl", ["kubectl", "version", "--client"]),
        ("jq", ["jq", "--version"]),
    ]
    
    missing = []
    for tool_name, version_cmd in tools:
        try:
            result = run(version_cmd, check=False, stream=False)
            if result.returncode == 0:
                ok(f"{tool_name} is available")
            else:
                missing.append(tool_name)
                warn(f"{tool_name} check failed (rc={result.returncode})")
        except FileNotFoundError:
            missing.append(tool_name)
            fail(f"{tool_name} not found in PATH")
        except Exception as e:
            missing.append(tool_name)
            warn(f"Error checking {tool_name}: {e}")
    
    if missing:
        fail(f"Missing required tools: {', '.join(missing)}")
    
    ok("All required tools are available")

def print_aws_info() -> None:
    """
    Print AWS identity and region information.
    """
    print("### AWS Configuration")
    try:
        region = aws_region()
        print(f"Region: {region}")
        
        identity = sts_identity()
        account_id = identity.get("Account", "unknown")
        user_arn = identity.get("Arn", "unknown")
        user_id = identity.get("UserId", "unknown")
        
        print(f"Account ID: {account_id}")
        print(f"User ARN: {user_arn}")
        print(f"User ID: {user_id}")
        ok("AWS credentials are valid")
    except Exception as e:
        fail(f"Failed to get AWS identity: {e}")

def setup_artifacts_dir(artifacts_dir: Optional[str] = None) -> Path:
    """
    Create the ARTIFACTS_DIR directory if it doesn't exist.
    Returns the Path to the artifacts directory.
    """
    if artifacts_dir is None:
        artifacts_dir = os.environ.get("ARTIFACTS_DIR", "./artifacts")
    
    artifacts_path = Path(artifacts_dir).expanduser().resolve()
    artifacts_path.mkdir(parents=True, exist_ok=True)
    ok(f"Artifacts directory ready: {artifacts_path}")
    
    # Set it in environment for other notebooks
    os.environ["ARTIFACTS_DIR"] = str(artifacts_path)
    
    return artifacts_path

def bootstrap(env_file: Optional[str] = None, artifacts_dir: Optional[str] = None) -> dict:
    """
    Main bootstrap function that:
    1. Loads environment variables from .env file
    2. Checks that required tools exist
    3. Prints AWS identity and region
    4. Creates ARTIFACTS_DIR
    
    Returns a dict with bootstrap information.
    """
    print("=" * 60)
    print("Bootstrapping workshop environment...")
    print("=" * 60)
    
    # Load environment variables
    load_env(env_file)
    
    # Check required tools
    check_required_tools()
    
    # Print AWS info
    print_aws_info()
    
    # Setup artifacts directory
    artifacts_path = setup_artifacts_dir(artifacts_dir)
    
    print("=" * 60)
    ok("Bootstrap complete!")
    print("=" * 60)
    
    return {
        "artifacts_dir": str(artifacts_path),
        "aws_region": aws_region(),
        "aws_identity": sts_identity(),
    }

