# Bhumi Release Process

This document describes the automated release process for the Bhumi project, which includes multi-platform wheel building, automated PyPI publishing, and version management.

## 🚀 Quick Start

### For Regular Releases
1. **Setup PyPI Token** (one-time setup - see [Setup section](#setup))
2. **Create Release**: Use GitHub Actions → "Release Process" → Run workflow
3. **Choose Version Bump**: Select patch/minor/major version bump
4. **Automatic Publishing**: Wheels are built and published to PyPI automatically

### For Hotfixes or Manual Control
1. **Manual Version Bump**: Edit version in `pyproject.toml` and `Cargo.toml`
2. **Tag Release**: `git tag -a v1.2.3 -m "Release v1.2.3"`
3. **Push Tag**: `git push origin v1.2.3`
4. **Automatic Build**: Workflows trigger automatically on tag push

## 📋 Release Workflows

### 1. Release Process Workflow (`release-process.yml`)
**Trigger**: Manual dispatch from GitHub Actions UI

**What it does**:
- Automatically bumps version (patch/minor/major) in both `pyproject.toml` and `Cargo.toml`
- Generates changelog from git commits
- Creates and pushes a new git tag
- Triggers the wheel building workflow
- Updates documentation with new version

**Usage**:
```bash
# Go to GitHub → Actions → "Release Process" → Run workflow
# Select version bump type: patch, minor, or major
```

### 2. Build and Publish Wheels (`build-wheels.yml`)
**Triggers**: 
- Automatic: When tags matching `v*` are pushed
- Manual: GitHub Actions UI dispatch

**Platform Coverage**:
- **Linux**: x86_64, aarch64 (manylinux 2.17 & 2.28)
- **Windows**: x64, x86
- **macOS**: x86_64, arm64 (Apple Silicon)

**Python Versions**: 3.8, 3.9, 3.10, 3.11, 3.12, 3.13

**What it does**:
- Builds wheels for all platform/Python combinations
- Tests wheels on each platform
- Creates source distribution (sdist)
- Publishes to PyPI (on tag pushes)
- Creates GitHub release with artifacts
- Generates release notes

## 🔧 Setup

### Required GitHub Secrets

Add these secrets in GitHub → Settings → Secrets and variables → Actions:

#### 1. `PYPI_API_TOKEN` (Required for PyPI publishing)
```bash
# Get your PyPI API token from https://pypi.org/manage/account/token/
# Scope: "Entire account" or specific to "bhumi" project
# Format: pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 2. Optional Secrets for Enhanced Features
```bash
# For Slack/Discord notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# For enhanced GitHub integration (optional - uses GITHUB_TOKEN by default)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### PyPI Token Setup Steps

1. **Go to PyPI**: https://pypi.org/manage/account/token/
2. **Create New Token**:
   - Token name: `bhumi-github-actions`
   - Scope: Select "Entire account" (or "bhumi" project if it exists)
3. **Copy Token**: Save the `pypi-` prefixed token
4. **Add to GitHub**:
   - Go to your repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Your copied token
5. **Save**: Click "Add secret"

## 📦 Release Types

### Patch Release (Bug fixes)
```bash
# Bumps 1.2.3 → 1.2.4
# Use GitHub Actions → Release Process → Run workflow → Select "patch"
```

### Minor Release (New features)
```bash
# Bumps 1.2.3 → 1.3.0  
# Use GitHub Actions → Release Process → Run workflow → Select "minor"
```

### Major Release (Breaking changes)
```bash
# Bumps 1.2.3 → 2.0.0
# Use GitHub Actions → Release Process → Run workflow → Select "major"
```

## 🔍 Monitoring Releases

### Check Release Status
1. **GitHub Actions**: Monitor workflow progress in Actions tab
2. **PyPI**: Check https://pypi.org/project/bhumi/ for new version
3. **GitHub Releases**: View release notes and downloadable assets

### Common Issues and Solutions

#### ❌ PyPI Publishing Failed
```bash
# Check if token is correctly set
# Verify token has correct permissions
# Ensure version doesn't already exist on PyPI
```

#### ❌ Wheel Building Failed
```bash
# Check platform-specific logs in GitHub Actions
# Verify all dependencies are available for target platform
# Check if Rust/Python versions are compatible
```

#### ❌ Version Bump Failed
```bash
# Ensure .bumpversion.cfg is properly configured
# Check if pyproject.toml and Cargo.toml have version fields
# Verify git working directory is clean
```

## 🏗️ Architecture

### File Structure
```
.github/workflows/
├── build-wheels.yml      # Multi-platform wheel building
├── release-process.yml   # Automated version management
├── integration-tests.yml # CI testing
└── check-release-ready.yml # Pre-release validation

scripts/
└── validate-workflows.py # Workflow validation utility

.bumpversion.cfg          # Version management configuration
```

### Build Matrix
The wheel building supports these combinations:

| Platform | Architecture | Python Versions | Special Notes |
|----------|--------------|-----------------|---------------|
| Linux | x86_64 | 3.8-3.13 | manylinux 2.17 & 2.28 |
| Linux | aarch64 | 3.8-3.13 | Cross-compiled with QEMU |
| Windows | x64 | 3.8-3.13 | Native compilation |
| Windows | x86 | 3.8-3.13 | 32-bit support |
| macOS | x86_64 | 3.8-3.13 | Intel Macs |
| macOS | arm64 | 3.8-3.13 | Apple Silicon (M1/M2) |

## 📚 Advanced Usage

### Manual Version Control
```bash
# Edit versions manually if needed
# pyproject.toml: version = "1.2.3"  
# Cargo.toml: version = "1.2.3"

# Create and push tag
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

### Testing Before Release
```bash
# Validate workflows
python scripts/validate-workflows.py

# Run integration tests locally
python -m pytest tests/integration/

# Build wheel locally (requires maturin)
maturin build --release
```

### Emergency Rollback
```bash
# If a release has issues, you can:
# 1. Delete the git tag: git tag -d v1.2.3 && git push origin :refs/tags/v1.2.3
# 2. Delete the PyPI release (not recommended - use yanking instead)
# 3. Create a new patch release with fixes
```

## 🎯 Best Practices

1. **Always test locally** before creating releases
2. **Use descriptive commit messages** for automatic changelog generation
3. **Follow semantic versioning** (patch/minor/major)
4. **Monitor the Actions tab** during releases
5. **Keep PyPI tokens secure** and rotate them regularly
6. **Test the released package** with `pip install bhumi==x.y.z`

## 🔒 Security Notes

- PyPI tokens are stored as GitHub secrets (encrypted)
- Workflows use minimal required permissions
- Cross-compilation uses official GitHub Actions runners
- All builds are reproducible and auditable

---

**Need help?** Check the GitHub Actions logs or create an issue in the repository.
