#!/usr/bin/env python3
"""
Release script for Hedge Fund Simulator.

This script automates the process of creating a new release of the package.
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
import click

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
CHANGELOG_PATH = PROJECT_ROOT / "CHANGELOG.md"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
RELEASE_NOTES_PATH = PROJECT_ROOT / "RELEASE_NOTES_TEMPLATE.md"


def get_current_version() -> str:
    """Get the current version from pyproject.toml."""
    with open(PYPROJECT_PATH, 'r') as f:
        content = f.read()
    
    version_match = re.search(r'version\s*=\s*"([\d.]+)"', content)
    if not version_match:
        raise ValueError("Could not find version in pyproject.toml")
    
    return version_match.group(1)


def update_version(new_version: str) -> None:
    """Update version in pyproject.toml and other files."""
    # Update pyproject.toml
    with open(PYPROJECT_PATH, 'r') as f:
        content = f.read()
    
    content = re.sub(
        r'(version\s*=\s*")[\d.]+(")',
        f'\\g<1>{new_version}\\g<2>',
        content
    )
    
    with open(PYPROJECT_PATH, 'w') as f:
        f.write(content)
    
    print(f"✓ Updated version to {new_version} in pyproject.toml")


def get_git_changes() -> str:
    """Get changes since last tag."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--no-merges", "--pretty=format:- %s", "$(git describe --tags --abbrev=0)..HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def update_changelog(version: str, changes: str) -> None:
    """Update CHANGELOG.md with the new release."""
    if not changes:
        print("No changes detected since last release.")
        return
    
    with open(CHANGELOG_PATH, 'r') as f:
        content = f.read()
    
    today = datetime.now().strftime("%Y-%m-%d")
    new_entry = f"## [{version}] - {today}\n\n{changes}\n\n"
    
    # Insert after the first occurrence of "## [Unreleased]"
    if "## [Unreleased]" in content:
        content = content.replace(
            "## [Unreleased]",
            f"## [Unreleased]\n\n## [{version}] - {today}\n\n{changes}"
        )
    else:
        content = f"## [{version}] - {today}\n\n{changes}\n\n{content}"
    
    with open(CHANGELOG_PATH, 'w') as f:
        f.write(content)
    
    print("✓ Updated CHANGELOG.md")


def create_git_tag(version: str) -> None:
    """Create and push a git tag for the release."""
    tag_name = f"v{version}"
    
    try:
        # Stage all changes
        subprocess.run(["git", "add", "-A"], check=True)
        
        # Commit changes
        subprocess.run(
            ["git", "commit", "-m", f"Release {tag_name}"],
            check=True
        )
        
        # Create tag
        subprocess.run(["git", "tag", "-a", tag_name, "-m", f"Version {version}"], check=True)
        
        print(f"✓ Created git tag {tag_name}")
        
        # Push changes and tags
        subprocess.run(["git", "push"], check=True)
        subprocess.run(["git", "push", "--tags"], check=True)
        
        print("✓ Pushed changes and tags to remote")
    except subprocess.CalledProcessError as e:
        print(f"Error creating git tag: {e}", file=sys.stderr)
        sys.exit(1)


def build_package() -> None:
    """Build the package for distribution."""
    try:
        subprocess.run(
            [sys.executable, "-m", "build", "--wheel"],
            cwd=PROJECT_ROOT,
            check=True
        )
        print("✓ Built package")
    except subprocess.CalledProcessError as e:
        print(f"Error building package: {e}", file=sys.stderr)
        sys.exit(1)


def upload_to_pypi(test: bool = False) -> None:
    """Upload the package to PyPI or TestPyPI."""
    dist_dir = PROJECT_ROOT / "dist"
    if not dist_dir.exists() or not any(dist_dir.iterdir()):
        print("No distribution files found. Building package first...")
        build_package()
    
    repo_url = "--repository testpypi" if test else ""
    
    try:
        subprocess.run(
            f"{sys.executable} -m twine upload {repo_url} dist/*",
            shell=True,
            cwd=PROJECT_ROOT,
            check=True
        )
        print(f"✓ Uploaded package to {'TestPyPI' if test else 'PyPI'}")
    except subprocess.CalledProcessError as e:
        print(f"Error uploading package: {e}", file=sys.stderr)
        sys.exit(1)


def bump_version(version: str, part: str = "patch") -> str:
    """Bump the version number."""
    major, minor, patch = map(int, version.split('.'))
    
    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


@click.command()
@click.option('--version', help='Version number to release (e.g., 1.0.0)')
@click.option('--part', type=click.Choice(['major', 'minor', 'patch']), 
              default='patch', help='Part of version to bump')
@click.option('--test', is_flag=True, help='Upload to TestPyPI instead of PyPI')
@click.option('--no-upload', is_flag=True, help='Skip uploading to PyPI')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompts')
def main(version: Optional[str], part: str, test: bool, no_upload: bool, yes: bool) -> None:
    """Release a new version of the package."""
    current_version = get_current_version()
    
    if version:
        new_version = version
    else:
        new_version = bump_version(current_version, part)
    
    changes = get_git_changes()
    
    print(f"Current version: {current_version}")
    print(f"New version:     {new_version}")
    
    if changes:
        print("\nChanges since last release:")
        print(changes)
    
    if not yes:
        if not click.confirm("\nDo you want to continue?", default=True):
            print("Release canceled.")
            return
    
    # Update version in files
    update_version(new_version)
    
    # Update changelog
    if changes:
        update_changelog(new_version, changes)
    
    # Create git tag
    create_git_tag(new_version)
    
    # Build and upload package
    if not no_upload:
        build_package()
        upload_to_pypi(test=test)
    
    print(f"\n🎉 Successfully released version {new_version}!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nRelease canceled by user.")
        sys.exit(1)
