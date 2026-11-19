# Releasing

## The release contract

One release is one traceable unit. Every part below names the same `X.Y.Z`.

- The git tag is `vX.Y.Z`.
- The tag points at one commit. The release notes print its full SHA.
- Every manifest carries `"version": "X.Y.Z"`. These are `plugin.json`, `.claude-plugin/plugin.json` and `.cursor-plugin/plugin.json`.
- The release has the asset `make-the-point-X.Y.Z.zip`.
- The release has the asset `make-the-point-X.Y.Z.zip.sha256`. It holds the SHA-256 of the zip.
- The ChatGPT install of the zip shows version `X.Y.Z`.

Marketplace catalogs carry no version. Hosts read it from the plugin manifest.

The release workflow enforces the contract. It runs the self-test and `scripts/check-manifests.py --tag vX.Y.Z` before it builds the zip. If either check fails, the workflow stops and no release exists.

## Cut a release

1. On a branch, set the new version in every manifest.
2. Run both checks. Each must exit 0.

   ```bash
   python3 skills/make-the-point/scripts/validate-tree.py --self-test
   python3 scripts/check-manifests.py --tag vX.Y.Z
   ```

3. Open a pull request and merge it to `main`.
4. Tag the merge commit by its SHA and push the tag. Tag the SHA, not the tip of `main`, because another merge can land first.

   ```bash
   git fetch origin
   sha=$(gh pr view <pr-number> --json mergeCommit -q .mergeCommit.oid)
   git tag -m "make-the-point vX.Y.Z" vX.Y.Z "$sha"
   git push origin vX.Y.Z
   ```

   The `-m` message makes an annotated tag. Git needs one when `tag.gpgsign` is on.

5. Watch the `release` workflow. It creates the GitHub release with the zip, the `.sha256` file and the notes.

The version also lives in the `This is make-the-point X.Y.Z.` line of `SKILL.md` and the `Plugin:` line of the example. `check-manifests.py` fails until every copy agrees. Bump the minor version for a breaking change while the major version is 0. Bump the patch version for a fix.

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
