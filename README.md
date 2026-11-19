# Make the Point

Make the Point helps you understand, construct, and communicate a central argument with the Minto Pyramid Principle. The canonical output is an ArgumentTree JSON document. Prose is a view of that tree. Replies show the tree as nested Markdown. Run `/make-the-point --debug <source>` to also show the JSON. The schema is `skills/make-the-point/argument-tree.schema.json`. The checker is `skills/make-the-point/scripts/validate-tree.py`. The plugin sends no data of its own. It uses only the text, link, or image you provide in the chat.

## Install from GitHub (Claude Desktop)

1. Open **Customize → Plugins → Add → Add marketplace**.
2. Enter `unfriction-ai/make-the-point` or `https://github.com/unfriction-ai/make-the-point`.
3. Add the **make-the-point** plugin from that marketplace and enable it.
4. In a chat, type `/` and select **make-the-point**, or run `/make-the-point:make-the-point`.

## Install from GitHub (Claude Code)

```bash
claude plugin marketplace add unfriction-ai/make-the-point
claude plugin install make-the-point@make-the-point
```

Confirm with `claude plugin list`. Skills appear as `/make-the-point:make-the-point`.

## Install from GitHub (Codex)

```bash
codex plugin marketplace add unfriction-ai/make-the-point
codex plugin add make-the-point@make-the-point
```

Confirm with `codex plugin list`. The catalog is `.agents/plugins/marketplace.json`.

## Local development (Claude Code)

```bash
claude --plugin-dir .
```

## Upload without a marketplace (Claude Desktop)

Zip this repository so `.claude-plugin/plugin.json` sits at the archive root, or inside one top-level folder. In Claude Desktop, use **Add → Upload plugin**.

## Local IDE plugin host

Copy this repository, or symlink it, to `~/.cursor/plugins/local/make-the-point`. Reload the window so `.cursor-plugin/plugin.json` and `skills/` load.

## Check which version is running

Ask the skill itself. It answers from the instructions it actually loaded:

```
/make-the-point --version
```

The reply names the version and the folder it loaded from. A reply with `--debug` also ends with a `Plugin: make-the-point X.Y.Z` line.

Each host also reports what it has installed:

- Claude Code: `/plugin`, or `claude plugin list`.
- Codex: `codex plugin list`.
- ChatGPT and Claude Desktop: the version shown in the plugin or skill settings.
- Cursor with a symlinked checkout: `version` in `.cursor-plugin/plugin.json`.

A session keeps the version it loaded when it started. After an update, run `/reload-plugins` in Claude Code or start a new session, then ask `--version` again. If the two answers differ, the session is still on the old copy.

## Run the self-test

From the repository root, run this command.

```bash
python3 skills/make-the-point/scripts/validate-tree.py --self-test
```

Exit code 0 means the packaged fixtures match the expected pass and the expected failure. It also means the example and the hand-writing template in `SKILL.md` match the renderer output.

## Releases

Each release is a tag, a commit, one version in every manifest, and a zip with its SHA-256. [RELEASING.md](RELEASING.md) states the contract, how to cut a release, and how to verify an install.
