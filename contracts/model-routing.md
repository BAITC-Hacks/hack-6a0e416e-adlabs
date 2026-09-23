# Model Routing Contract

Status: draft

## Input

```json
{
  "request": "string",
  "repo": "control | frontend | backend | ml",
  "context_files": ["string"]
}
```

## Output

```json
{
  "task_type": "frontend | backend | ml | docs | git | architecture | review | mixed",
  "owner_agent": "triage | architect | frontend | backend | ml | reviewer | docs-pitch | git-manager",
  "model_tier": "cheap | balanced | strongest",
  "files_needed": ["string"],
  "needs_review": true,
  "reason": "string"
}
```

## Tier policy

- `cheap`: summaries, simple docs, git checks, copy edits.
- `balanced`: normal implementation and scoped bug fixes.
- `strongest`: architecture, hard debugging, security, and final review.

