#!/usr/bin/env python3
"""
Agent Audit Trail - Lightweight evidence tracker for agent workflows.

Usage:
    python audit_trail.py start --task "Task description"
    python audit_trail.py action --session <id> --type <type> --description <desc>
    python audit_trail.py evidence --session <id> --type <type> --value <value>
    python audit_trail.py complete --session <id> --outcome <success|failure>
    python audit_trail.py verify --report <path>
    python audit_trail.py list
"""

import argparse
import json
import hashlib
import os
import sys
from datetime import datetime
from pathlib import Path


def generate_session_id():
    """Generate unique session ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    random_part = hashlib.md5(os.urandom(8)).hexdigest()[:6]
    return f"ats_{timestamp}_{random_part}"


def get_timestamp():
    """Get current UTC timestamp in ISO format."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def load_sessions():
    """Load all sessions from storage."""
    sessions_file = Path.home() / ".agent_audit_trail" / "sessions.json"
    if sessions_file.exists():
        with open(sessions_file, "r") as f:
            return json.load(f)
    return {"sessions": [], "reports": []}


def save_sessions(data):
    """Save sessions to storage."""
    sessions_dir = Path.home() / ".agent_audit_trail"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    sessions_file = sessions_dir / "sessions.json"
    with open(sessions_file, "w") as f:
        json.dump(data, f, indent=2)


def cmd_start(args):
    """Start a new audit session."""
    session_id = generate_session_id()
    session = {
        "session_id": session_id,
        "task": args.task,
        "started_at": get_timestamp(),
        "status": "in_progress",
        "actions": [],
        "evidence": []
    }
    
    data = load_sessions()
    data["sessions"].append(session)
    save_sessions(data)
    
    print(json.dumps({
        "session_id": session_id,
        "task": session["task"],
        "started_at": session["started_at"],
        "status": session["status"]
    }, indent=2))


def cmd_action(args):
    """Record an action in a session."""
    data = load_sessions()
    
    for session in data["sessions"]:
        if session["session_id"] == args.session:
            if session["status"] != "in_progress":
                print(f"Error: Session {args.session} is not in_progress", file=sys.stderr)
                sys.exit(1)
            
            action = {
                "timestamp": get_timestamp(),
                "type": args.type,
                "description": args.description
            }
            
            if args.artifact:
                action["artifact"] = args.artifact
            if args.output:
                action["output"] = args.output
            if args.metadata:
                action["metadata"] = json.loads(args.metadata)
            
            session["actions"].append(action)
            save_sessions(data)
            
            print(json.dumps({"status": "recorded", "action": action}, indent=2))
            return
    
    print(f"Error: Session {args.session} not found", file=sys.stderr)
    sys.exit(1)


def cmd_evidence(args):
    """Add evidence to a session."""
    data = load_sessions()
    
    for session in data["sessions"]:
        if session["session_id"] == args.session:
            if session["status"] != "in_progress":
                print(f"Error: Session {args.session} is not in_progress", file=sys.stderr)
                sys.exit(1)
            
            evidence = {
                "type": args.type,
                "value": args.value,
                "added_at": get_timestamp(),
                "verified": args.verified.lower() == "true" if args.verified else False
            }
            
            if args.description:
                evidence["description"] = args.description
            
            session["evidence"].append(evidence)
            save_sessions(data)
            
            print(json.dumps({"status": "added", "evidence": evidence}, indent=2))
            return
    
    print(f"Error: Session {args.session} not found", file=sys.stderr)
    sys.exit(1)


def cmd_complete(args):
    """Complete a session and generate report."""
    data = load_sessions()
    
    for session in data["sessions"]:
        if session["session_id"] == args.session:
            if session["status"] != "in_progress":
                print(f"Error: Session {args.session} is not in_progress", file=sys.stderr)
                sys.exit(1)
            
            session["status"] = "completed"
            session["completed_at"] = get_timestamp()
            session["outcome"] = args.outcome
            session["summary"] = args.summary or ""
            
            # Generate report
            report = {
                "session_id": session["session_id"],
                "task": session["task"],
                "started_at": session["started_at"],
                "completed_at": session["completed_at"],
                "duration_seconds": calculate_duration(session["started_at"], session["completed_at"]),
                "outcome": session["outcome"],
                "actions": session["actions"],
                "evidence": session["evidence"],
                "summary": session["summary"]
            }
            
            # Save report
            reports_dir = Path.home() / ".agent_audit_trail" / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            report_file = reports_dir / f"audit_report_{session['session_id']}.json"
            
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            
            data["reports"].append({
                "session_id": session["session_id"],
                "report_file": str(report_file),
                "completed_at": session["completed_at"]
            })
            
            save_sessions(data)
            
            print(json.dumps({
                "status": "completed",
                "session_id": session["session_id"],
                "report_file": str(report_file),
                "outcome": session["outcome"]
            }, indent=2))
            return
    
    print(f"Error: Session {args.session} not found", file=sys.stderr)
    sys.exit(1)


