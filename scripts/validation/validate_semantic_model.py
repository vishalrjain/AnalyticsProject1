import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "analytics" / "semantic-model"
REPORT_DIR = ROOT / "analytics" / "powerbi" / "reports"


def model_names(model_files):
    names = set()
    errors = []
    for path in model_files:
        if path.suffix.lower() == ".bim":
            try:
                model = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError) as error:
                errors.append(f"{path.relative_to(ROOT)}: invalid model JSON: {error}")
                continue
            for table in model.get("model", {}).get("tables", []):
                if table.get("name"):
                    names.add(table["name"])
                for column in table.get("columns", []):
                    if column.get("name"):
                        names.add(column["name"])
        else:
            text = path.read_text(encoding="utf-8-sig")
            pattern = re.compile(r"(?m)^\s*(?:table|column|measure)\s+(?:'((?:[^']|'')+)'|\"([^\"]+)\"|([^\s='\"]+))")
            for match in pattern.finditer(text):
                names.add(next(value for value in match.groups() if value is not None).replace("''", "'"))
    return names, errors


def main():
    model_files = sorted([*MODEL_DIR.rglob("*.bim"), *MODEL_DIR.rglob("*.tmdl")])
    if not model_files:
        print("No semantic model artifacts found; add a .bim or .tmdl file to enable these checks.")
        return 0

    names, errors = model_names(model_files)
    for error in errors:
        print(f"ERROR: {error}")

    visuals = sorted(REPORT_DIR.rglob("visual.json"))
    visual_text = "\n".join(path.read_text(encoding="utf-8-sig") for path in visuals)
    if visuals:
        unused = sorted(name for name in names if name.casefold() not in visual_text.casefold())
        for name in unused:
            print(f"CANDIDATE: model object '{name}' is not referenced by report visual JSON (name-based heuristic).")
    else:
        print("No PBIR visual.json files found; visual usage analysis skipped.")

    if not names and not errors:
        print("No table, column, or measure names were recognized in the model artifacts.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())