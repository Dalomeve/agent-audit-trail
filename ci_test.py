#!/usr/bin/env python3
"""
CI Test Runner for Agent Audit Trail.

Usage:
    python ci_test.py          # Run all tests
    python ci_test.py --quick  # Quick test (no file I/O)
"""

import subprocess
import sys
import json
from pathlib import Path


def run_test(name, cmd, expected_returncode=0):
    """Run a test command and report results."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == expected_returncode:
        print(f"[PASS] Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout[:200]}...")
        return True
    else:
        print(f"[FAIL] Expected {expected_returncode}, got {result.returncode}")
        if result.stderr:
            print(f"Error: {result.stderr[:200]}...")
        return False


def test_import():
    """Test that audit_trail can be imported."""
    cmd = [sys.executable, "-c", "import audit_trail; print('Import OK')"]
    return run_test("Module Import", cmd)


def test_help():
    """Test help command."""
    cmd = [sys.executable, "audit_trail.py", "--help"]
    return run_test("Help Command", cmd)


def test_workflow():
    """Test complete workflow."""
    tests = [
        ("Start", ["start", "--task", "CI Test"]),
        ("List", ["list"]),
    ]
    
    # Start session
    result = subprocess.run(
        [sys.executable, "audit_trail.py"] + tests[0][1],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print(f"[FAIL] Start failed: {result.stderr}")
        return False
    
    data = json.loads(result.stdout)
    session_id = data["session_id"]
    print(f"Session: {session_id}")
    
    # List sessions
    result = subprocess.run(
        [sys.executable, "audit_trail.py"] + tests[1][1],
        capture_output=True, text=True
    )
    
    if session_id not in result.stdout:
        print("[FAIL] Session not in list")
        return False
    
    print("[PASS] Workflow test")
    return True


def test_privacy_scan():
    """Scan for sensitive data patterns."""
    print(f"\n{'='*60}")
    print("TEST: Privacy Scan")
    print(f"{'='*60}")
    
    sensitive_patterns = [
        "api_key=",
        "token=",
        "secret=",
        "password=",
        "Bearer ",
        "sk-"
    ]
    
    files_to_scan = list(Path(".").glob("*.py")) + list(Path(".").glob("*.md"))
    
    findings = []
    for f in files_to_scan:
        if f.name in ["ci_test.py", "test_audit_trail.py"]:
            continue
        content = f.read_text().lower()
        for pattern in sensitive_patterns:
            if pattern.lower() in content and "example" not in content:
                findings.append(f"{f.name}: {pattern}")
    
    if findings:
        print(f"[FAIL] Sensitive patterns found: {findings}")
        return False
    else:
        print("[PASS] No sensitive data detected")
        return True


def main():
    """Run all CI tests."""
    print("="*60)
    print("AGENT AUDIT TRAIL - CI TEST SUITE")
    print("="*60)
    
    tests = [
        ("Module Import", test_import),
        ("Help Command", test_help),
        ("Complete Workflow", test_workflow),
        ("Privacy Scan", test_privacy_scan),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            results.append((name, test_fn()))
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
            results.append((name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"[{status}] {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All CI tests passed!")
        return 0
    else:
        print("\n[FAILURE] Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
