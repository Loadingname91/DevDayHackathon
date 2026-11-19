# Setting up Claude Code on a new device

This gets a new machine to the same Claude Code setup used to plan Quilt: the same model settings, plugins, personal skills, hook and MCP servers.

## What comes with your account

When you sign in with `/login`, the claude.ai connectors (Railway, Claude Docs, GlockApps), the skills synced from claude.ai and every published artifact come along on their own. The canvas, the Home and Flows prototypes and the motion catalogue all live on claude.ai.

## 1. Install Claude Code and clone the repo

```bash
curl -fsSL https://claude.ai/install.sh | bash
git clone https://github.com/Loadingname91/DevDayHackathon.git
cd DevDayHackathon
```

The hook needs Python 3 at `/usr/bin/python3`, and the design tests need Node with Playwright.

## 2. Copy the settings and the hook

The repo keeps a copy of the user settings in `setup/claude-code/`. It holds no keys.

```bash
mkdir -p ~/.claude/hooks
cp setup/claude-code/settings.json ~/.claude/settings.json
cp setup/claude-code/hooks/skill-finder.py ~/.claude/hooks/
```

`settings.json` sets Opus with high effort, the dark fullscreen theme, auto-compact, the nine plugins with the GitHub sources they install from, and a hook that suggests matching skills on every prompt. If you change settings on the old machine, copy the file back into the repo so the two stay in step.

## 3. Sign in and check the plugins

Run `claude`, then `/login`. The plugins listed in `settings.json` should install on first start. If any are missing, add the sources and install them:

```
/plugin marketplace add mattpocock/skills
/plugin marketplace add pbakaus/impeccable
/plugin marketplace add DietrichGebert/ponytail
/plugin marketplace add blader/humanizer
/plugin marketplace add latent-spaces/brag
/plugin marketplace add spotify/portal-ai-plugins
/plugin marketplace add https://github.com/product-on-purpose/pm-skills.git
/plugin install mattpocock-skills@mattpocock
/plugin install impeccable@impeccable
/plugin install ponytail@ponytail
/plugin install humanizer@humanizer
/plugin install brag@brag
/plugin install shunt@portal
/plugin install pm-skills@pm-skills-marketplace
/plugin install frontend-design@claude-plugins-official
```

Restart `claude` afterwards.

## 4. Copy the personal skills

The 22 skills in `~/.claude/skills` (listed in `setup/claude-code/skills.txt`) are third-party skill packs, so they aren't in this public repo. Copy them from the old machine:

```bash
# old machine
cd ~ && tar czf claude-skills.tgz --exclude='.claude/skills/synced' .claude/skills .claude/projects/*/memory .claude/plans
# new machine
tar xzf claude-skills.tgz -C ~
```

That also brings saved plans and project memories. Memories are filed under the project's full path (`~/.claude/projects/-home-hitesh-workfiles-ProjectWork-DevDay/`). If the repo lives at a different path on the new machine, rename that folder to match.

Don't copy `~/.claude/.credentials.json` or `~/.claude.json`. They hold the old machine's sign-in and state.

## 5. Add the MCP servers

These are tied to a project folder and one needs a key, so they are added by hand. Run each from inside the project folder it belongs to.

```bash
# in this repo: Google Stitch (design screens)
claude mcp add --transport http stitch https://stitch.googleapis.com/mcp --header "X-Goog-Api-Key: <your Stitch key>"
# in the VendorSpace repo: Playwright browser
claude mcp add playwright -- npx @playwright/mcp@latest
```

## 6. Check it

Start `claude` in the repo and run `/plugin` to see the plugins, `/mcp` to see Stitch connected, and `/hooks` to see the skill finder. `CLAUDE.md` at the repo root tells Claude where everything lives, so a fresh session can pick up the work.
