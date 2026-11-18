# Make the Point

Make the Point helps you understand, construct, and communicate a central argument with the Minto Pyramid Principle. The canonical output is an ArgumentTree JSON document. Prose is a view of that tree. The schema is `skills/make-the-point/argument-tree.schema.json`. The checker is `skills/make-the-point/scripts/validate-tree.py`. The plugin sends no data of its own. It uses only the text, link, or image you provide in the chat.

## Install in Cursor

Copy this repository, or symlink it, to `~/.cursor/plugins/local/make-the-point`. Reload the Cursor window. Cursor reads `.cursor-plugin/plugin.json` and loads the skill from `skills/`.

## Install in Claude Code

From this repository, start a session with the plugin loaded.

```bash
claude --plugin-dir .
```

## Install in Claude Desktop

Zip this repository so `.claude-plugin/plugin.json` sits at the archive root, or inside one top-level folder. In Claude Desktop, upload that zip as a plugin.

## Run the self-test

From the repository root, run this command.

```bash
python3 skills/make-the-point/scripts/validate-tree.py --self-test
```

Exit code 0 means the packaged fixtures match the expected pass and the expected failure.
