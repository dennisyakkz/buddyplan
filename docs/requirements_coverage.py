"""List requirements that no verification points at.

Usage: python docs/requirements_coverage.py [--github]

Prints one line per uncovered requirement (Deprecated ones are skipped) and always exits 0:
the gap is meant to stay visible, not to block. With --github the lines are GitHub Actions
warnings, so they show up on the PR.
"""

import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent
NODE = re.compile(
    r"^\[(REQUIREMENT|VERIFICATION)\]\n(.*?)(?=^\[|\Z)", re.MULTILINE | re.DOTALL
)


def field(body: str, name: str) -> str | None:
    match = re.search(rf"^{name}: (.+)$", body, re.MULTILINE)
    return match.group(1).strip() if match else None


def main() -> None:
    requirements: dict[str, tuple[str, str, Path]] = {}
    verified: set[str] = set()
    for path in sorted(DOCS.glob("*/*/*.sdoc")):
        for kind, body in NODE.findall(path.read_text(encoding="utf-8")):
            if kind == "REQUIREMENT":
                requirements[field(body, "UID")] = (
                    field(body, "STATUS"),
                    field(body, "TITLE"),
                    path,
                )
            else:
                verified.update(re.findall(r"^  VALUE: (\S+)$", body, re.MULTILINE))

    uncovered = [
        (uid, title, path)
        for uid, (status, title, path) in requirements.items()
        if uid not in verified and status != "Deprecated"
    ]
    github = "--github" in sys.argv
    for uid, title, path in uncovered:
        rel = path.relative_to(DOCS.parent)
        if github:
            print(f"::warning file={rel},title=No verification::{uid} {title}")
        else:
            print(f"{uid:<12} {title}  ({rel})")
    print(
        f"{len(requirements) - len(uncovered)} of {len(requirements)} requirements have a verification."
    )


if __name__ == "__main__":
    main()
