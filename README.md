# StanStationPayloadRepo — automatic release updater

This add-on checks configured GitHub release sources approximately every six hours and
updates `catalog.json` with the latest release tag, direct asset URL, and asset size.
It can also be run manually from GitHub Actions. It does not download or execute payload
files in the workflow runner.

## Install into your existing repository

1. Download this package and extract it.
2. In `x574n/StanStationPayloadRepo`, upload these two paths, preserving directories:
   - `.github/workflows/update-catalog.yml`
   - `scripts/update_catalog.py`
3. Commit them to the repository's **default branch**.
4. In the repository, open **Settings → Actions → General → Workflow permissions**.
   Allow read and write permissions if repository policy requires that setting. The
   workflow itself requests only `contents: write`.
5. Open **Actions → Update payload catalog → Run workflow** to test it immediately.
   Scheduled runs target approximately every six hours. GitHub may delay schedules, and
   scheduled workflows in public repositories may be disabled after 60 days without
   repository activity.

## Configure each entry in catalog.json

A URL-only entry cannot be automatically discovered. Add `source_repo` and `asset_name`
for a public GitHub repository that publishes GitHub Releases. Example (fictional source
and asset; replace these with the actual upstream repository and exact release filename):

```json
{
  "name": "My Payload",
  "description": "Example release-based entry",
  "source_repo": "OWNER/UPSTREAM-REPOSITORY",
  "asset_name": "payload.bin",
  "version": "v1.0.0",
  "url": "https://example.com/initial-placeholder.bin",
  "filename": "payload.bin",
  "size": 0,
  "sha256": "",
  "enabled": true
}
```

- `source_repo`: exact GitHub `OWNER/REPOSITORY` slug.
- `asset_name`: exact filename attached to the latest GitHub Release.
- `version`, `url`, and `size` are refreshed from that release.
- `filename` remains your chosen SD-card filename, or defaults to the asset name.
- Entries without both `source_repo` and `asset_name` are left alone.
- This first version supports repositories with a published **latest release**. It does
  not infer a download URL from arbitrary webpages, tags without releases, or projects
  that publish files only on their own websites.

## Integrity note

If a new release is detected, the updater clears a pre-existing `sha256` value because
the old checksum must not be treated as valid for the new binary. The workflow does not
calculate a new checksum yet. For safety, configure firmware to verify a trusted checksum
before installing files, and only use sources you trust. A direct URL is not proof that
the file is safe or compatible.

## Troubleshooting

- **No configured sources:** add `source_repo` and `asset_name` to entries.
- **No asset found:** check that `asset_name` exactly matches the filename attached to
  the upstream repository's latest published release.
- **Push rejected:** check the repository's Actions workflow permissions and branch rules.
- **Nothing changes:** if the latest release tag, URL, and size match the catalog, no commit
  is made.
