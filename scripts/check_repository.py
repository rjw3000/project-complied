"""Check documentation links and workflow security invariants without dependencies."""
from pathlib import Path
import re
root = Path(__file__).resolve().parents[1]
errors = []
for file in root.rglob("*.md"):
    if ".git" in file.parts:
        continue
    for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", file.read_text()):
        if ":" not in target and not target.startswith("#"):
            if not (file.parent / target.split("#")[0]).exists():
                errors.append(f"Broken link: {file.relative_to(root)} -> {target}")
for file in (root / ".github/workflows").glob("*.yml"):
    text = file.read_text()
    if "pull_request_target" in text or "write-all" in text:
        errors.append(f"Unsafe workflow privilege: {file.name}")
    if "persist-credentials: false" not in text or "timeout-minutes:" not in text:
        errors.append(f"Missing credential/timeout control: {file.name}")
    for action in re.findall(r"uses:\s*(\S+)", text):
        if not re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", action):
            errors.append(f"Unpinned action: {action}")
if errors:
    raise SystemExit("\n".join(errors))
print("Documentation links and workflow controls passed")
