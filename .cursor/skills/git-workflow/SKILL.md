---
name: git-workflow
description: >-
  Enforces project-specific Git conventions for Python AI agent and data science
  work: conventional commits, feature branches, session-end commits, and pre-commit
  checks. Use when the user mentions commit, git, push, branch, version control,
  save my work, merge, pull request, or asks to checkpoint or wrap up a session.
---

# Git Workflow (AI Agents & Data Science)

This project treats Git as part of production-ready agent development — not optional bookkeeping. Follow these conventions exactly. Do not explain generic Git; apply our rules.

## When to Commit

Commit often and predictably:

- **Always commit at the end of each working session**, even if the feature is incomplete
- **Commit before switching** to a different task, agent component, or branch of work
- **One logical change per commit** — if the message needs "and", split into two commits

A clean history is as important as clean code in agentic systems where behavior changes are hard to audit after the fact.

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): description`

### Types

| Type | Use for |
|------|---------|
| `feat` | New agent functionality, tools, MCP servers, graph nodes, prompts |
| `fix` | Bug fixes in agents, pipelines, or data handling |
| `refactor` | Restructuring without behavior change |
| `docs` | README, docstrings, comments, notebook documentation |
| `chore` | Config, dependencies, `.gitignore`, CI, env templates |

### Scope

Scope names the **component** being changed — agent name, service, or config area:

```
feat(mcp-server): add query tool
fix(cleaning-agent): handle empty dataframe edge case
refactor(langgraph): extract shared state schema
docs(readme): document agent setup steps
chore(env): add new API key to .env.example
chore(deps): pin langchain-core version
```

### Description rules

- Lowercase
- Imperative mood ("add", "fix", "remove" — not "added" or "fixes")
- Under 72 characters
- No period at the end

**Bad:** `feat: added slack bot and fixed the dataframe bug`  
**Good:** two commits — `feat(slackbot): add channel notification tool` and `fix(cleaning-agent): handle empty dataframe edge case`

## Pre-Commit Checklist

Run this sequence before every commit:

```
Pre-commit:
- [ ] Run smoke check: python main.py
- [ ] Run tests if code changed: pytest -q
- [ ] Review staged diff: git diff --staged
- [ ] Confirm no secrets, credentials, or large data files in staged files
- [ ] Confirm commit message follows type(scope): description
```

If `main.py` or tests fail, fix before committing. Never commit broken code to `main`.

## Never Commit

Block these from every commit — warn the user if they request committing any of them:

| Category | Examples |
|----------|----------|
| Secrets | `.env`, API keys, tokens, database credentials |
| Data | CSVs, Parquet, large datasets, model weights — add to `.gitignore` |
| Python artifacts | `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `.eggs/` |
| Notebook junk | `.ipynb_checkpoints/` |

Use `.env.example` with placeholder values for required environment variables. Real secrets live only in local `.env` (gitignored).

## Branch Conventions

- **Feature branches for all new work** — never commit directly to `main`
- **Naming:** `feature/descriptive-name`
  - `feature/data-cleaning-agent`
  - `feature/slackbot-integration`
  - `feature/mcp-query-tool`
- **Keep `main` stable** — only merge working, verified code
- **Delete branches after merging**

### Starting new work

```bash
git checkout main
git pull
git checkout -b feature/your-feature-name
```

## End-of-Session Workflow

When wrapping up or when the user says "save my work":

1. Run `python main.py` (and `pytest -q` if tests exist for changed code)
2. Review `git status` and `git diff`
3. Stage only intentional changes — never `git add .` without reviewing
4. Write a conventional commit message
5. Commit
6. Push the feature branch if remote backup is needed: `git push -u origin HEAD`

Do not wait for the user to ask — proactively offer to commit at natural stopping points.

## Commit Workflow (Agent Steps)

When the user asks to commit or at session end:

1. Run in parallel: `git status`, `git diff`, `git log -3 --oneline` (for message style)
2. Verify no forbidden files are staged
3. Run `python main.py`; run `pytest -q` when applicable
4. Stage relevant files explicitly
5. Commit with HEREDOC format:

```bash
git commit -m "$(cat <<'EOF'
feat(agent-name): short imperative description

EOF
)"
```

6. Run `git status` to confirm success

Only create commits when the user requests it or at session end when saving work is implied. Never amend, force-push, or skip hooks unless explicitly requested.

## Pull Requests

When opening a PR from a feature branch:

1. Ensure branch is up to date with `main`
2. All commits follow conventional format
3. PR title matches the primary commit or summarizes the feature: `feat(cleaning-agent): add null-handling pipeline`
4. Include what changed, which agent/component was affected, and how it was verified (`python main.py`, `pytest -q`)

## Quick Reference

```
Session end     → commit (even if WIP)
Switching tasks → commit first
Message format  → type(scope): description
Branch format   → feature/descriptive-name
Verify          → python main.py, pytest -q, git diff --staged
Never commit    → secrets, data files, caches, venvs
Split commits   → if message contains "and"
```
