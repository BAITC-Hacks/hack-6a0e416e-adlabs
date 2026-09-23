# Commit Log

Shared index for team commit discipline.

The actual hourly logs are stored per teammate in `team-logs/<member>.md` to avoid merge conflicts.

Use:

```bash
TEAM_MEMBER=<name> TEAM_ROLE=<role> ./scripts/team-commit "short summary"
```

Route tasks before asking Codex:

```bash
./scripts/route-task "describe the task"
```
