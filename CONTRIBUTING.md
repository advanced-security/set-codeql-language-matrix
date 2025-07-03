# Versioning and Releases

## Keeping roll up version tags up to date

Move the dynamic version identifier (ex: `v1`) to match the current SHA. This allows users to adopt a major version number (e.g. `v1`) in their workflows while automatically getting all the minor/patch updates.

To do this just checkout `main` given the latest version, force-create a new annotated tag, and push it:

```
git tag -fa v1 -m "Updating v1 to 1.2.2"
git push origin v1 --force
```