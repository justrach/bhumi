#!/usr/bin/env python3
"""
Bhumi Release Helper Script

This script helps automate the release process for Bhumi.
It updates the version, creates a git tag, and triggers the release pipeline.
"""

import subprocess
import sys
import re
import argparse
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def get_current_version():
    """Get the current version from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path) as f:
        content = f.read()
    
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)
    
    return match.group(1)


def update_version(new_version):
    """Update the version in pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path) as f:
        content = f.read()
    
    # Update version
    content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)
    
    with open(pyproject_path, 'w') as f:
        f.write(content)
    
    print(f"Updated version to {new_version} in pyproject.toml")


def validate_version(version):
    """Validate version format (semantic versioning)."""
    pattern = r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+)?$'
    if not re.match(pattern, version):
        print(f"Error: Invalid version format '{version}'. Use semantic versioning (e.g., 1.0.0, 1.0.0-beta1)")
        sys.exit(1)


def check_git_status():
    """Check if git working directory is clean."""
    status = run_command("git status --porcelain")
    if status:
        print("Error: Git working directory is not clean. Please commit or stash changes first.")
        print("Uncommitted changes:")
        print(status)
        sys.exit(1)


def create_and_push_tag(version):
    """Create and push a git tag for the version."""
    tag = f"v{version}"
    
    # Check if tag already exists
    try:
        run_command(f"git rev-parse {tag}", check=True)
        print(f"Error: Tag {tag} already exists")
        sys.exit(1)
    except:
        pass  # Tag doesn't exist, which is good
    
    # Create and push tag
    run_command(f"git add pyproject.toml")
    run_command(f'git commit -m "🔖 Bump version to {version}"')
    run_command(f'git tag -a {tag} -m "Release version {version}"')
    run_command(f"git push origin main")
    run_command(f"git push origin {tag}")
    
    print(f"Created and pushed tag: {tag}")
    return tag


def main():
    parser = argparse.ArgumentParser(description="Release helper for Bhumi")
    parser.add_argument("version", help="Version to release (e.g., 0.4.1)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without actually doing it")
    parser.add_argument("--test-pypi", action="store_true", help="Release to Test PyPI instead of PyPI")
    
    args = parser.parse_args()
    
    # Validate inputs
    validate_version(args.version)
    current_version = get_current_version()
    
    print(f"🚀 Bhumi Release Helper")
    print(f"Current version: {current_version}")
    print(f"New version: {args.version}")
    
    if args.dry_run:
        print("🔍 DRY RUN - No changes will be made")
        print("\nWould perform the following actions:")
        print(f"1. Update version to {args.version} in pyproject.toml")
        print(f"2. Create git tag v{args.version}")
        print(f"3. Push changes and tag to trigger release pipeline")
        return
    
    # Check git status
    check_git_status()
    
    # Confirm release
    confirm = input(f"\n❓ Are you sure you want to release version {args.version}? (y/N): ")
    if confirm.lower() not in ['y', 'yes']:
        print("Release cancelled.")
        return
    
    try:
        # Update version
        update_version(args.version)
        
        # Create and push tag (this will trigger the release pipeline)
        tag = create_and_push_tag(args.version)
        
        print("\n✅ Release initiated successfully!")
        print(f"📦 Tag {tag} has been created and pushed")
        print("🔄 GitHub Actions will now build and release the package")
        print("🔗 Check progress at: https://github.com/rachpradhan/bhumi/actions")
        
        if args.test_pypi:
            print("📍 Note: This will be released to Test PyPI")
        else:
            print("📍 Note: This will be released to PyPI")
        
        print(f"\n🎉 Once complete, users can install with:")
        print(f"   pip install bhumi=={args.version}")
        
    except Exception as e:
        print(f"❌ Error during release: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
