import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "analytics" / "semantic-model"
REPORT_DIR = ROOT / "analytics" / "powerbi" / "reports"
COMPLEXITY_LIMIT = 12


def model_measures():
    measures = []
    errors = []
    for path in sorted([*MODEL_DIR.rglob("*.bim"), *MODEL_DIR.rglob("*.tmdl")]):
        text = path.read_text(encoding="utf-8-sig")
        if path.suffix.lower() == ".bim":
            try:
                model = json.loads(text)
            except json.JSONDecodeError as error:
                errors.append(f"{path.relative_to(ROOT)}: invalid model JSON: {error}")
                continue
            for table in model.get("model", {}).get("tables", []):
                for measure in table.get("measures", []):
                    measures.append((measure.get("name", "<unnamed>"), str(measure.get("expression", ""))))
        else:
            pattern = re.compile(r"(?m)^\s*measure\s+(?:'((?:[^']|'')+)'|\"([^\"]+)\"|([^=\s]+))\s*=\s*")
            matches = list(pattern.finditer(text))
            for index, match in enumerate(matches):
                end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
                name = next(value for value in match.groups() if value is not None).replace("''", "'")
                measures.append((name, text[match.end():end].strip()))
    return measures, errors


def is_commented(expression):
    return bool(re.search(r"//|/\*|\*/", expression))


def complexity(expression):
    function_calls = len(re.findall(r"\b[A-Za-z_][A-Za-z0-9_.]*\s*\(", expression))
    branches = len(re.findall(r"\b(?:IF|SWITCH)\s*\(", expression, re.IGNORECASE))
    operators = len(re.findall(r"(?:&&|\|\||<>|>=|<=|[=<>+*/-])", expression))
    return function_calls + branches * 2 + operators // 3


def main():
    errors = []
    report_files = sorted([*REPORT_DIR.rglob("*.json"), *REPORT_DIR.rglob("*.pbir")])
    for path in report_files:
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{path.relative_to(ROOT)}: invalid report JSON: {error}")

    measures, model_errors = model_measures()
    errors.extend(model_errors)
    for error in errors:
        print(f"ERROR: {error}")

    for name, expression in measures:
        if not is_commented(expression):
            print(f"ERROR: measure '{name}' has no DAX comment.")
            errors.append(name)
        score = complexity(expression)
        if score > COMPLEXITY_LIMIT:
            print(f"REVIEW: measure '{name}' has a complexity score of {score}; consider simplifying it.")

    if not measures:
        print("No measures found; add model artifacts to enable DAX checks.")
    if not list(REPORT_DIR.rglob("*.pbir")) and not list(REPORT_DIR.rglob("visual.json")):
        print("No PBIR report definitions or visuals found; report structure checks are limited to available JSON files.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())