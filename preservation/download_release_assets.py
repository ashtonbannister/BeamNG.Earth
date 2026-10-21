#!/usr/bin/env python3
"""Preserve BeamNG.Earth release assets using the pinned upstream release catalog.

Python 3.10+, no external dependencies. Do not run the downloaded installers
automatically; this script only downloads and records SHA-256 digests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

CHUNK = 1024 * 1024
CATALOG = Path(__file__).resolve().with_name("releases.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def read_checksums(file: Path) -> dict[str, str]:
    result = {}
    if file.exists():
        for line in file.read_text(encoding="utf-8").splitlines():
            if len(line) >= 68 and line[64:66] == "  ":
                result[line[66:]] = line[:64]
    return result


def write_checksums(file: Path, data: dict[str, str]) -> None:
    body = "".join(f"{digest}  {path}\n" for path, digest in sorted(data.items()))
    temporary = file.with_suffix(".tmp")
    temporary.write_text(body, encoding="utf-8")
    temporary.replace(file)


def download_one(url: str, destination: Path, size: int, retries: int = 4) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    for attempt in range(1, retries + 1):
        try:
            partial.unlink(missing_ok=True)
            request = Request(url, headers={"User-Agent": "BeamNG.Earth-preservation/1.0"})
            digest = hashlib.sha256()
            received = 0
            with urlopen(request, timeout=120) as source, partial.open("wb") as target:
                while True:
                    block = source.read(CHUNK)
                    if not block:
                        break
                    target.write(block)
                    digest.update(block)
                    received += len(block)
            if received != size:
                raise IOError(f"expected {size} bytes, received {received}")
            partial.replace(destination)
            return digest.hexdigest()
        except Exception as exc:
            partial.unlink(missing_ok=True)
            if attempt == retries:
                raise IOError(f"Unable to download {url}: {exc}") from exc
            print(f"  retry {attempt}/{retries}: {exc}", file=sys.stderr)
            time.sleep(min(2 ** attempt, 12))
    raise RuntimeError("unreachable")


def main() -> int:
    parser = argparse.ArgumentParser(description="Download original BeamNG.Earth binary releases")
    parser.add_argument("--all", action="store_true", help="All historical releases; otherwise latest only")
    parser.add_argument("--platform", choices=("windows", "linux", "both"), default="windows")
    parser.add_argument("--output", type=Path, default=Path("BeamNG.Earth-binaries"))
    parser.add_argument("--verify-only", action="store_true", help="Never download: check existing assets")
    args = parser.parse_args()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    releases = sorted(catalog["releases"], key=lambda r: r["published_at"], reverse=True)
    selected = releases if args.all else releases[:1]
    base = args.output.resolve()
    base.mkdir(parents=True, exist_ok=True)
    checksum_path = base / "SHA256SUMS.txt"
    checksum_index = read_checksums(checksum_path)
    failures = 0
    total = 0

    for release in selected:
        for asset in release["assets"]:
            name = asset["name"]
            if Path(name).name != name:  # Reject unusual names instead of creating paths
                raise ValueError(f"Unsafe asset filename: {name}")
            kind = "windows" if name.lower().endswith(".exe") else "linux" if name.endswith(".AppImage") else "other"
            if args.platform != "both" and kind != args.platform:
                continue
            if kind == "other":
                continue
            total += 1
            relative = f'{release["tag"]}/{name}'
            target = base / release["tag"] / name
            expected_bytes = int(asset["size_bytes"])
            print(f"[{total}] {relative} ({expected_bytes:,} bytes)")
            try:
                if target.exists() and target.stat().st_size == expected_bytes:
                    digest = sha256_file(target)
                    expected_digest = checksum_index.get(relative)
                    if expected_digest and digest != expected_digest:
                        raise IOError("SHA-256 changed since last download")
                    checksum_index[relative] = digest
                    print("  verified existing file")
                elif args.verify_only:
                    raise FileNotFoundError("missing or incorrect size")
                else:
                    digest = download_one(asset["download_url"], target, expected_bytes)
                    checksum_index[relative] = digest
                    print("  downloaded and size-checked, SHA-256:", digest)
                if not args.verify_only:
                    write_checksums(checksum_path, checksum_index)
            except Exception as exc:
                failures += 1
                print("  FAILED:", exc, file=sys.stderr)

    if not args.verify_only:
        write_checksums(checksum_path, checksum_index)
    print(f"Checked {total} assets; failures: {failures}; output: {base}")
    if args.verify_only and not checksum_path.exists():
        print("No previous SHA256SUMS.txt: hashes computed, but cannot compare to prior download.", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
