# Azure Analytics Project Template

A starting point for analytics projects on Azure. Add project assets under `analytics/`, deployment definitions under `pipelines/`, and keep environment-specific values in configuration or secret stores rather than embedding them in pipeline files.

## Repository layout

```text
analytics/
	notebooks/                 Jupyter notebooks
	powerbi/reports/           Power BI Project (PBIP) reports
	semantic-model/            Tabular model (TMDL or model.bim)
	sql/                       SQL scripts and queries
config/                      Shared, non-secret project configuration
pipelines/                   Azure pipeline definitions and templates
scripts/validation/          Local validators used by CI
.github/workflows/           Independent validation workflows
```

## Validation workflows

Each workflow runs on every push and can also be started with **Actions > Run workflow**:

- **SQL**: SQLFluff linting. Set the repository variable `SQL_DIALECT` for your engine; the default is `tsql` (SQL Server/Azure SQL).
- **Semantic model**: validates model artifact structure and reports candidate tables/columns not referenced by report visual JSON. Unused-field detection is a name-based heuristic; review its findings before deleting model objects.
- **Power BI report**: parses report JSON and checks model measures for comments. It reports complex DAX using a configurable static heuristic; it cannot establish whether a measure can be simplified without semantic review.
- **Pipeline**: checks pipeline YAML syntax, environment selector/configuration, and likely hard-coded environment-specific values.
- **Notebook**: validates notebook format and Python syntax without executing notebooks or requiring Azure credentials/data.

Power BI checks work with PBIP report artifacts and either a Tabular Editor `model.bim` JSON artifact or TMDL model files. These static checks do not replace Power BI Desktop, Tabular Editor Best Practice Analyzer, or deployment tests against Azure. Store credentials in GitHub Actions secrets or Azure Key Vault, and use workload identity/OIDC where supported.

## Local validation

```bash
python -m pip install -r requirements-dev.txt
python scripts/validation/validate_semantic_model.py
python scripts/validation/validate_powerbi_report.py
python scripts/validation/validate_pipeline.py
python scripts/validation/validate_notebooks.py
if find analytics/sql -type f -name '*.sql' -print -quit | grep -q .; then
	sqlfluff lint analytics/sql --dialect "${SQL_DIALECT:-ansi}"
else
	echo "No SQL files to lint yet."
fi
```

Replace the placeholders in `pipelines/environments.yml` with non-secret environment configuration. Keep credentials in secret stores; do not commit connection strings or credentials.
