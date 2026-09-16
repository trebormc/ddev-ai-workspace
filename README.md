[![add-on registry](https://img.shields.io/badge/DDEV-Add--on_Registry-blue)](https://addons.ddev.com)
[![last commit](https://img.shields.io/github/last-commit/trebormc/ddev-ai-workspace)](https://github.com/trebormc/ddev-ai-workspace/commits)
[![release](https://img.shields.io/github/v/release/trebormc/ddev-ai-workspace)](https://github.com/trebormc/ddev-ai-workspace/releases/latest)

# DDEV AI Workspace -- AI-Assisted Drupal Development

One command installs a complete AI development stack inside your existing DDEV project: OpenCode and Claude Code in their own containers, a headless browser, a task tracker, an autonomous task runner, a parallel-candidates arena, and a pack of 11 Drupal agents, 17 rules and 38 skills that all of them share.

> **Built for Drupal.** The agents understand Drupal 10/11 APIs, coding standards, caching, render arrays, testing and the module/theme ecosystem out of the box.
>
> Created by [Robert Menetray](https://menetray.com) · Sponsored by [DruScan](https://druscan.com) — Drupal site auditing and monitoring tools.

## At a glance

| You want to... | Run | Provided by |
|---|---|---|
| Work interactively with an AI agent on your Drupal code | `ddev claude-code` or `ddev opencode` | [ddev-claude-code](https://github.com/trebormc/ddev-claude-code), [ddev-opencode](https://github.com/trebormc/ddev-opencode) |
| Leave a list of tasks running unattended (overnight) | `ddev ralph --backend claude` | [ddev-ralph](https://github.com/trebormc/ddev-ralph) |
| Have several agents attempt the same task in isolated copies and keep the best | `ddev ai-arena ...` (from your host AI harness) | [ddev-ai-arena](https://github.com/trebormc/ddev-ai-arena) |
| Track tasks across agents and sessions | `ddev bd ready` | [ddev-beads](https://github.com/trebormc/ddev-beads) |
| Let agents open your site in a real browser | automatic (Playwright MCP) | [ddev-playwright-mcp](https://github.com/trebormc/ddev-playwright-mcp) |
| Keep agents, rules and skills up to date in every project | automatic on `ddev start` | [ddev-agents-sync](https://github.com/trebormc/ddev-agents-sync) + [drupal-ai-agents](https://github.com/trebormc/drupal-ai-agents) |

Everything runs in containers on the DDEV network. AI containers never touch the database directly: they reach the web container over SSH ([ddev-ai-ssh](https://github.com/trebormc/ddev-ai-ssh)) to run drush, composer, PHPUnit and PHPStan.

## Prerequisites

- [DDEV](https://ddev.readthedocs.io/) >= v1.24.10
- An Anthropic subscription or API key for Claude Code, or any provider OpenCode supports (Anthropic, OpenAI, OpenCode Zen, free models, a LiteLLM proxy)

## Quick Start

```bash
cd /path/to/your-drupal-project
ddev add-on get trebormc/ddev-ai-workspace
ddev restart

ddev claude-code   # or: ddev cc
ddev opencode      # or: ddev oc
```

Each tool guides you through authentication the first time. Credentials live in shared directories on your host, so every DDEV project reuses them:

| Tool | Shared directory | Contains |
|------|-----------------|----------|
| Claude Code | `~/.ddev/claude-code/` | OAuth credentials, settings, MCP config |
| OpenCode | `~/.ddev/opencode/` | API credentials (`auth.json`), config overrides (`config/`) |

Then, when you need them:

```bash
ddev ralph --backend claude          # autonomous loop over requirements.md and Beads tasks
ddev ai-arena doctor                 # check the host before your first arena
ddev bd ready                        # task tracker
```

## Architecture

```
HOST
 ├─ your AI harness (Claude Code / OpenCode) ── ddev ai-arena ──▶ candidate projects
 └─ ai-notify-bridge (optional desktop notifications, port 5454)

DDEV Network (one project)
 ├─ claude-code ─┬─ SSH ──▶ web (PHP, Drupal, drush, composer, phpunit, phpstan)
 ├─ opencode ────┤─ SSH ──▶ beads (bd task tracker, .beads/ in the project)
 │               └─ HTTP MCP ─▶ playwright-mcp (headless Chromium)
 ├─ ralph ── SSH ─▶ claude-code or opencode (delegates every AI step)
 └─ agents-sync ─▶ named volumes read by claude-code and opencode
```

| Piece | Role | Used by |
|-------|------|---------|
| **Claude Code / OpenCode** | Interactive AI development (TUI), also the executors for Ralph and arena candidates | You, Ralph, ai-arena |
| **Web** | PHP, Drupal, Drush, Composer, quality tools | AI containers over SSH |
| **Beads** | Git-backed task tracking (`.beads/`) | Claude Code, OpenCode, Ralph |
| **Playwright MCP** | Real browser for screenshots and UI verification | Claude Code, OpenCode |
| **Agents Sync** | Clones the agent repos, resolves model tokens, generates per-tool configs | Claude Code, OpenCode |
| **Ralph** | Loops over Beads tasks and delegates each one to an AI container | You (overnight runs) |
| **ai-arena** | Host command: N candidates in isolated worktrees, mechanical gates, blind judge | Your host AI harness |
| **ai-ssh** | sshd in the web container with per-project keys | Every AI container |

## The three ways to work

**Interactive.** Open `ddev claude-code` or `ddev opencode` and talk to the orchestrator. It runs on a cheap model and delegates to specialists (backend, theme, tests, a seven-judge code review, a context-firewall explorer) that run on the right model for the job. Task playbooks (bug fix, feature, refactoring, investigation) and one verification bar apply to every task: tests alone are not enough, behavior is observed on the real site and the evidence is in the summary.

**Autonomous.** Write `requirements.md`, run `ddev ralph`. Ralph plans Beads tasks, then executes them one by one through an AI container until none is left, leaving a decision trail in the task notes. Audit fixers and test generators ship ready to run.

**Arena.** From the AI harness on your host, ask for an arena. `ddev ai-arena` creates one git worktree with its own DDEV project and database per candidate, runs each candidate detached in its own AI container (different harnesses and models if you like), verifies them mechanically (site bootstrap, PHPStan, PHPCS, PHPUnit), lets a project-manager session judge the diffs blind, and promotes the winner to a `feature/` branch. Questions bubble up to you only when a human must decide.

## Why both OpenCode and Claude Code?

**Claude Code** works with an Anthropic subscription (Max plan) and gives access to the most capable models (Opus, Sonnet). The subscription cannot be used from other tools. Best for architecture decisions, large refactors and multi-file changes.

**OpenCode** is open source and connects to many providers, including free models and OpenCode Zen. Great to keep costs low, to run local models, and as a second family of models for arena candidates and cross-tool second opinions.

Having both in the same project means you pick per task, keep working if one provider is down, and avoid vendor lock-in. Install only one if you prefer (see below).

## Individual installation

```bash
ddev add-on get trebormc/ddev-opencode      # OpenCode (+ ai-ssh, beads, playwright-mcp, agents-sync)
ddev add-on get trebormc/ddev-claude-code   # Claude Code (same dependencies)
ddev add-on get trebormc/ddev-ralph         # Ralph (needs OpenCode or Claude Code first)
ddev add-on get trebormc/ddev-ai-arena      # Arena (host command; needs the AI containers to run)
```

## Desktop notifications (optional, Linux only)

Containers can notify you when a session finishes or needs attention. The bridge is a host-level tool installed once for all projects:

```bash
curl -fsSL https://raw.githubusercontent.com/trebormc/ai-notify-bridge/main/install.sh | bash
```

It runs a small HTTP server on port 5454 as a systemd user service. Without it, containers get an instant "connection refused" and nothing else changes. See [ai-notify-bridge](https://github.com/trebormc/ai-notify-bridge).

## Repositories

This workspace is 10 independent git repositories. Install them all with this meta add-on or pick the ones you need.

### AI tools

| Repository | Description | Auto-installs |
|------------|-------------|---------------|
| [ddev-claude-code](https://github.com/trebormc/ddev-claude-code) | [Claude Code](https://docs.anthropic.com/en/docs/claude-code) in a dedicated container. Interactive TUI, OAuth or API key, shared credentials across projects. | ai-ssh, playwright-mcp, beads, agents-sync |
| [ddev-opencode](https://github.com/trebormc/ddev-opencode) | [OpenCode](https://opencode.ai) in a dedicated container. Interactive TUI, any provider, shared credentials across projects. | ai-ssh, playwright-mcp, beads, agents-sync |
| [ddev-ralph](https://github.com/trebormc/ddev-ralph) | Autonomous task orchestrator. Plans Beads tasks from `requirements.md` and delegates each one to an AI container over SSH. | playwright-mcp, beads |
| [ddev-ai-arena](https://github.com/trebormc/ddev-ai-arena) | Host command that runs N AI candidates in isolated worktree environments, gates them mechanically and judges them blind. Ships a skill for your host AI harness. | — |

### Shared dependencies

| Repository | Description | Required by |
|------------|-------------|-------------|
| [ddev-ai-ssh](https://github.com/trebormc/ddev-ai-ssh) | sshd in the web container with per-project ed25519 keys, so agents run drush and composer without a Docker socket. | claude-code, opencode |
| [ddev-playwright-mcp](https://github.com/trebormc/ddev-playwright-mcp) | Headless Chromium exposed as an MCP endpoint for navigation, screenshots and UI verification. | claude-code, opencode, ralph |
| [ddev-beads](https://github.com/trebormc/ddev-beads) | [Beads](https://github.com/steveyegge/beads) (`bd`) git-backed task tracker in its own container, shared by every agent. | claude-code, opencode, ralph |
| [ddev-agents-sync](https://github.com/trebormc/ddev-agents-sync) | Syncs one or more agent repos on every `ddev start`, resolves model tokens per tool, generates configs and the git-access policy. | claude-code, opencode |

### Agents

| Repository | Description |
|------------|-------------|
| [drupal-ai-agents](https://github.com/trebormc/drupal-ai-agents) | 11 agents, 17 rules and 38 skills for Drupal 10/11: backend, theming, tests, a seven-judge code review with implementation contracts, task playbooks, engineering principles, blast-radius analysis, project verification skills, technical writing and the arena protocol. Not a DDEV add-on: synced automatically by ddev-agents-sync. Add a private repo of your own after it to override or extend. |

## Uninstallation

```bash
ddev add-on remove ddev-ai-workspace
ddev restart
```

The meta add-on only groups the others: remove them individually with `ddev add-on remove <name>` if you want them gone too.

## Disclaimer

This project is an independent initiative by [Robert Menetray](https://menetray.com), sponsored by [DruScan](https://druscan.com). It is **not affiliated with, endorsed by, or sponsored by** Anthropic (Claude Code), OpenCode, Beads, Playwright, Microsoft, or DDEV. These are third-party tools integrated here for convenience.

AI-generated code may contain errors, security issues, or unintended behavior. **Always review AI-generated changes before deploying to production.** Unattended runs (Ralph, arena candidates) should be followed by a thorough human review. The author assumes no responsibility for damages caused by the use or misuse of these configurations or the code they produce.

## License

Apache-2.0 (all repositories)
