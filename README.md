# DDEV AI -- AI-Assisted Drupal Development

A set of DDEV add-ons and configurations that bring AI-powered development tools into your Drupal project. Run OpenCode or Claude Code in dedicated containers, automate tasks with Ralph, and use 13 specialized Drupal agents -- all inside your existing DDEV environment.

## Prerequisites

- [DDEV](https://ddev.readthedocs.io/) >= v1.23.5
- An API key (Anthropic, OpenAI, or a LiteLLM proxy)

## Architecture

```
                          ┌──────────────────┐
                          │   Your Machine   │
                          │                  │
                          │ config/          │ <- Mounted as volume
                          │ share/auth.json  │ <- Mounted as volume
                          └────────┬─────────┘
                                   │
    ┌──────────────────────────────┼──────────────────────────────┐
    │                              │          DDEV Network        │
    │                              ▼                              │
    │  ┌────────────────┐   ┌──────────────┐   ┌──────────────┐  │
    │  │   OpenCode     │   │     Web      │   │  Playwright  │  │
    │  │  (interactive) │──>│   (PHP)      │   │     MCP      │  │
    │  │ ddev-opencode  │   │   (Drupal)   │   │  (Chromium)  │  │
    │  └────────┬───────┘   └──────────────┘   └──────────────┘  │
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
    │  └────────┬───────┘                                        │
    │           │                                                │
    │           │  docker exec $BEADS_CONTAINER bd ...           │
    │           v                                                │
    │  ┌────────────────┐                                        │
    │  │    Beads       │  Task tracking (.beads/ in project)    │
    │  │ ddev-beads     │                                        │
    │  └────────────────┘                                        │
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
- **drupal-ai-agents** -- Agent definitions, rules, and skills for OpenCode
- **Notification bridge** -- Desktop notifications from containers to your host

## Quick Start

### 1. Clone the workspace

```bash
git clone https://github.com/trebormc/ddev-ai-workspace.git
cd ddev-ai-workspace
```

### 2. Set up API credentials

```bash
cp share/auth.json.example share/auth.json
```

Edit `share/auth.json` with your API keys:

```json
{
  "anthropic": {
    "type": "oauth",
    "access": "sk-ant-oat01-YOUR_ACCESS_TOKEN",
    "refresh": "sk-ant-ort01-YOUR_REFRESH_TOKEN",
    "expires": 0
  },
  "litellm": {
    "type": "api",
    "key": "YOUR_LITELLM_API_KEY"
  }
}
```

### 3. Set up OpenCode config (if using OpenCode)

```bash
cp config/opencode.json.example config/opencode.json
```

Edit `config/opencode.json` to set your preferred models and provider URLs.

### 4. Install the DDEV add-on in your Drupal project

```bash
cd /path/to/your-drupal-project

# Option A: Interactive OpenCode
ddev add-on get trebormc/ddev-opencode

# Option B: Interactive Claude Code
ddev add-on get trebormc/ddev-claude-code

# Option C: Autonomous Ralph (needs OpenCode or Claude Code installed first)
ddev add-on get trebormc/ddev-ralph
```

Each add-on automatically installs `ddev-playwright-mcp`, `ddev-beads`, and `ddev-agents-sync` as dependencies.

### 5. Install Drupal agents (for OpenCode users)

```bash
git clone https://github.com/trebormc/drupal-ai-agents.git ~/drupal-ai-agents
```

Then in your project's `.ddev/.env.opencode`:

```bash
HOST_OPENCODE_AUTH_DIR=/path/to/ddev-ai-workspace/share/
HOST_OPENCODE_CONFIG_DIR=/path/to/drupal-ai-agents/
```

### 6. Start using it

```bash
ddev restart

# OpenCode
ddev opencode

# Claude Code
ddev claude-code

# Ralph (autonomous)
ddev ralph --backend opencode
```

## Configuration

After cloning this workspace, create your local configuration files from the provided examples:

```bash
# API credentials
cp share/auth.json.example share/auth.json
vi share/auth.json

# OpenCode configuration
cp config/opencode.json.example config/opencode.json
vi config/opencode.json
```

Then point your DDEV project's `.env.opencode` to these directories:

```bash
HOST_OPENCODE_AUTH_DIR=/path/to/ddev-ai-workspace/share/
HOST_OPENCODE_CONFIG_DIR=/path/to/drupal-ai-agents/
```

### File structure

| Path | Tracked | Purpose |
|------|---------|---------|
| `config/*.json.example` | Yes | Template configs for new users |
| `config/*.json` | **No** | Your real config (local only) |
| `share/*.json.example` | Yes | Template credentials for new users |
| `share/*.json` | **No** | Your real API keys (local only) |
| `scripts/` | Yes | Shared utilities (notification bridge) |

## Desktop Notifications

The AI containers can send desktop notifications to your host when they complete a task, encounter an error, or need your attention.

### Start the notification bridge

```bash
./scripts/start-notify-bridge.sh
```

This starts an HTTP server on port 5454 that receives POST requests from Docker containers and triggers `notify-send` + `paplay` on your desktop.

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

### Test it

```bash
curl -X POST http://localhost:5454/notify \
  -H 'Content-Type: application/json' \
  -d '{"title":"Test","message":"It works"}'
```

### Requirements (Linux)

```bash
sudo apt install libnotify-bin pulseaudio-utils
```

## Repositories

| Repository | Type | Description |
|------------|------|-------------|
| [ddev-playwright-mcp](https://github.com/trebormc/ddev-playwright-mcp) | DDEV add-on | Headless Playwright browser as a DDEV service (shared dependency) |
| [ddev-beads](https://github.com/trebormc/ddev-beads) | DDEV add-on | Git-backed task tracker for AI agents (shared dependency) |
| [ddev-agents-sync](https://github.com/trebormc/ddev-agents-sync) | DDEV add-on | Auto-syncs AI agent repos into shared volume (shared dependency) |
| [ddev-opencode](https://github.com/trebormc/ddev-opencode) | DDEV add-on | OpenCode AI CLI in a dedicated container |
| [ddev-claude-code](https://github.com/trebormc/ddev-claude-code) | DDEV add-on | Claude Code CLI in a dedicated container |
| [ddev-ralph](https://github.com/trebormc/ddev-ralph) | DDEV add-on | Autonomous task runner (delegates to OpenCode or Claude Code) |
| [drupal-ai-agents](https://github.com/trebormc/drupal-ai-agents) | Configuration | 13 agents, 4 rules, 14 skills for Drupal development (OpenCode) |

## Disclaimer

This project is an independent initiative by [Robert Menetray](https://menetray.com) and is **not affiliated with, endorsed by, or sponsored by** Anthropic (Claude Code), OpenCode, Beads, Playwright, Microsoft, or DDEV. These are third-party tools integrated here for convenience.

AI-generated code may contain errors, security issues, or unintended behavior. **Always review AI-generated changes before deploying to production.** Unattended autonomous execution (e.g., Ralph Loop) should be followed by a thorough human review. The author assumes no responsibility for damages caused by the use or misuse of these configurations or the code they produce.

For more information, visit [menetray.com](https://menetray.com). For Drupal site auditing tools that complement this project, see [DruScan](https://druscan.com).

## License

Apache-2.0 (all repositories)
