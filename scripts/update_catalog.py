# StanStation payload catalog updater
# Checks configured source_repo + asset_name entries against GitHub latest releases.
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
        repo, asset_name = entry.get("source_repo"), entry.get("asset_name")
        if not repo or not asset_name:
            continue
        parts = repo.split("/")
        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        if len(parts) != 2 or not all(parts) or any(c not in allowed for part in parts for c in part):
            print("Skipping invalid source_repo:", repo)
            continue
        try:
            release = get_json("https://api.github.com/repos/{}/releases/latest".format(repo))
            asset = next((a for a in release.get("assets", []) if a.get("name") == asset_name), None)
            if not asset:
                print("Asset not found for", repo, asset_name)
                continue
            version = release.get("tag_name") or entry.get("version", "")
            if version != entry.get("version") and entry.get("sha256"):
                entry["sha256"] = ""
                changed = True
            values = {"version": version, "url": asset.get("browser_download_url", entry.get("url", "")), "size": asset.get("size", entry.get("size", 0)), "filename": entry.get("filename") or asset_name}
            for key, value in values.items():
                if value is not None and entry.get(key) != value:
                    entry[key] = value
                    changed = True
            print("Checked", entry.get("name", repo), version)
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
