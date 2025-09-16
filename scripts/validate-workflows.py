#!/usr/bin/env python3
"""
Script to validate GitHub Actions workflows for bhumi project.
"""

import yaml
import os
import sys
from pathlib import Path

def validate_workflow_file(filepath):
    """Validate a single workflow YAML file."""
    try:
        with open(filepath, 'r') as f:
            workflow = yaml.safe_load(f)
        
        print(f"✅ {filepath.name} - Valid YAML")
        
        # Check for required fields
        required_fields = ['name', 'jobs']
        for field in required_fields:
            if field not in workflow:
                print(f"❌ {filepath.name} - Missing required field: {field}")
                return False
        
        # Special handling for 'on' field (reserved keyword in Python)
        if 'on' not in workflow and True not in workflow:
            print(f"❌ {filepath.name} - Missing required field: on")
            return False
        
        # Check jobs structure
        jobs = workflow.get('jobs', {})
        if not jobs:
            print(f"❌ {filepath.name} - No jobs defined")
            return False
        
        print(f"   - Found {len(jobs)} jobs: {', '.join(jobs.keys())}")
        
        # Check for permissions (security best practice)
        if 'permissions' in workflow:
            print(f"   - Permissions defined: {list(workflow['permissions'].keys())}")
        
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ {filepath.name} - YAML Error: {e}")
        return False
    except Exception as e:
        print(f"❌ {filepath.name} - Error: {e}")
        return False

def main():
    """Main validation function."""
    print("🔍 Validating GitHub Actions workflows for bhumi...")
    print()
    
    workflows_dir = Path(__file__).parent.parent / '.github' / 'workflows'
    
    if not workflows_dir.exists():
        print("❌ .github/workflows directory not found!")
        return 1
    
    workflow_files = list(workflows_dir.glob('*.yml')) + list(workflows_dir.glob('*.yaml'))
    
    if not workflow_files:
        print("❌ No workflow files found!")
        return 1
    
    print(f"Found {len(workflow_files)} workflow files:")
    
    all_valid = True
    for workflow_file in workflow_files:
        valid = validate_workflow_file(workflow_file)
        all_valid = all_valid and valid
        print()
    
    # Check for specific workflows
    expected_workflows = ['build-wheels.yml', 'release-process.yml']
    existing_workflows = [f.name for f in workflow_files]
    
    print("📋 Checking for expected workflows:")
    for expected in expected_workflows:
        if expected in existing_workflows:
            print(f"   ✅ {expected} - Found")
        else:
            print(f"   ❌ {expected} - Missing")
            all_valid = False
    
    print()
    if all_valid:
        print("🎉 All workflows are valid!")
        print()
        print("📝 Usage:")
        print("1. To create a new release: Go to Actions → Release Process → Run workflow")
        print("2. To manually build wheels: Go to Actions → Build and publish wheels → Run workflow")
        print("3. Automatic builds: Push a tag like 'v1.0.0' to trigger wheel building")
        return 0
    else:
        print("❌ Some workflows have issues. Please check the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
