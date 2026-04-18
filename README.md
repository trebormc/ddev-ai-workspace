[![add-on registry](https://img.shields.io/badge/DDEV-Add--on_Registry-blue)](https://addons.ddev.com)
[![last commit](https://img.shields.io/github/last-commit/trebormc/ddev-ai-workspace)](https://github.com/trebormc/ddev-ai-workspace/commits)
[![release](https://img.shields.io/github/v/release/trebormc/ddev-ai-workspace)](https://github.com/trebormc/ddev-ai-workspace/releases/latest)

# DDEV AI -- AI-Assisted Drupal Development

A set of DDEV add-ons and configurations that bring AI-powered development tools into your **Drupal** project. Run OpenCode or Claude Code in dedicated containers, automate tasks with Ralph, and use 10 specialized Drupal agents. All inside your existing DDEV environment.

> **Built for Drupal.** This workspace is designed specifically for Drupal 10/11 development. AI agents understand Drupal APIs, coding standards, caching, render arrays, and the module/theme ecosystem out of the box.
>
> Created by [Robert Menetray](https://menetray.com) · Sponsored by [DruScan](https://druscan.com) — Drupal site auditing and monitoring tools.

## Prerequisites

- [DDEV](https://ddev.readthedocs.io/) >= v1.24.10
- An API key (Anthropic, OpenAI, or a LiteLLM proxy)

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        DDEV Network                          │
│                                                              │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐            │
│  │   Beads    │   │   Agents   │   │ Playwright │            │
│  │  (tasks)   │   │    Sync    │   │    MCP     │            │
│  │            │   │ (git+conf) │   │ (Chromium) │            │
│  └─────┬──────┘   └──────┬─────┘   └─────┬──────┘            │
│        │                 │               │                   │
│        │  bd commands    │  volumes      │  HTTP MCP         │
│        ▼                 ▼               ▼                   │
│  ┌────────────────────────────────────────────────────┐      │
│  │              OpenCode  ·  Claude Code              │      │
│  │           (interactive AI development)             │      │
│  └───────────────────────┬────────────────────────────┘      │
│             ▲            │                                   │
│  docker exec│            │ docker exec                       │
│             │            ▼                                   │
│  ┌──────────┴──┐   ┌──────────────┐                          │
│  │    Ralph    │   │     Web      │                          │
│  │(orchestrator│   │   (Drupal)   │                          │
│  │  overnight) │   │  PHP, Drush  │                          │
│  └─────────────┘   └──────────────┘                          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
        │  HTTP POST (optional)
        ▼
 ┌──────────────┐
 │ Notify Bridge│  Host (port 5454)
 └──────────────┘
```

**How the pieces fit together:**

| Container | Role | Used by |
|-----------|------|---------|
| **Beads** | Git-backed task tracking (.beads/) | OpenCode, Claude Code, Ralph |
| **Agents Sync** | Syncs agent repos, resolves model tokens | OpenCode, Claude Code (via volumes) |
| **Playwright MCP** | Headless Chromium for screenshots and browser testing | OpenCode, Claude Code |
| **OpenCode** | Interactive AI development (TUI) | Connects to Web, Playwright, Beads |
| **Claude Code** | Interactive AI development (TUI) | Connects to Web, Playwright, Beads |
| **Ralph** | Autonomous orchestrator (overnight runs) | Delegates to OpenCode or Claude Code |
| **Web** | PHP, Drupal, Drush, Composer | Receives commands from AI containers |

## Quick Start

### 1. Install everything with one command

```bash
cd /path/to/your-drupal-project
ddev add-on get trebormc/ddev-ai-workspace
```

This installs all AI development tools and their dependencies automatically:
- **ddev-playwright-mcp**: Headless browser
- **ddev-beads**: Task tracking
- **ddev-agents-sync**: Agent configuration sync
- **ddev-opencode**: OpenCode CLI
- **ddev-claude-code**: Claude Code CLI
- **ddev-ralph**: Autonomous orchestrator

### 2. Start using it

```bash
ddev restart

# Interactive AI development (each tool guides you through authentication on first launch)
ddev opencode    # or: ddev oc
ddev claude-code # or: ddev cc

# Autonomous task execution
ddev ralph --backend opencode
```

Credentials are stored in shared directories on your host. Configure once and all DDEV projects share them automatically:

| Tool | Shared directory | Contains |
|------|-----------------|----------|
| Claude Code | `~/.ddev/claude-code/` | OAuth credentials, settings, MCP config |
| OpenCode | `~/.ddev/opencode/` | API credentials (`auth.json`), config overrides (`config/`) |

## Why both OpenCode and Claude Code?

The workspace installs both AI tools because they serve different purposes and complement each other well.

**Claude Code** is the most popular AI coding tool today. It works with an Anthropic subscription (Max plan), which gives access to the most capable models (Opus, Sonnet). This subscription can only be used inside Claude Code, not in other tools. It is the best option for complex tasks like architecture decisions, large refactors, or multi-file changes.

**OpenCode** is an open-source alternative that connects to multiple AI providers. It works great with free APIs for people who are getting started or want to keep costs low. The free models are less capable, so they work best for simpler tasks. OpenCode also supports paid APIs (Anthropic, OpenAI) and services like OpenCode Zen, which gives access to API models at a lower cost.

In practice, having both tools in the same project gives you flexibility:

- Use **Claude Code** for complex tasks where you need the best models.
- Use **OpenCode** for simpler tasks where a free or cheaper model is enough.
- If one provider is down, you can switch to the other without losing your workflow.
- You are not locked into a single vendor.

You can install only one of them if you prefer (see Individual Installation below). The workspace installs both by default so you can choose based on the task at hand.

## Individual Installation

If you only need specific tools, install them individually:

```bash
# Just OpenCode
ddev add-on get trebormc/ddev-opencode

# Just Claude Code
ddev add-on get trebormc/ddev-claude-code

# Just Ralph (needs OpenCode or Claude Code installed first)
ddev add-on get trebormc/ddev-ralph
```

OpenCode and Claude Code automatically install `ddev-playwright-mcp`, `ddev-beads`, and `ddev-agents-sync` as dependencies. Ralph installs `ddev-playwright-mcp` and `ddev-beads` (but not `ddev-agents-sync`).

## Desktop Notifications (optional, Linux only)

AI containers can send desktop notifications when tasks complete or need attention. The notification bridge is a **host-level tool** (not a DDEV add-on) — install it once and all your DDEV projects share it automatically.

```bash
# One-time install on your host machine
curl -fsSL https://raw.githubusercontent.com/trebormc/ai-notify-bridge/main/install.sh | bash
```

This installs a lightweight Python HTTP server that listens on port 5454 and a systemd user service that starts automatically on login. See [ai-notify-bridge](https://github.com/trebormc/ai-notify-bridge) for details.

If the bridge is not running, containers simply get an instant "connection refused" — no timeouts, no errors, no impact on performance.

## Repositories

This workspace contains 8 independent git repositories. Each can be installed individually or all at once via `ddev add-on get trebormc/ddev-ai-workspace`.

### AI Tools (interactive and autonomous)

| Repository | Description | Auto-installs |
|------------|-------------|---------------|
| [ddev-opencode](https://github.com/trebormc/ddev-opencode) | [OpenCode](https://opencode.ai) AI CLI in a dedicated container. Interactive TUI and shell for AI-powered Drupal development. | ddev-playwright-mcp, ddev-beads, ddev-agents-sync |
| [ddev-claude-code](https://github.com/trebormc/ddev-claude-code) | [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Anthropic CLI) in a dedicated container. Interactive AI development with OAuth or API key auth. | ddev-playwright-mcp, ddev-beads, ddev-agents-sync |
| [ddev-ralph](https://github.com/trebormc/ddev-ralph) | Autonomous AI task orchestrator. Delegates work to OpenCode or Claude Code via `docker exec` and tracks progress with Beads. Ideal for overnight unattended runs. | ddev-playwright-mcp, ddev-beads |

### Shared Dependencies (auto-installed)

| Repository | Description | Required by |
|------------|-------------|-------------|
| [ddev-playwright-mcp](https://github.com/trebormc/ddev-playwright-mcp) | Headless [Playwright](https://github.com/anthropics/playwright-mcp) browser as a DDEV service. Exposes an MCP endpoint for browser automation, screenshots, and visual testing. | ddev-opencode, ddev-claude-code, ddev-ralph |
| [ddev-beads](https://github.com/trebormc/ddev-beads) | [Beads](https://github.com/steveyegge/beads) (bd) git-backed task tracker in a dedicated container. All AI containers delegate task tracking here via `docker exec`. | ddev-opencode, ddev-claude-code, ddev-ralph |
| [ddev-agents-sync](https://github.com/trebormc/ddev-agents-sync) | Auto-syncs AI agent repos, resolves model tokens via `envsubst`, and generates separate configs for OpenCode and Claude Code on every `ddev start`. Supports multiple repos with override priority. | ddev-opencode, ddev-claude-code |

### Configuration

| Repository | Description |
|------------|-------------|
| [drupal-ai-agents](https://github.com/trebormc/drupal-ai-agents) | 10 specialized agents, 12 rule sets, 24 skills, and model token config (`.env.agents`) for Drupal development. Agent `.md` files use fat frontmatter compatible with both tools. Not a DDEV add-on (synced automatically via ddev-agents-sync). |

## Uninstallation

```bash
ddev add-on remove ddev-ai-workspace
ddev restart
```

To remove individual add-ons, see each add-on's README for specific uninstall instructions.

## Disclaimer

This project is an independent initiative by [Robert Menetray](https://menetray.com), sponsored by [DruScan](https://druscan.com). It is **not affiliated with, endorsed by, or sponsored by** Anthropic (Claude Code), OpenCode, Beads, Playwright, Microsoft, or DDEV. These are third-party tools integrated here for convenience.

AI-generated code may contain errors, security issues, or unintended behavior. **Always review AI-generated changes before deploying to production.** Unattended autonomous execution (e.g., Ralph Loop) should be followed by a thorough human review. The author assumes no responsibility for damages caused by the use or misuse of these configurations or the code they produce.

## License

Apache-2.0 (all repositories)
