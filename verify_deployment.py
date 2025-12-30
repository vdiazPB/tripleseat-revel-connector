#!/usr/bin/env python3
"""Final pre-deployment verification script."""

import os
import sys
import subprocess

def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"✓ {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ PASS")
        return True
    else:
        print("❌ FAIL")
        print(result.stderr)
        return False

def check_file_exists(path, description):
    """Check if a file exists."""
    print(f"\n{'='*60}")
    print(f"✓ {description}")
    print(f"{'='*60}")
    if os.path.exists(path):
        print(f"✅ Found: {path}")
        return True
    else:
        print(f"❌ Missing: {path}")
        return False

print("\n" + "="*60)
print("FINAL PRE-DEPLOYMENT VERIFICATION")
print("="*60)

all_passed = True

# 1. Syntax verification
print("\n[1/7] Checking Python syntax...")
all_passed &= run_command(
    "python -m py_compile app.py integrations/tripleseat/webhook_handler.py integrations/tripleseat/sync.py",
    "Python files syntax check"
)

# 2. Import verification
print("\n[2/7] Checking imports...")
all_passed &= run_command(
    "python -c \"from app import app; from integrations.tripleseat.sync import TripleSeatSync; print('All imports OK')\"",
    "Import verification"
)

# 3. APScheduler availability
print("\n[3/7] Checking APScheduler...")
all_passed &= run_command(
    "python -c \"from apscheduler.schedulers.background import BackgroundScheduler; print('APScheduler available')\"",
    "APScheduler availability"
)

# 4. Requirements.txt has apscheduler
print("\n[4/7] Checking requirements.txt...")
with open('requirements.txt', 'r') as f:
    content = f.read()
    if 'apscheduler' in content:
        print("✅ apscheduler in requirements.txt")
    else:
        print("❌ apscheduler NOT in requirements.txt")
        all_passed = False

# 5. Check key files exist
print("\n[5/7] Checking file structure...")
key_files = [
    ('app.py', 'app.py (main app file)'),
    ('integrations/tripleseat/sync.py', 'sync.py (reconciliation module)'),
    ('integrations/tripleseat/webhook_handler.py', 'webhook_handler.py (webhook processing)'),
    ('requirements.txt', 'requirements.txt (dependencies)'),
]

for filepath, description in key_files:
    all_passed &= check_file_exists(filepath, description)

# 6. Environment variables
print("\n[6/7] Checking environment variables...")
print("="*60)
print("✓ Checking required environment variables")
print("="*60)

required_vars = [
    'REVEL_API_KEY',
    'TRIPLESEAT_OAUTH_CLIENT_ID',
    'TRIPLESEAT_OAUTH_CLIENT_SECRET',
    'TRIPLESEAT_SITE_ID',
    'REVEL_ESTABLISHMENT_ID',
]

missing_vars = []
for var in required_vars:
    if os.getenv(var):
        print(f"✅ {var} set")
    else:
        print(f"❌ {var} NOT set")
        missing_vars.append(var)
        all_passed = False

if not missing_vars:
    print("\n✅ All required environment variables configured")

# 7. Git status
print("\n[7/7] Checking git status...")
print("="*60)
print("✓ Git repository status")
print("="*60)
result = subprocess.run("git status --short", shell=True, capture_output=True, text=True)
print(result.stdout)

# Summary
print("\n" + "="*60)
print("VERIFICATION SUMMARY")
print("="*60)

if all_passed and not missing_vars:
    print("\n✅ ALL CHECKS PASSED - READY FOR DEPLOYMENT\n")
    print("Next steps:")
    print("1. Review changes: git diff")
    print("2. Commit: git commit -m 'Implement 3-tier reconciliation architecture'")
    print("3. Push: git push")
    print("\nAfter push:")
    print("- Wait 5-10 minutes for Render to redeploy")
    print("- Check logs for: 'APScheduler initialized'")
    print("- Wait 45 minutes for first scheduled sync")
    sys.exit(0)
else:
    print("\n❌ SOME CHECKS FAILED - DO NOT DEPLOY\n")
    print("Fix issues before deploying:")
    if missing_vars:
        print(f"- Missing environment variables: {', '.join(missing_vars)}")
    print("- Check errors above")
    sys.exit(1)
