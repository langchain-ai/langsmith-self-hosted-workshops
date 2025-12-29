"""
Azure-specific helper functions.

These functions provide Azure CLI-based implementations of cloud operations.
"""
from __future__ import annotations
import os
import json
from typing import Optional
from ._shell import run
from ._validation import ok, warn

def azure_location() -> str:
    """
    Get the Azure location (region).
    
    Returns:
        Azure location string (e.g., 'eastus', 'westus2')
    """
    location = os.environ.get("AZURE_LOCATION", "").strip()
    if location:
        return location
    
    # Try to get from current subscription context
    try:
        result = run(["az", "account", "show", "--query", "location", "--output", "tsv"], 
                     check=False, stream=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    
    # Default location
    return "eastus"

def azure_identity() -> dict:
    """
    Get Azure account/subscription identity information.
    
    Returns:
        Dictionary with subscription and account information
    """
    result = run(["az", "account", "show", "--output", "json"], check=True, stream=False)
    account_info = json.loads(result.stdout)
    
    # Normalize to similar structure as AWS
    return {
        "SubscriptionId": account_info.get("id", ""),
        "SubscriptionName": account_info.get("name", ""),
        "TenantId": account_info.get("tenantId", ""),
        "User": account_info.get("user", {}).get("name", ""),
        # For compatibility with AWS-style identity checks
        "Account": account_info.get("id", ""),  # Subscription ID
        "Arn": f"azure://{account_info.get('id', '')}",  # Pseudo-ARN
        "UserId": account_info.get("user", {}).get("name", ""),
    }

def assert_subscription(expected_subscription_id: Optional[str]) -> None:
    """
    Assert that the current Azure subscription matches the expected value.
    
    Args:
        expected_subscription_id: Expected subscription ID
    """
    if not expected_subscription_id:
        return
    
    identity = azure_identity()
    actual = identity.get("SubscriptionId", "") or identity.get("Account", "")
    
    if actual != expected_subscription_id:
        raise RuntimeError(f"❌ Azure subscription mismatch: expected {expected_subscription_id}, got {actual}")
    ok(f"Azure subscription guardrail matched: {actual}")

def aks_cluster_exists(cluster_name: str) -> bool:
    """
    Check if an AKS cluster exists.
    
    Args:
        cluster_name: Name of the AKS cluster
        
    Returns:
        True if cluster exists, False otherwise
    """
    location = azure_location()
    resource_group = os.environ.get("AZURE_RESOURCE_GROUP", "")
    
    # Try to get resource group from cluster name pattern or environment
    if not resource_group:
        # Common pattern: resource group might be same as cluster name or have a prefix
        # We'll try a few common patterns, but ideally this should be set in env
        resource_group = os.environ.get("CLUSTER_NAME", cluster_name)
    
    try:
        cmd = ["az", "aks", "show", "--name", cluster_name, "--output", "json"]
        if resource_group:
            cmd.extend(["--resource-group", resource_group])
        else:
            # Try without resource group (will search all resource groups)
            cmd.append("--query")
            cmd.append("name")
        
        result = run(cmd, check=False, stream=False)
        
        if result.returncode == 0:
            return True
        
        # Check for "not found" error
        if "NotFound" in result.stderr or "not found" in result.stderr.lower():
            return False
        
        warn("AKS show returned an unexpected error; treat as inconclusive.")
        return False
    except Exception as e:
        warn(f"Error checking AKS cluster existence: {e}")
        return False

def configure_kubectl_aks(cluster_name: str, location: Optional[str] = None) -> None:
    """
    Configure kubectl to connect to an AKS cluster.
    
    Args:
        cluster_name: Name of the AKS cluster
        location: Azure location (optional, will be auto-detected if not provided)
    """
    if location is None:
        location = azure_location()
    
    resource_group = os.environ.get("AZURE_RESOURCE_GROUP", "")
    if not resource_group:
        # Try to infer from cluster name or use a default
        resource_group = os.environ.get("CLUSTER_NAME", cluster_name)
        warn(f"AZURE_RESOURCE_GROUP not set, using '{resource_group}'. Set it explicitly for reliability.")
    
    cmd = ["az", "aks", "get-credentials", "--name", cluster_name, "--resource-group", resource_group]
    if location:
        # Location is not required for get-credentials, but we can use it for validation
        pass
    
    run(cmd, check=True, stream=True)

def verify_blob_storage_access() -> bool:
    """
    Verify access to Azure Blob Storage.
    
    Returns:
        True if access is verified, False otherwise
    """
    try:
        # List storage accounts to verify access
        result = run(["az", "storage", "account", "list", "--output", "json"], 
                     check=False, stream=False)
        
        if result.returncode == 0:
            accounts = json.loads(result.stdout)
            return True
        
        return False
    except Exception as e:
        warn(f"Error verifying Azure Blob Storage access: {e}")
        return False

def get_storage_accounts() -> list:
    """
    Get list of Azure Storage Accounts.
    
    Returns:
        List of storage account dictionaries
    """
    try:
        result = run(["az", "storage", "account", "list", "--output", "json"], 
                     check=True, stream=False)
        return json.loads(result.stdout)
    except Exception as e:
        warn(f"Error listing storage accounts: {e}")
        return []

