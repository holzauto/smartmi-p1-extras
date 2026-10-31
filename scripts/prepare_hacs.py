"""Set the actual publishing destination before adding this repository to HACS."""

import argparse
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="Your GitHub OWNER/REPOSITORY")
    parser.add_argument("--maintainer", required=True, help="Your GitHub username")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
        raise SystemExit("Expected OWNER/REPOSITORY")
    if not re.fullmatch(r"[A-Za-z0-9-]+", args.maintainer):
        raise SystemExit("Expected a GitHub username")
    root = Path(__file__).resolve().parents[1]
    path = root / "custom_components/smartmi_p1_extras/manifest.json"
    data = json.loads(path.read_text())
    data["documentation"] = f"https://github.com/{args.repository}#readme"
    data["issue_tracker"] = f"https://github.com/{args.repository}/issues"
    data["codeowners"] = [f"@{args.maintainer}"]
    path.write_text(json.dumps(data, indent=2) + "\n")
    print("Manifest updated locally. No files uploaded or published.")


if __name__ == "__main__":
    main()
