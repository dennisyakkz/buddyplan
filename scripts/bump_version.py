#!/usr/bin/env python3
"""Set or check the Buddyplan version in every file that carries it.

Usage:
    scripts/bump_version.py X.Y.Z      # write X.Y.Z everywhere
    scripts/bump_version.py --check    # verify every file matches the latest vX.Y.Z git tag
    scripts/bump_version.py --check X.Y.Z

The Android versionCode and the Flutter build number are derived from the
version (MAJOR*10000 + MINOR*100 + PATCH), so they always increase with the
version. MINOR and PATCH must therefore stay below 100.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = r"\d+\.\d+\.\d+"


def version_code(version: str) -> int:
    major, minor, patch = (int(p) for p in version.split("."))
    if minor >= 100 or patch >= 100:
        sys.exit(f"MINOR and PATCH must be < 100 for versionCode: {version}")
    return major * 10000 + minor * 100 + patch


def rules(version: str) -> dict[str, list[tuple[str, str]]]:
    code = version_code(version)
    return {
        "mobile_app/pubspec.yaml": [
            (r"(?m)^version: .*$", f"version: {version}+{code}"),
        ],
        "dashboard_app/app/build.gradle.kts": [
            (r"versionCode = \d+", f"versionCode = {code}"),
            (r'versionName = "[^"]*"', f'versionName = "{version}"'),
        ],
        "backend/docker-compose.prod.yml": [
            (rf"\(e\.g\. {SEMVER}\)", f"(e.g. {version})"),
            (rf"buddyplan-backend:{SEMVER}", f"buddyplan-backend:{version}"),
            (rf"BUDDYPLAN_VERSION:-{SEMVER}\}}", f"BUDDYPLAN_VERSION:-{version}}}"),
        ],
        "README.md": [
            (rf"\(e\.g\. `{SEMVER}`\)", f"(e.g. `{version}`)"),
            (rf"export BUDDYPLAN_VERSION={SEMVER}", f"export BUDDYPLAN_VERSION={version}"),
        ],
        "docs/releases.md": [
            (rf"export BUDDYPLAN_VERSION={SEMVER}", f"export BUDDYPLAN_VERSION={version}"),
        ],
    }


def latest_tag() -> str:
    out = subprocess.run(
        ["git", "tag", "--list", "v*", "--sort=-v:refname"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    if not out:
        sys.exit("No vX.Y.Z tags found.")
    return out[0].removeprefix("v")


def main(argv: list[str]) -> int:
    check = "--check" in argv
    args = [a for a in argv if a != "--check"]
    if args:
        version = args[0].removeprefix("v")
    elif check:
        version = latest_tag()
    else:
        print(__doc__)
        return 2
    if not re.fullmatch(SEMVER, version):
        sys.exit(f"Not a X.Y.Z version: {version}")

    problems = []
    for rel, subs in rules(version).items():
        path = ROOT / rel
        text = path.read_text()
        new = text
        for pattern, replacement in subs:
            if not re.search(pattern, new):
                problems.append(f"{rel}: pattern not found: {pattern}")
                continue
            new = re.sub(pattern, replacement, new)
        if new != text:
            if check:
                problems.append(f"{rel}: not at {version}")
            else:
                path.write_text(new)
                print(f"updated {rel}")

    for p in problems:
        print(p, file=sys.stderr)
    if problems:
        return 1
    print(f"All versions {'match' if check else 'set to'} {version} (code {version_code(version)}).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
