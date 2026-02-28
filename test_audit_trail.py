#!/usr/bin/env python3
"""
Test script for Agent Audit Trail CLI.

Run: python test_audit_trail.py
"""

import subprocess
import json
import sys
import os
from pathlib import Path


def run_cmd(args):
    """Run audit_trail.py command and return output."""
    cmd = [sys.executable, "audit_trail.py"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def test_full_workflow():
    """Test complete workflow: start -> action -> evidence -> complete -> verify."""
    print("=" * 60)
    print("TEST: Full Workflow")
    print("=" * 60)
    
    # Test 1: Start session
    print("\n1. Starting session...")
    code, out, err = run_cmd(["start", "--task", "Test deployment"])
    assert code == 0, f"Start failed: {err}"
    data = json.loads(out)
    session_id = data["session_id"]
    print(f"   Session ID: {session_id}")
    print(f"   [PASS] Session started")
    
    # Test 2: Record action
    print("\n2. Recording action...")
    code, out, err = run_cmd([
        "action", "--session", session_id,
        "--type", "command_exec",
        "--description", "Ran unit tests"
    ])
    assert code == 0, f"Action failed: {err}"
    print(f"   [PASS] Action recorded")
    
    # Test 3: Add evidence
    print("\n3. Adding evidence...")
    code, out, err = run_cmd([
        "evidence", "--session", session_id,
        "--type", "url",
        "--value", "https://example.com/deploy",
        "--verified", "true"
    ])
    assert code == 0, f"Evidence failed: {err}"
    print(f"   [PASS] Evidence added")
    
    # Test 4: Complete session
    print("\n4. Completing session...")
    code, out, err = run_cmd([
        "complete", "--session", session_id,
        "--outcome", "success",
        "--summary", "Test deployment completed"
    ])
    assert code == 0, f"Complete failed: {err}"
    data = json.loads(out)
    report_file = data["report_file"]
    print(f"   Report: {report_file}")
    print(f"   [PASS] Session completed")
    
    # Test 5: Verify report
    print("\n5. Verifying report...")
    code, out, err = run_cmd(["verify", "--report", report_file])
    assert code == 0, f"Verify failed: {err}"
    data = json.loads(out)
    print(f"   Overall: {data['overall']}")
    print(f"   [PASS] Report verified")
    
    # Test 6: List sessions
    print("\n6. Listing sessions...")
    code, out, err = run_cmd(["list"])
    assert code == 0, f"List failed: {err}"
    assert session_id in out, "Session not in list"
    print(f"   [PASS] Session listed")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
    return True


def test_help():
    """Test help command."""
    print("\n" + "=" * 60)
    print("TEST: Help Command")
    print("=" * 60)
    
    code, out, err = run_cmd(["--help"])
    assert code == 0, f"Help failed: {err}"
    assert "Agent Audit Trail" in out, "Help text missing"
    print("   [PASS] Help displayed")
    return True


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    
    try:
        test_help()
        test_full_workflow()
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAILURE] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
