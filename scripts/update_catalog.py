# StanStation payload catalog updater
# Tracks the newest GitHub release that provides a direct .elf asset.
# Only .elf release assets are eligible; archives and source bundles are never selected.
import json, os, sys, urllib.request, datetime
from pathlib import Path

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "StanStation-Payload-Catalog-Updater", "X-GitHub-Api-Version": "2022-11-28"}
if os.getenv("GITHUB_TOKEN"):
    HEADERS["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]

def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)

def main(path):
    p = Path(path)
    catalog = json.loads(p.read_text(encoding="utf-8"))
    entries = catalog.get("payloads")
    if not isinstance(entries, list):
        raise ValueError("catalog.json must contain a payloads array")
    changed = False
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        repo = entry.get("source_repo")
        if not repo:
            continue
        parts = repo.split("/")
        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        if len(parts) != 2 or not all(parts) or any(c not in allowed for part in parts for c in part):
            print("Skipping invalid source_repo:", repo)
            continue
        try:
            # /releases/latest omits prereleases. Inspect recent releases so a
            # prerelease with a direct ELF can be tracked too.
            releases = get_json("https://api.github.com/repos/{}/releases?per_page=20".format(repo))
            selected = None
            asset = None
            for release in releases:
                if release.get("draft"):
                    continue
                elf_assets = [
                    a for a in release.get("assets", [])
                    if isinstance(a.get("name"), str) and a["name"].lower().endswith(".elf")
                    and a.get("browser_download_url")
                ]
                if elf_assets:
                    # Prefer the configured exact asset name if present; otherwise
                    # use the first direct ELF in the newest eligible release.
                    wanted = entry.get("asset_name")
                    asset = next((a for a in elf_assets if a["name"] == wanted), elf_assets[0])
                    selected = release
                    break
            if not selected or not asset:
                print("No direct .elf release asset found for", repo)
                continue
            version = selected.get("tag_name") or entry.get("version", "")
            asset_name = asset["name"]
            values = {
                "version": version,
                "url": asset["browser_download_url"],
                "size": asset.get("size", entry.get("size", 0)),
                "filename": asset_name,
                "asset_name": asset_name,
                "sha256": (asset.get("digest") or "").removeprefix("sha256:"),
                "elf_only": True
            }
            for key, value in values.items():
                if value is not None and entry.get(key) != value:
                    entry[key] = value
                    changed = True
            print("Checked", entry.get("name", repo), version, asset_name)
        except Exception as exc:
            print("Warning: release check failed for", repo, str(exc))
    if changed:
        catalog["updated"] = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        p.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("Catalog updated")
    else:
        print("No catalog changes")
if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: update_catalog.py catalog.json")
    main(sys.argv[1])
