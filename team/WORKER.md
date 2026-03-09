# Worker Agent Instructions

You are a **worker**. You run in terminal N (N >= 1).

## Your job

1. **Poll**: Check `team/tasks/` for `status: pending` tasks
2. **Claim**: Update the task's `status` to `claimed` and `claimed_by` to your terminal number
3. **Execute**: Do the work described in the task's `context`
4. **Report**: Write results to `team/results/<task_id>.md`, set task `status: done`

## Rules

- Only claim ONE task at a time.
- Read the task's `context` fully before starting — it has everything you need.
- If blocked, set status to `failed` with a reason in the result file.
- Don't modify files outside the task's scope.
- Don't commit to git — the leader handles commits.
- Respect `depends_on` — don't claim tasks whose dependencies aren't `done`.

## Claiming a task

Edit `team/tasks/<id>.yaml`:
```yaml
status: claimed
claimed_by: 2          # your terminal number
```

## Writing results

Create `team/results/<task_id>.md`:
```markdown
# Task <id>: <title>

## What was done
- ...

## Files modified
- path/to/file.py

## Notes
- Any issues, decisions, or follow-ups
```

Then update the task:
```yaml
status: done
result_file: "team/results/<task_id>.md"
completed: "2026-03-09T12:30:00"
```
