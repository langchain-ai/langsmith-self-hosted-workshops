# Module 4: Troubleshooting & Incident Response

This directory contains notebooks for Module 4 of the LangSmith Self-Hosted Operator workshop.

## Notebooks

### Setup & Baseline
- **`00_setup_or_resume_environment.ipynb`** - Validates environment is ready for Module 4
- **`01_diagnostics_baseline.ipynb`** - Captures baseline diagnostics (run this first!)

### Failure Labs
- **`10_failure_lab_postgres.ipynb`** - PostgreSQL connectivity failure debugging
- **`20_failure_lab_redis.ipynb`** - Redis connectivity failure debugging
- **`30_failure_lab_clickhouse.ipynb`** - ClickHouse connectivity failure debugging
- **`40_failure_lab_blob_storage.ipynb`** - Blob storage configuration failure debugging

### Advanced
- **`90_full_incident_drill.ipynb`** - Complete incident simulation (optional)

## Workflow

1. Run `00_setup_or_resume_environment.ipynb` to verify your environment
2. Run `01_diagnostics_baseline.ipynb` to capture baseline
3. Run failure labs in order (10, 20, 30, 40) or pick specific ones
4. Optionally run `90_full_incident_drill.ipynb` for complete practice

## Important Notes

- **Always run baseline first** - You need "before" to compare to "after"
- **Failure injections are reversible** - All labs include remediation steps
- **Don't skip diagnostics collection** - Support will ask for the canonical bundle
- **Practice in test environments only** - These labs modify your deployment

## Documentation

See `docs/modules/module-4.md` for complete module documentation.

