# BeamNG.Earth — preservation archive

Snapshot: 2026-10-20. This branch (`archive/upstream-release-index`) contains archival **metadata and download utilities**. It is separate from the playable version on `main` and from the untouched KyzoFox version on `archive/kyzofox-1.5.4`.

## What is preserved in this GitHub fork

- `main` — TecnaGamer 1.5.3-beta, commit `011d6b54e42407b2f3a6deaddc47305cf2325a47`.
- `archive/kyzofox-1.5.4` — KyzoFox improvements, exactly at `e556702e89204b51082b289281e66fff120f2195`.
- All 35 original official release **commit snapshots** are reachable from `main`. Every tag's commit SHA was separately compared to the fork's `main` on 2026-10-20.
- `preservation/releases.json` — the exact names and commit SHAs of 35 original release tags; heads of 8 upstream branches; names, publication dates, sizes, and original URLs of 70 release binaries (Windows .exe and Linux AppImage).

**Important limitation:** Forking does **not** copy GitHub Releases, binary assets, or tag refs. The original names/SHAs are recorded here so lightweight tags can be recreated later. The `download_url` fields are pointers to the upstream repository, **not backed-up binary data**; they can stop working if the upstream repository disappears. The original project downloads map data from third-party services at runtime, which are not backed up here.

## Recreate the original lightweight Git tags locally

While in a normal clone of this fork, check out the archive index once to obtain `preservation/releases.json`, then run:

```python
import json, subprocess
with open("preservation/releases.json", encoding="utf-8") as f:
    releases = json.load(f)["releases"]
for release in releases:
    subprocess.run(["git", "tag", release["tag"], release["commit_sha"]], check=True)
print(f"Restored {len(releases)} local tags")
```

The tags are local until you explicitly push them (`git push origin --tags`). Tags whose names already exist must be handled deliberately; the example refuses to overwrite them.

## Save the actual release binaries before upstream disappears

On a machine with network access, use the included standard-library-only downloader:

```powershell
# Download latest original Windows installer
py preservation/download_release_assets.py --platform windows

# Archive all 35 Windows + Linux versions (about 3.92 GB)
py preservation/download_release_assets.py --all --platform both --output BeamNG.Earth-binaries

# Verify existing downloads and print any missing files
py preservation/download_release_assets.py --all --platform both --output BeamNG.Earth-binaries --verify-only
```

It uses the exact asset names/URLs/sizes recorded in `releases.json`, verifies size and computes SHA-256 hashes for downloaded files, and keeps a SHA-256 checksum index in the output folder. Only execute binaries if you trust their source. GitHub metadata does not supply expected SHA-256 digests for these historic assets.

## Back up the full source repository offline

For a complete offline Git history/refs copy of this **fork**:

```bash
git clone --mirror https://github.com/ashtonbannister/BeamNG.Earth.git BeamNG.Earth.git
```

Copy the resulting `BeamNG.Earth.git` directory to another disk. The local mirror contains the fork's Git refs and commits (including the separate 1.5.4 branch and this metadata branch), but **not** upstream GitHub Release binaries or external map services. Preserve the downloaded binary directory as a separate backup.

## Provenance

- Original: https://github.com/TecnaGamer/BeamNG.Earth
- Intermediate: https://github.com/KyzoFox/BeamNG.Earth
- Personal preservation fork: https://github.com/ashtonbannister/BeamNG.Earth

Original source files are MIT licensed (see root `LICENSE`). Respect third-party content licenses and attribution in `CREDITS.md`.
