"""
Input validation utilities
"""
import os
import validators
from pathlib import Path


def validate_repository_source(source: str) -> bool:
    """Validate repository source (URL, path, or zip)"""
    
    # Check if it's a valid URL
    if validators.url(source):
        return True
    
    # Check if it's a valid local path
    if os.path.exists(source):
        return True
    
    # Check if it's a zip file
    if source.endswith('.zip') and os.path.exists(source):
        return True
    
    return False


def validate_cloud_provider(provider: str) -> bool:
    """Validate cloud provider"""
    valid_providers = ['aws', 'gcp', 'azure']
    return provider.lower() in valid_providers


def validate_deployment_description(description: str) -> bool:
    """Validate deployment description"""
    if not description or len(description.strip()) < 10:
        return False
    return True
