import ast
import sys
from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_DIR = ROOT / "analytics" / "notebooks"


def main():
    errors = []
    notebooks = sorted(NOTEBOOK_DIR.rglob("*.ipynb"))
    for path in notebooks:
        try:
            notebook = nbformat.read(path, as_version=4)
            nbformat.validate(notebook)
        except Exception as error:
            errors.append(f"{path.relative_to(ROOT)}: invalid notebook: {error}")
            continue

        for number, cell in enumerate(notebook.cells, start=1):
            if cell.cell_type == "code":
                try:
                    ast.parse(cell.source)
                except SyntaxError as error:
                    errors.append(f"{path.relative_to(ROOT)} cell {number}: Python syntax error: {error}")

    for error in errors:
        print(f"ERROR: {error}")
    if not notebooks:
        print("No notebooks found.")
    else:
        print(f"Validated {len(notebooks)} notebook(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())