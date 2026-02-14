"""
Test script for the auto-update system.
Run this to verify the update checker is working correctly.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from updater import UpdateChecker
from version import get_version_info

def test_version_info():
    """Test version information retrieval."""
    print("=" * 50)
    print("Testing Version Information")
    print("=" * 50)
    
    info = get_version_info()
    print(f"Current Version: {info['version']}")
    print(f"Build Date: {info['build_date']}")
    print(f"GitHub Repo: {info['github_repo']}")
    print()

def test_update_check():
    """Test checking for updates."""
    print("=" * 50)
    print("Testing Update Check")
    print("=" * 50)
    
    checker = UpdateChecker()
    print(f"Checking repository: {checker.github_repo}")
    print(f"Current version: {checker.current_version}")
    print()
    
    print("Checking for updates...")
    result = checker.check_for_updates()
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        print()
        print("Common issues:")
        print("1. No internet connection")
        print("2. GitHub repository not found or private")
        print("3. No releases published yet")
        print("4. GitHub API rate limit reached")
        return False
    
    print(f"✓ Successfully checked for updates")
    print()
    print(f"Current Version: {result['current_version']}")
    print(f"Latest Version: {result['latest_version']}")
    print(f"Update Available: {'Yes' if result['available'] else 'No'}")
    
    if result['available']:
        print(f"Download URL: {result['download_url']}")
        print()
        print("Release Notes:")
        print("-" * 50)
        print(result['release_notes'])
        print("-" * 50)
    
    print()
    return True

def test_version_comparison():
    """Test version comparison logic."""
    print("=" * 50)
    print("Testing Version Comparison")
    print("=" * 50)
    
    checker = UpdateChecker()
    
    test_cases = [
        ("1.0.1", "1.0.0", True),   # Newer patch
        ("1.1.0", "1.0.0", True),   # Newer minor
        ("2.0.0", "1.0.0", True),   # Newer major
        ("1.0.0", "1.0.0", False),  # Same version
        ("1.0.0", "1.0.1", False),  # Older patch
        ("1.0.0", "1.1.0", False),  # Older minor
        ("1.0.0", "2.0.0", False),  # Older major
    ]
    
    all_passed = True
    for v1, v2, expected in test_cases:
        result = checker._compare_versions(v1, v2)
        status = "✓" if result == expected else "❌"
        print(f"{status} {v1} > {v2}: {result} (expected: {expected})")
        if result != expected:
            all_passed = False
    
    print()
    if all_passed:
        print("✓ All version comparison tests passed!")
    else:
        print("❌ Some version comparison tests failed!")
    
    print()
    return all_passed

def main():
    """Run all tests."""
    print()
    print("╔" + "=" * 48 + "╗")
    print("║" + " " * 10 + "Auto-Update System Test" + " " * 15 + "║")
    print("╚" + "=" * 48 + "╝")
    print()
    
    # Test 1: Version Info
    test_version_info()
    
    # Test 2: Version Comparison
    test_version_comparison()
    
    # Test 3: Update Check
    success = test_update_check()
    
    # Summary
    print("=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    if success:
        print("✓ Update system is working correctly!")
        print()
        print("Next steps:")
        print("1. Update version.py with your GitHub username")
        print("2. Create a release using build_release.bat")
        print("3. Publish the release to GitHub")
        print("4. Test the auto-update from the application")
    else:
        print("⚠ Update check failed. Please review the errors above.")
        print()
        print("Make sure:")
        print("1. version.py has the correct GitHub repository")
        print("2. The repository is public")
        print("3. You have published at least one release")
    
    print()

if __name__ == "__main__":
    main()
