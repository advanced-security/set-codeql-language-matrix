# Versioning and Releases

## Keeping roll up version tags up to date

Move the dynamic version identifier (ex: `v1`) to match the current SHA. This allows users to adopt a major version number (e.g. `v1`) in their workflows while automatically getting all the minor/patch updates.

To do this just checkout `main` given the latest version, force-create a new annotated tag, and push it:

```
git tag -fa v1 -m "Updating v1 to 1.2.2"
git push origin v1 --force
```

## Keeping sample version references up to date

The [README.md](./README.md) samples pin to a full release version (e.g. `advanced-security/set-codeql-language-matrix@v1.6.0`). The [Bump Sample Version](./.github/workflows/bump-sample-version.yml) workflow automatically opens a pull request to update these references whenever a new (non-prerelease) release is published, so no manual action is required.
