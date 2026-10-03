import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = ROOT / "pipelines"
CONFIG_PATH = PIPELINE_DIR / "environments.yml"
ENVIRONMENTS = {"dev", "test", "prod"}
HARDCODED_ENV_VALUE = re.compile(r"(?i)(?:https?://[^\s/'\"]+|[a-z0-9-]+)\.(?:dev|test|prod)\.[a-z0-9.-]+")


def main():
    errors = []
    pipeline_files = sorted(path for path in PIPELINE_DIR.rglob("*.y*ml") if path != CONFIG_PATH)
    try:
        config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as error:
        errors.append(f"{CONFIG_PATH.relative_to(ROOT)}: invalid environment config: {error}")
        config = {}

    environment_parameter = next(
        (parameter for parameter in config.get("parameters", []) if parameter.get("name") == "environment"),
        {},
    )
    configured = set(environment_parameter.get("values", []))
    if not ENVIRONMENTS.issubset(configured):
        errors.append(f"Environment config must define: {', '.join(sorted(ENVIRONMENTS))}.")
    config_text = CONFIG_PATH.read_text(encoding="utf-8") if CONFIG_PATH.exists() else ""
    for environment in ENVIRONMENTS:
        if f"eq(parameters.environment, '{environment}')" not in config_text:
            errors.append(f"Environment config must map the '{environment}' selector to environment-specific variables.")

    for path in pipeline_files:
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            errors.append(f"{path.relative_to(ROOT)}: invalid YAML: {error}")
            continue
        text = path.read_text(encoding="utf-8")
        if not re.search(r"(?im)^\s*parameters\s*:", text) or not re.search(r"(?i)environment", text):
            errors.append(f"{path.relative_to(ROOT)}: pipeline must expose an environment selector/parameter.")
        if HARDCODED_ENV_VALUE.search(text):
            errors.append(f"{path.relative_to(ROOT)}: possible hard-coded environment-specific endpoint; use environment configuration.")

    for error in errors:
        print(f"ERROR: {error}")
    if not pipeline_files:
        print("No pipeline YAML files found.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())