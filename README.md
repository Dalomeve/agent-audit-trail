# Agent Audit Trail

Lightweight evidence tracker for agent workflows. Create verifiable audit trails for AI agent actions.

## Why This Exists

**Problem**: AI agents (Claude Code, Codex, etc.) claim completion but provide no verifiable evidence. Hard to audit what actually happened.

**Solution**: Record agent actions with timestamps, capture evidence artifacts, generate verifiable reports.

## Features

- Record actions with timestamps
- Attach evidence (files, URLs, command outputs)
- Generate JSON audit reports
- Verify evidence integrity
- Framework-agnostic (works with any agent)

## Installation

```bash
pip install -r requirements.txt
```

Or just run directly (Python 3.8+ required):

```bash
python audit_trail.py --help
```

## Quick Start

### 1. Start a Session

```bash
python audit_trail.py start --task "Publish skill to ClawHub"
```

Output:
```json
{
  "session_id": "ats_20260301_abc123",
  "task": "Publish skill to ClawHub",
  "started_at": "2026-03-01T15:30:00Z",
  "status": "in_progress"
}
```

### 2. Record Actions

```bash
python audit_trail.py action --session ats_20260301_abc123 ^
  --type "file_create" ^
  --description "Created SKILL.md" ^
  --artifact "skills/my-skill/SKILL.md"
```

### 3. Add Evidence

```bash
python audit_trail.py evidence --session ats_20260301_abc123 ^
  --type "url" ^
  --value "https://clawhub.ai/Dalomeve/my-skill" ^
  --verified "true"
```

### 4. Complete and Generate Report

```bash
python audit_trail.py complete --session ats_20260301_abc123 ^
  --outcome "success" ^
  --summary "Published skill v1.0.0"
```

Output: `audit_report_ats_20260301_abc123.json`

## Report Structure

```json
{
  "session_id": "ats_20260301_abc123",
  "task": "Publish skill to ClawHub",
  "started_at": "2026-03-01T15:30:00Z",
  "completed_at": "2026-03-01T15:45:00Z",
  "outcome": "success",
  "actions": [
    {
      "timestamp": "2026-03-01T15:31:00Z",
      "type": "file_create",
      "description": "Created SKILL.md",
      "artifact": "skills/my-skill/SKILL.md"
    }
  ],
  "evidence": [
    {
      "type": "url",
      "value": "https://clawhub.ai/Dalomeve/my-skill",
      "verified": true
    }
  ],
  "summary": "Published skill v1.0.0"
}
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `start` | Begin audit session |
| `action` | Record an action |
| `evidence` | Add evidence |
| `complete` | End session, generate report |
| `verify` | Verify evidence integrity |
| `list` | List past sessions |

## Action Types

- `file_create` - Created a file
- `file_modify` - Modified a file
- `file_delete` - Deleted a file
- `command_exec` - Executed command
- `web_request` - Made HTTP request
- `git_commit` - Git commit
- `git_push` - Git push
- `publish` - Published to external service
- `custom` - Custom action

## Evidence Types

- `file` - Local file path
- `url` - Web URL
- `command_output` - CLI output
- `hash` - File hash (SHA256)
- `screenshot` - Image capture

## Programmatic Usage

```python
from audit_trail import AuditSession

# Start session
session = AuditSession(task="Deploy to production")

# Record actions
session.record_action("command_exec", "Ran tests", output="All 42 tests passed")
session.record_action("git_push", "Pushed to main", commit="abc123")

# Add evidence
session.add_evidence("url", "https://github.com/repo/commit/abc123", verified=True)

# Complete
report = session.complete(outcome="success", summary="Deployed v2.1.0")
print(report.save())  # Saves to JSON file
```

## Limitations

- Evidence verification is best-effort (URLs may expire)
- No built-in encryption (sensitive data should be redacted)
- Single-machine only (no distributed tracing)
- Manual instrumentation required (not automatic)

## Security

**DO NOT record**:
- API keys or tokens
- Passwords or secrets
- Personal data
- Internal URLs

Use environment variable redaction:

```bash
export AUDIT_REDACT_PATTERNS="api_key,token,secret"
```

## Examples

See `examples/` directory for:
- `skill-publish.json` - Sample skill publishing audit
- `deploy.json` - Sample deployment audit
- `research.json` - Sample research session

## License

MIT

---

**Verifiable by design. Trust but verify.**
