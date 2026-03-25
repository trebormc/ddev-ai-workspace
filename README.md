# DDEV AI -- AI-Assisted Drupal Development

A set of DDEV add-ons and configurations that bring AI-powered development tools into your Drupal project. Run OpenCode or Claude Code in dedicated containers, automate tasks with Ralph, and use 13 specialized Drupal agents -- all inside your existing DDEV environment.

## Prerequisites

- [DDEV](https://ddev.readthedocs.io/) >= v1.23.5
- An API key (Anthropic, OpenAI, or a LiteLLM proxy)

## Architecture

```
    ┌────────────────────────────────────────────────────────────┐
    │                         DDEV Network                       │
    │                                                            │
    │  ┌────────────────┐   ┌──────────────┐  ┌──────────────┐  │
    │  │   OpenCode     │   │     Web      │  │  Playwright  │  │
    │  │  (interactive) │──>│   (PHP)      │  │     MCP      │  │
    │  │ ddev-opencode  │   │   (Drupal)   │  │  (Chromium)  │  │
    │  └────────┬───────┘   └──────────────┘  └──────────────┘  │
    │           │              ^  docker exec      ^  HTTP MCP   │
    │  ┌────────┼───────┐     │                   │              │
    │  │  Claude Code   │─────┘───────────────────┘              │
    │  │  (interactive) │                                        │
    │  │ ddev-claude-   │                                        │
    │  │   code         │                                        │
    │  └────────┬───────┘                                        │
    │           │              ^  docker exec      ^  HTTP MCP   │
    │  ┌────────┼───────┐     │                   │              │
    │  │    Ralph       │─────┘───────────────────┘              │
    │  │  (orchestrator)│  docker exec --backend opencode|claude │
    │  │ ddev-ralph     │                                        │
    │  └────────────────┘                                        │
    │                                                            │
    │  ┌────────────────┐  ┌────────────────┐                    │
    │  │  Agents Sync   │  │    Beads       │                    │
    │  │  (git pull)    │  │  (bd tasks)    │                    │
    │  │  → /agents vol │  │  → .beads/     │                    │
    │  └────────────────┘  └────────────────┘                    │
    └────────────────────────────────────────────────────────────┘
          ^ HTTP POST (curl)
          │ http://host.docker.internal:5454/notify
    ┌─────┴──────────────────┐
    │  Notification Bridge   │  <- scripts/start-notify-bridge.sh
    │  (host, port 5454)     │     notify-send + paplay
    └────────────────────────┘
```

**How the pieces fit together:**
- **ddev-opencode** / **ddev-claude-code** -- Interactive AI development (TUI, shell)
- **ddev-ralph** -- Autonomous execution (overnight runs, delegates via `docker exec`)
- **ddev-agents-sync** -- Auto-syncs AI agent repos into a shared volume
- **ddev-beads** -- Git-backed task tracking shared by all AI containers
- **ddev-playwright-mcp** -- Shared headless browser for all containers
- **drupal-ai-agents** -- Agent definitions, rules, and skills for OpenCode and Claude Code
- **Notification bridge** -- Desktop notifications from containers to your host

## Quick Start

### 1. Install everything with one command

```bash
cd /path/to/your-drupal-project
ddev add-on get trebormc/ddev-ai-workspace
```

This installs all AI development tools and their dependencies automatically:
- **ddev-playwright-mcp** -- Headless browser
- **ddev-beads** -- Task tracking
- **ddev-agents-sync** -- Agent configuration sync
- **ddev-opencode** -- OpenCode CLI
- **ddev-claude-code** -- Claude Code CLI
- **ddev-ralph** -- Autonomous orchestrator

### 2. Configure API keys

```bash
ddev ai-setup
```

The interactive wizard guides you through configuring authentication for Claude Code and OpenCode.

### 3. Start using it

```bash
ddev restart

# Interactive AI development
ddev opencode
ddev claude-code

# Autonomous task execution
ddev ralph --backend opencode

# Desktop notifications (optional, Linux)
ddev ai-notify start
```

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

## Desktop Notifications (Linux only)

AI containers can send desktop notifications when tasks complete or need attention. The notification bridge runs on your host machine (not inside Docker) because it needs access to your desktop's notification system.

**Note:** Desktop notifications are currently only supported on Linux. The bridge relies on `notify-send` (libnotify) and `paplay` (PulseAudio/PipeWire), which are not available on macOS or Windows.

### Usage

```bash
ddev ai-notify start    # Start the bridge (port 5454)
ddev ai-notify stop     # Stop the bridge
ddev ai-notify status   # Check if running
ddev ai-notify test     # Send a test notification
```

### How it works

```
Container (OpenCode/Claude Code)
  │  curl -s -X POST http://host.docker.internal:5454/notify
  │       -H 'Content-Type: application/json'
  │       -d '{"title":"Task completed","message":"All done"}'
  v
Host (port 5454)
  ├─ notify-send -> Desktop notification
  └─ paplay      -> System sound
```

**OpenCode:** Notifications are pre-configured in `drupal-ai-agents/opencode-notifier.json` (ships as default -- no setup needed).

**Claude Code:** Add a stop hook to `.claude/settings.json`:

```json
{
  "hooks": {
    "stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "curl -s -X POST http://host.docker.internal:5454/notify -H 'Content-Type: application/json' -d '{\"title\":\"Claude Code\",\"message\":\"Session finished\"}'"
          }
        ]
      }
    ]
  }
}
```

### Requirements (Linux)

```bash
sudo apt install libnotify-bin pulseaudio-utils
```

## Repositories

This workspace contains 8 independent git repositories. Each can be installed individually or all at once via `ddev add-on get trebormc/ddev-ai-workspace`.

### AI Tools (interactive and autonomous)

| Repository | Description | Auto-installs |
|------------|-------------|---------------|
| [ddev-opencode](https://github.com/trebormc/ddev-opencode) | [OpenCode](https://opencode.ai) AI CLI in a dedicated container. Interactive TUI and shell for AI-powered Drupal development. | ddev-playwright-mcp, ddev-beads, ddev-agents-sync |
| [ddev-claude-code](https://github.com/trebormc/ddev-claude-code) | [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Anthropic CLI) in a dedicated container. Interactive AI development with OAuth or API key auth. | ddev-playwright-mcp, ddev-beads, ddev-agents-sync |
| [ddev-ralph](https://github.com/trebormc/ddev-ralph) | Autonomous AI task orchestrator. Delegates work to OpenCode or Claude Code via `docker exec`, tracks progress with Beads -- ideal for overnight unattended runs. | ddev-playwright-mcp, ddev-beads |

### Shared Dependencies (auto-installed)

| Repository | Description | Required by |
|------------|-------------|-------------|
| [ddev-playwright-mcp](https://github.com/trebormc/ddev-playwright-mcp) | Headless [Playwright](https://github.com/anthropics/playwright-mcp) browser as a DDEV service. Exposes an MCP endpoint for browser automation, screenshots, and visual testing. | ddev-opencode, ddev-claude-code, ddev-ralph |
| [ddev-beads](https://github.com/trebormc/ddev-beads) | [Beads](https://github.com/steveyegge/beads) (bd) git-backed task tracker in a dedicated container. All AI containers delegate task tracking here via `docker exec`. | ddev-opencode, ddev-claude-code, ddev-ralph |
| [ddev-agents-sync](https://github.com/trebormc/ddev-agents-sync) | Auto-syncs AI agent repositories into a shared Docker volume on every `ddev start`. Supports multiple repos with override priority for private customizations. | ddev-opencode, ddev-claude-code |

### Configuration

| Repository | Description |
|------------|-------------|
| [drupal-ai-agents](https://github.com/trebormc/drupal-ai-agents) | 13 specialized agents, 4 rule sets, and 14 skills for Drupal development. Mounted as OpenCode config; also provides `CLAUDE.md` for Claude Code. Not a DDEV add-on -- synced automatically via ddev-agents-sync. |

## Disclaimer

This project is an independent initiative by [Robert Menetray](https://menetray.com) and is **not affiliated with, endorsed by, or sponsored by** Anthropic (Claude Code), OpenCode, Beads, Playwright, Microsoft, or DDEV. These are third-party tools integrated here for convenience.

AI-generated code may contain errors, security issues, or unintended behavior. **Always review AI-generated changes before deploying to production.** Unattended autonomous execution (e.g., Ralph Loop) should be followed by a thorough human review. The author assumes no responsibility for damages caused by the use or misuse of these configurations or the code they produce.

For more information, visit [menetray.com](https://menetray.com). For Drupal site auditing tools that complement this project, see [DruScan](https://druscan.com).

## License

Apache-2.0 (all repositories)
