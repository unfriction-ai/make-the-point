# Releasing

The release-please bot owns versions, tags, and releases. You choose commit types and merge pull requests. Nobody edits a version or pushes a tag by hand.

## Cut a release

1. Give every pull request a Conventional Commits title, such as `fix(make-the-point): keep the key line`. Pick the type with [Choose the commit type](#choose-the-commit-type).
2. Merge the pull request to `main`. If it holds a releasable commit, the `release-please` workflow opens or updates one release pull request, titled `chore(main): release X.Y.Z`.
3. Review the release pull request. It holds the next version, the `CHANGELOG.md` entry, and a `chore(release): sync version sources` commit that writes the version into every file the release contract lists.
4. Merge the release pull request. This merge is the only release gate.
5. Wait for the `release-please` run on `main`. It tags the merge commit `vX.Y.Z`, creates the GitHub release, builds the zip and its `.sha256` file, and adds the contract table to the release notes.

The release pull request usually shows no `check` result, because GitHub does not run workflows for pull requests that `GITHUB_TOKEN` opens. The `sync-versions` job runs the same checks before it pushes. The `publish` job runs them again on the tag before it builds anything.

## Choose the commit type

The type decides whether a merge releases and how far the version moves. The version follows `bump-minor-pre-major` in `release-please-config.json`.

| Type | Makes a release | Version change while the major version is 0 |
| --- | --- | --- |
| `feat` | Yes | Minor, such as 0.3.2 to 0.4.0 |
| `fix` | Yes | Patch, such as 0.3.2 to 0.3.3 |
| `deps` | Yes | Patch |
| Any type with `!`, or a `BREAKING CHANGE:` footer | Yes | Minor, not 1.0.0 |
| `docs`, `chore`, `ci`, `test`, `refactor`, `style`, `build`, `perf`, `revert` | No | None |

Pick the type by what a user of the skill sees, not by the file you changed:

- `SKILL.md`, `pyramid.md`, and the schema are the skill. A wording change that changes agent behavior is a `fix` or a `feat`. As `docs`, it never reaches users.
- Use `docs` for `README.md`, `RELEASING.md`, and comments.
- release-please reads every commit inside a merged pull request and the pull request title in the merge commit. A `fix` commit inside a `docs` pull request still makes a release.

A merge that makes no release stays out of every install. Both catalogs pin the last release tag, so Claude Code and Codex install that tag, and the zip comes only from a release.

## Publish a release again

If the `publish` job fails, or a release is missing its assets, run the workflow by hand with the tag:

```bash
gh workflow run release-please.yml -f tag=vX.Y.Z
```

The run skips the `release-please` and `sync-versions` jobs. The `publish` job checks out `refs/tags/vX.Y.Z`, runs both checks, rebuilds the zip, and replaces the assets. It leaves release notes that already hold the contract table. The rebuilt zip has the same SHA-256 as the first build, because `git archive` takes its timestamps from the commit and the runner uses UTC.

## Verify an install

1. Run `/make-the-point --version`. Compare the version with the latest release.
2. Download the zip and its `.sha256` file from that release to one folder.
3. Check the zip:

   ```bash
   shasum -a 256 -c make-the-point-X.Y.Z.zip.sha256
   ```

   The command prints `OK` when the zip matches the release.

A version with no matching release, or a checksum that fails, means the install does not map to known code. Remove the install, and install the zip from the latest release.

## Release contract

One release is one traceable unit. Every part names the same `X.Y.Z`.

| Part | Value |
| --- | --- |
| Git tag | `vX.Y.Z`, on the merge commit of the release pull request |
| Manifests | `"version": "X.Y.Z"` in `plugin.json`, `.claude-plugin/plugin.json`, and `.cursor-plugin/plugin.json` |
| Catalogs | `"ref": "vX.Y.Z"` in `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` |
| Skill text | `This is make-the-point X.Y.Z.` and the `--version` example in `SKILL.md`, and the `Plugin:` line of the example |
| Release assets | `make-the-point-X.Y.Z.zip` and `make-the-point-X.Y.Z.zip.sha256` |
| Release notes | A table with the tag, the full commit SHA, the version, the asset name, and the SHA-256 |

`scripts/check-manifests.py` checks every row before a release. On a branch, both checks must exit 0:

```bash
python3 skills/make-the-point/scripts/validate-tree.py --self-test
python3 scripts/check-manifests.py
```

## Known limits

- The workflow uses `GITHUB_TOKEN`, which opens release pull requests only while **Allow GitHub Actions to create and approve pull requests** is on. Turn it on under **Actions → General** in the organization settings first, then in the repository settings.
- Release tags are lightweight. They carry no message and no signature. The release notes name the commit, and the `.sha256` file holds the checksum of the zip.
- A pull request whose commit subject equals its title appears twice in `CHANGELOG.md`. The duplicate changes only the notes.
- For a few seconds after the release pull request merges, the catalogs name `vX.Y.Z` before the tag exists. An install in that window fails. Retry after the `release-please` run finishes.
