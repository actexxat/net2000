"""
Version information for Internet 2000 application.
This file is automatically updated during the build process.
"""

__version__ = "1.0.002"
__build_date__ = "2026-02-15"
__github_repo__ = "actexxat/net2000"  # Update this with your actual GitHub repo

# Minimum version required to run the application
# Set this to enforce updates (e.g., "1.0.0" means versions below 1.0.0 cannot run)
# Set to None to disable enforcement
__minimum_required_version__ = "1.0.001"

def get_version():
    """Returns the current version string."""
    return __version__

def get_build_date():
    """Returns the build date."""
    return __build_date__

def get_version_info():
    """Returns a dictionary with all version information."""
    return {
        'version': __version__,
        'build_date': __build_date__,
        'github_repo': __github_repo__,
        'minimum_required_version': __minimum_required_version__,
    }

def compare_versions(version1, version2):
    """
    Compare two version strings (e.g., "1.2.3" vs "1.2.0").
    Returns: 1 if version1 > version2, -1 if version1 < version2, 0 if equal
    """
    try:
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        # Pad with zeros if needed
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts += [0] * (max_len - len(v1_parts))
        v2_parts += [0] * (max_len - len(v2_parts))
        
        if v1_parts > v2_parts:
            return 1
        elif v1_parts < v2_parts:
            return -1
        else:
            return 0
    except:
        return 0

def is_version_allowed():
    """
    Check if the current version meets the minimum required version.
    Returns: (allowed: bool, message: str)
    """
    if __minimum_required_version__ is None:
        return True, ""
    
    comparison = compare_versions(__version__, __minimum_required_version__)
    
    if comparison < 0:
        return False, f"This version ({__version__}) is outdated. Minimum required version is {__minimum_required_version__}. Please update immediately."
    
    return True, ""
