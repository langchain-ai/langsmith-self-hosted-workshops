from __future__ import annotations
import os
from typing import Optional
from ._shell import run
from ._validation import ok, warn

def aws_region() -> str:
    return os.environ.get("AWS_REGION", "").strip() or os.environ.get("AWS_DEFAULT_REGION", "").strip() or "us-west-2"

def sts_identity() -> dict:
    r = run(["aws", "sts", "get-caller-identity", "--output", "json"], check=True, stream=False)
    import json
    return json.loads(r.stdout)

def assert_account(expected_account_id: Optional[str]) -> None:
    if not expected_account_id:
        return
    ident = sts_identity()
    actual = ident.get("Account", "")
    if actual != expected_account_id:
        raise RuntimeError(f"❌ AWS account mismatch: expected {expected_account_id}, got {actual}")
    ok(f"AWS account guardrail matched: {actual}")

def eks_cluster_exists(cluster_name: str) -> bool:
    r = run(["aws", "eks", "describe-cluster", "--name", cluster_name, "--region", aws_region(), "--output", "json"],
            check=False, stream=False)
    if r.returncode == 0:
        return True
    if "ResourceNotFoundException" in r.stderr or "ResourceNotFoundException" in r.stdout:
        return False
    warn("EKS describe-cluster returned an unexpected error; treat as inconclusive.")
    return False

def configure_kubectl_eks(cluster_name: str, region: Optional[str] = None) -> None:
    """
    Configure kubectl to connect to an EKS cluster.
    
    Args:
        cluster_name: Name of the EKS cluster
        region: AWS region (optional, will be auto-detected if not provided)
    """
    if region is None:
        region = aws_region()
    
    run(["aws", "eks", "update-kubeconfig", "--name", cluster_name, "--region", region],
        check=True, stream=True)

def verify_s3_access() -> bool:
    """
    Verify access to S3.
    
    Returns:
        True if access is verified, False otherwise
    """
    try:
        result = run(["aws", "s3", "ls", "--output", "json"], check=False, stream=False)
        return result.returncode == 0
    except Exception:
        return False

def alb_target_health(load_balancer_arn: str) -> str:
    # Caller should provide ARN; this returns raw JSON for inspection.
    return run(["aws", "elbv2", "describe-target-health",
                "--target-group-arn", load_balancer_arn,
                "--region", aws_region(),
                "--output", "json"], check=False, stream=False).stdout
