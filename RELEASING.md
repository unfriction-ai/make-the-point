# Releasing

## The release contract

One release is one traceable unit. Every part below names the same `X.Y.Z`.

- The git tag is `vX.Y.Z`.
- The tag points at one commit. The release notes print its full SHA.
- Every manifest carries `"version": "X.Y.Z"`. These are `plugin.json`, `.claude-plugin/plugin.json` and `.cursor-plugin/plugin.json`.
- Both marketplace catalogs pin the plugin source to `"ref": "vX.Y.Z"`. These are `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`.
- The release has the asset `make-the-point-X.Y.Z.zip`.
- The release has the asset `make-the-point-X.Y.Z.zip.sha256`. It holds the SHA-256 of the zip.
- The ChatGPT install of the zip shows version `X.Y.Z`.

The catalog pin is what keeps unreleased code away from users. A host that installs from the catalog fetches the tagged commit, not the tip of `main`.

The release workflow enforces the contract. It runs the self-test and `scripts/check-manifests.py --tag vX.Y.Z` before it builds the zip. If either check fails, the workflow stops and the release gets no zip.

## Cut a release

The release-please bot owns versions, tags and releases. Nobody edits a version or pushes a tag by hand.

1. Give every pull request a Conventional Commits title, such as `fix(make-the-point): keep the key line`. Merge pull requests to `main` as usual.
2. After each merge, the `release-please` workflow opens or updates one release pull request, titled `chore(main): release X.Y.Z`. It holds the next version, the `CHANGELOG.md` entry and a `chore(release): sync version sources` commit. That commit runs `scripts/check-manifests.py --set-version X.Y.Z`, which writes the version into every manifest, both catalog refs, the two version lines in `SKILL.md` and the `Plugin:` line of the example.
3. Review the release pull request. Merge it when you want to release. This merge is the only release gate.
4. The workflow then tags the merge commit `vX.Y.Z`, creates the GitHub release with the changelog, and runs the `publish` job. That job checks the tag against the contract, builds the zip and its `.sha256` file with `git archive`, uploads both, and adds the contract table above the changelog.

To check the files on a branch, run both checks. Each must exit 0.

```bash
python3 skills/make-the-point/scripts/validate-tree.py --self-test
python3 scripts/check-manifests.py
```

### How the version goes up

release-please reads the commit messages on `main` since the last release.

- A `feat` commit bumps the minor version.
- A `fix` or `perf` commit bumps the patch version.
- A breaking change (`feat!:` or a `BREAKING CHANGE:` footer) bumps the minor version while the major version is 0. The `bump-minor-pre-major` setting in `release-please-config.json` does this.
- `docs`, `chore`, `ci`, `test` and `refactor` commits make no release on their own.

### Prerequisite for repository admins

The workflow uses `GITHUB_TOKEN`. That token can open the release pull request only when a repository admin turns on **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests**. Without it, the `release-please` job fails and no release pull request appears.

### Known limits

- release-please reads the commits inside each merged pull request, and also the pull request title in the body of its merge commit. A pull request whose commit subject equals its title appears twice in `CHANGELOG.md`. The duplicate changes only the notes, not the version.
- The bot makes lightweight tags. They carry no message and no signature. The release notes name the commit SHA, and the `.sha256` file holds the SHA-256 of the zip.
- For a few seconds after the release pull request merges, the catalogs on `main` name `vX.Y.Z` before the tag exists. A host that adds the marketplace in that window fails to install. Retry after the `release-please` run finishes.
- The release pull request usually shows no `check` result. GitHub does not run workflows for pull requests that `GITHUB_TOKEN` opens, so its runs stay waiting or end with no jobs. The `sync-versions` job runs the same checks before it pushes, and the `publish` job runs them again on the tag before it builds anything.
- To publish a release again, for example after a failed `publish` job, run the workflow by hand with the tag. The job rebuilds the zip from the tag, replaces the assets and leaves notes that already hold the contract table:

  ```bash
  gh workflow run release-please.yml -f tag=vX.Y.Z
  ```

## Verify an install

1. Open the release for the version you installed.
2. Compare the version ChatGPT shows with the plugin version in the release notes. They must be equal.
3. Download the zip and its `.sha256` file to one folder.
4. Check the zip.

   ```bash
   shasum -a 256 -c make-the-point-X.Y.Z.zip.sha256
   ```

   The command prints `OK` when the zip matches the release.

## When they disagree

A version with no matching release, or a checksum that fails, means the install does not map to known code. Remove that install and install the zip from the latest release.

The `0.1.1` install predates this contract. No tag or zip exists for it. Replace it with `make-the-point-0.2.0.zip` from the `v0.2.0` release.
