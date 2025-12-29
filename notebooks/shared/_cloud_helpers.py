"""
Cloud-agnostic helper functions that route to cloud-specific implementations.

This module provides a unified interface for cloud operations, automatically
detecting the cloud provider and routing to the appropriate implementation.
"""
from __future__ import annotations
import os
from typing import Optional, Literal

# Lazy imports to avoid circular dependencies
_aws_helpers = None
_azure_helpers = None

CloudProvider = Literal["aws", "azure", "gcp"]

def get_cloud_provider() -> CloudProvider:
    """
    Detect the cloud provider from environment variables or tooling.
    
    Checks in order:
    1. CLOUD_PROVIDER environment variable
    2. Presence of AWS_REGION or AWS credentials
    3. Presence of AZURE_LOCATION or Azure credentials
    4. Defaults to 'aws' for backward compatibility
    """
    # Explicit cloud provider setting takes precedence
    explicit = os.environ.get("CLOUD_PROVIDER", "").strip().lower()
    if explicit in ("aws", "azure", "gcp"):
        return explicit
    
    # Auto-detect from environment variables
    if os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_ACCESS_KEY_ID"):
        return "aws"
    
    if os.environ.get("AZURE_LOCATION") or os.environ.get("AZURE_SUBSCRIPTION_ID") or os.environ.get("AZURE_CLIENT_ID"):
        return "azure"
    
    # Default to AWS for backward compatibility
    return "aws"

def _get_aws_helpers():
    """Lazy import AWS helpers."""
    global _aws_helpers
    if _aws_helpers is None:
        from . import _aws_helpers as aws
        _aws_helpers = aws
    return _aws_helpers

def _get_azure_helpers():
    """Lazy import Azure helpers."""
    global _azure_helpers
    if _azure_helpers is None:
        from . import _azure_helpers as azure
        _azure_helpers = azure
    return _azure_helpers

def get_region() -> str:
    """
    Get the current cloud region/location.
    
    Returns:
        Region string (e.g., 'us-west-2' for AWS, 'eastus' for Azure)
    """
    provider = get_cloud_provider()
    
    if provider == "aws":
        return _get_aws_helpers().aws_region()
    elif provider == "azure":
        return _get_azure_helpers().azure_location()
    else:
        raise NotImplementedError(f"Region detection not implemented for {provider}")

def get_identity() -> dict:
    """
    Get the current cloud identity/account information.
    
    Returns:
        Dictionary with identity information (structure varies by cloud)
    """
    provider = get_cloud_provider()
    
    if provider == "aws":
        return _get_aws_helpers().sts_identity()
    elif provider == "azure":
        return _get_azure_helpers().azure_identity()
    else:
        raise NotImplementedError(f"Identity detection not implemented for {provider}")

def assert_account(expected_account_id: Optional[str]) -> None:
    """
    Assert that the current cloud account/subscription matches the expected value.
    
    Args:
        expected_account_id: Expected account ID (AWS) or subscription ID (Azure)
    """
    if not expected_account_id:
        return
    
    provider = get_cloud_provider()
    
    if provider == "aws":
        _get_aws_helpers().assert_account(expected_account_id)
    elif provider == "azure":
        _get_azure_helpers().assert_subscription(expected_account_id)
    else:
        raise NotImplementedError(f"Account assertion not implemented for {provider}")

def cluster_exists(cluster_name: str) -> bool:
    """
    Check if a Kubernetes cluster exists.
    
    Args:
        cluster_name: Name of the cluster
        
    Returns:
        True if cluster exists, False otherwise
    """
    provider = get_cloud_provider()
    
    if provider == "aws":
        return _get_aws_helpers().eks_cluster_exists(cluster_name)
    elif provider == "azure":
        return _get_azure_helpers().aks_cluster_exists(cluster_name)
    else:
        raise NotImplementedError(f"Cluster existence check not implemented for {provider}")

def configure_kubectl(cluster_name: str, region: Optional[str] = None) -> None:
    """
    Configure kubectl to connect to the specified cluster.
    
    Args:
        cluster_name: Name of the cluster
        region: Region/location (optional, will be auto-detected if not provided)
    """
    if region is None:
        region = get_region()
    
    provider = get_cloud_provider()
    
    if provider == "aws":
        _get_aws_helpers().configure_kubectl_eks(cluster_name, region)
    elif provider == "azure":
        _get_azure_helpers().configure_kubectl_aks(cluster_name, region)
    else:
        raise NotImplementedError(f"kubectl configuration not implemented for {provider}")

def get_blob_storage_service_name() -> str:
    """
    Get the name of the blob storage service for the current cloud provider.
    
    Returns:
        Service name (e.g., 'S3' for AWS, 'Blob Storage' for Azure)
    """
    provider = get_cloud_provider()
    
    if provider == "aws":
        return "S3"
    elif provider == "azure":
        return "Blob Storage"
    else:
        return "Object Storage"

def get_kubernetes_service_name() -> str:
    """
    Get the name of the managed Kubernetes service for the current cloud provider.
    
    Returns:
        Service name (e.g., 'EKS' for AWS, 'AKS' for Azure)
    """
    provider = get_cloud_provider()
    
    if provider == "aws":
        return "EKS"
    elif provider == "azure":
        return "AKS"
    else:
        return "Kubernetes"

def get_database_service_name() -> str:
    """
    Get the name of the managed database service for the current cloud provider.
    
    Returns:
        Service name (e.g., 'RDS' for AWS, 'Azure Database' for Azure)
    """
    provider = get_cloud_provider()
    
    if provider == "aws":
        return "RDS"
    elif provider == "azure":
        return "Azure Database for PostgreSQL"
    else:
        return "Managed Database"

def get_cache_service_name() -> str:
    """
    Get the name of the managed cache service for the current cloud provider.
    
    Returns:
        Service name (e.g., 'ElastiCache' for AWS, 'Azure Cache' for Azure)
    """
    provider = get_cloud_provider()
    
    if provider == "aws":
        return "ElastiCache"
    elif provider == "azure":
        return "Azure Cache for Redis"
    else:
        return "Managed Cache"

def get_storage_driver_name() -> str:
    """
    Get the name of the storage CSI driver for the current cloud provider.
    
    Returns:
        Driver name (e.g., 'EBS CSI' for AWS, 'Azure Disk CSI' for Azure)
    """
    provider = get_cloud_provider()
    
    if provider == "aws":
        return "EBS CSI"
    elif provider == "azure":
        return "Azure Disk CSI"
    else:
        return "Storage CSI"

def verify_blob_storage_access() -> bool:
    """
    Verify access to blob storage service.
    
    Returns:
        True if access is verified, False otherwise
    """
    provider = get_cloud_provider()
    
    if provider == "aws":
        return _get_aws_helpers().verify_s3_access()
    elif provider == "azure":
        return _get_azure_helpers().verify_blob_storage_access()
    else:
        raise NotImplementedError(f"Blob storage verification not implemented for {provider}")