def cmd_verify(args):
    """Verify a report's evidence."""
    if not os.path.exists(args.report):
        print(f"Error: Report file not found: {args.report}", file=sys.stderr)
        sys.exit(1)
    
    with open(args.report, "r") as f:
        report = json.load(f)
    
    results = {"report": args.report, "evidence_checks": []}
    
    for ev in report.get("evidence", []):
        check = {
            "type": ev["type"],
            "value": ev["value"],
            "status": "unknown"
        }
        
        if ev["type"] == "file":
            check["status"] = "exists" if os.path.exists(ev["value"]) else "missing"
        elif ev["type"] == "url":
            check["status"] = "format_valid" if ev["value"].startswith("http") else "invalid_format"
        elif ev["type"] == "hash":
            check["status"] = "format_valid" if len(ev["value"]) == 64 else "invalid_length"
        else:
            check["status"] = "verified" if ev.get("verified") else "unverified"
        
        results["evidence_checks"].append(check)
    
    results["overall"] = "pass" if all(c["status"] in ["exists", "verified", "format_valid"] for c in results["evidence_checks"]) else "warning"
    
    print(json.dumps(results, indent=2))


def cmd_list(args):
    """List all sessions."""
    data = load_sessions()
    
    if not data["sessions"]:
        print("No sessions found.")
        return
    
    print(f"{'Session ID':<30} {'Task':<40} {'Status':<12} {'Started'}")
    print("-" * 90)
    
    for session in data["sessions"][-10:]:  # Last 10 sessions
        print(f"{session['session_id']:<30} {session['task'][:38]:<40} {session['status']:<12} {session['started_at']}")


def calculate_duration(start, end):
    """Calculate duration in seconds between two timestamps."""
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
        end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
        return int((end_dt - start_dt).total_seconds())
    except:
        return 0


def main():
    parser = argparse.ArgumentParser(description="Agent Audit Trail - Evidence tracker for agent workflows")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # start command
    start_parser = subparsers.add_parser("start", help="Start a new audit session")
    start_parser.add_argument("--task", required=True, help="Task description")
    
    # action command
    action_parser = subparsers.add_parser("action", help="Record an action")
    action_parser.add_argument("--session", required=True, help="Session ID")
    action_parser.add_argument("--type", required=True, help="Action type")
    action_parser.add_argument("--description", required=True, help="Action description")
    action_parser.add_argument("--artifact", help="Artifact path")
    action_parser.add_argument("--output", help="Command output")
    action_parser.add_argument("--metadata", help="Additional metadata (JSON)")
    
    # evidence command
    evidence_parser = subparsers.add_parser("evidence", help="Add evidence")
    evidence_parser.add_argument("--session", required=True, help="Session ID")
    evidence_parser.add_argument("--type", required=True, help="Evidence type")
    evidence_parser.add_argument("--value", required=True, help="Evidence value")
    evidence_parser.add_argument("--description", help="Evidence description")
    evidence_parser.add_argument("--verified", help="Is verified (true/false)")
    
    # complete command
    complete_parser = subparsers.add_parser("complete", help="Complete session")
    complete_parser.add_argument("--session", required=True, help="Session ID")
    complete_parser.add_argument("--outcome", required=True, choices=["success", "failure"], help="Outcome")
    complete_parser.add_argument("--summary", help="Summary of what was accomplished")
    
    # verify command
    verify_parser = subparsers.add_parser("verify", help="Verify report evidence")
    verify_parser.add_argument("--report", required=True, help="Path to report JSON file")
    
    # list command
    list_parser = subparsers.add_parser("list", help="List sessions")
    
    args = parser.parse_args()
    
    if args.command == "start":
        cmd_start(args)
    elif args.command == "action":
        cmd_action(args)
    elif args.command == "evidence":
        cmd_evidence(args)
    elif args.command == "complete":
        cmd_complete(args)
    elif args.command == "verify":
        cmd_verify(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
